"""Streamlit dashboard: Predict / Admin Review / Evaluation."""
import os

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Complaint Classifier", page_icon="📋", layout="wide")


def _setting(name, default=""):
    """Environment variable first, then Streamlit secrets, then default."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except Exception:
        return default


API_URL = _setting("API_URL", "http://localhost:8000").rstrip("/")
ADMIN_KEY = _setting("ADMIN_API_KEY")
HEADERS = {"X-API-Key": ADMIN_KEY} if ADMIN_KEY else {}


def call(method, path, **kwargs):
    """Call the backend; show a friendly error instead of crashing."""
    try:
        r = requests.request(method, f"{API_URL}{path}", headers=HEADERS, timeout=60, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Cannot reach the API at {API_URL}. Is it running? ({exc})")
        return None
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        st.error(f"API error {r.status_code}: {detail}")
        return None
    return r


st.sidebar.title("📋 Complaint Classifier")
page = st.sidebar.radio("Page", ["Predict", "Admin Review", "Evaluation"])
st.sidebar.caption(f"API: {API_URL}")

# ---------------------------------------------------------------- Predict
if page == "Predict":
    st.header("Classify a complaint")
    text = st.text_area("Complaint text", height=150, max_chars=1000,
                        placeholder="e.g. There has been no water in our street for three days")
    if st.button("Classify", type="primary"):
        if not text.strip():
            st.warning("Please type a complaint first.")
        else:
            r = call("POST", "/predict", json={"text": text})
            if r is not None:
                res = r.json()
                st.subheader(res["category"])
                st.progress(min(max(res["confidence"], 0.0), 1.0),
                            text=f"Confidence: {res['confidence']:.0%}")
                if res["needs_review"]:
                    st.warning("Low confidence: this complaint has been flagged for admin review.")
                st.write("Top 3 categories")
                st.dataframe(pd.DataFrame(res["top3"]), hide_index=True, use_container_width=True)

# ----------------------------------------------------------- Admin Review
elif page == "Admin Review":
    st.header("Admin review")
    cats = call("GET", "/categories")
    pending = call("GET", "/predictions", params={"needs_review": True, "limit": 200})
    if cats is not None and pending is not None:
        categories = cats.json()["categories"]
        items = pending.json()["items"]
        st.subheader(f"Low-confidence predictions ({len(items)})")
        if items:
            df = pd.DataFrame(items)[["timestamp", "text", "predicted", "confidence"]]
            st.dataframe(df, hide_index=True, use_container_width=True)
            idx = st.selectbox("Pick a complaint to correct", range(len(items)),
                               format_func=lambda i: f"{items[i]['text'][:80]}  →  {items[i]['predicted']}")
            chosen = items[idx]
            default = categories.index(chosen["predicted"]) if chosen["predicted"] in categories else 0
            new_cat = st.selectbox("Correct category", categories, index=default)
            if st.button("Save correction"):
                r = call("POST", "/correct", json={"text": chosen["text"],
                                                   "predicted": chosen["predicted"],
                                                   "correct_category": new_cat})
                if r is not None:
                    st.success("Correction saved. Retrain to apply it.")
                    st.rerun()
        else:
            st.info("Nothing waiting for review.")

        st.divider()
        st.subheader("Retrain")
        if st.button("Retrain model with corrections"):
            with st.spinner("Retraining..."):
                r = call("POST", "/retrain")
            if r is not None:
                res = r.json()
                c1, c2, c3 = st.columns(3)
                before = res["before_accuracy"]
                c1.metric("Before", "n/a" if before is None else f"{before:.1%}")
                c2.metric("After", f"{res['after_accuracy']:.1%}",
                          None if before is None else f"{res['after_accuracy'] - before:+.1%}")
                c3.metric("Corrections used", res["n_corrections_used"])
                st.caption("Old and new models are both scored on the same new test split.")

        st.divider()
        st.subheader("Export")
        e1, e2 = st.columns(2)
        for col, path, label, name in [
            (e1, "/export/predictions", "Download predictions CSV", "predictions.csv"),
            (e2, "/export/corrections", "Download corrections CSV", "corrections.csv"),
        ]:
            r = call("GET", path)
            if r is not None:
                col.download_button(label, r.content, file_name=name, mime="text/csv")

# ------------------------------------------------------------- Evaluation
else:
    st.header("Model evaluation")
    r = call("GET", "/metrics")
    if r is not None:
        m = r.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Accuracy", f"{m['accuracy']:.1%}")
        c2.metric("Training rows", m["n_train"])
        c3.metric("Test rows", m["n_test"])

        st.subheader("Per-class report")
        rep = pd.DataFrame(m["classification_report"]).T
        rep = rep.loc[m["labels"]][["precision", "recall", "f1-score", "support"]]
        st.dataframe(rep.round(3), use_container_width=True)

        st.subheader("Confusion matrix")
        labels = m["labels"]
        cm = pd.DataFrame(m["confusion_matrix"], index=labels, columns=labels)
        long = cm.reset_index().melt(id_vars="index", var_name="Predicted", value_name="Count")
        long = long.rename(columns={"index": "Actual"})
        base = alt.Chart(long).encode(x=alt.X("Predicted:N", sort=labels),
                                      y=alt.Y("Actual:N", sort=labels))
        heat = base.mark_rect().encode(color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")))
        numbers =  base.mark_text().encode(
        text="Count:Q",
        color=alt.condition(alt.datum.Count > 12, alt.value("white"), alt.value("black")),
)
        st.altair_chart((heat + numbers).properties(height=420), use_container_width=True)
