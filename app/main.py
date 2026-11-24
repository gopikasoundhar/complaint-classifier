"""FastAPI backend for the Complaint Category Classifier."""
import csv
import io
import json
import secrets
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from app import config
from app.preprocess import clean_text
from app.train import train_model

_lock = threading.Lock()
_state = {"model": None}

PRED_FIELDS = ["timestamp", "text", "predicted", "confidence", "needs_review"]
CORR_FIELDS = ["timestamp", "text", "predicted", "correct_category"]


# ---------- helpers ----------
def load_model():
    if config.MODEL_PATH.exists():
        _state["model"] = joblib.load(config.MODEL_PATH)
    else:
        _state["model"] = None
    return _state["model"]


def get_model():
    model = _state["model"] or load_model()
    if model is None:
        raise HTTPException(503, "Model not trained yet. Run: python -m app.train")
    return model


def require_admin(x_api_key: Optional[str] = Header(default=None)):
    """If ADMIN_API_KEY is set, admin endpoints need a matching X-API-Key header."""
    key = config.ADMIN_API_KEY
    if key and not secrets.compare_digest((x_api_key or "").encode(), key.encode()):
        raise HTTPException(401, "Invalid or missing API key")


def append_row(path, fields, row):
    with _lock:
        new_file = not path.exists() or path.stat().st_size == 0
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if new_file:
                w.writeheader()
            w.writerow(row)


def csv_response(path, fields, filename):
    if path.exists() and path.stat().st_size > 0:
        content = path.read_text(encoding="utf-8")
    else:
        buf = io.StringIO()
        csv.writer(buf).writerow(fields)
        content = buf.getvalue()
    return Response(content, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- schemas ----------
class PredictRequest(BaseModel):
    text: str = Field(..., max_length=config.MAX_TEXT_LENGTH)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class CategoryScore(BaseModel):
    category: str
    confidence: float


class PredictResponse(BaseModel):
    category: str
    confidence: float
    needs_review: bool
    top3: List[CategoryScore]


class CorrectionRequest(BaseModel):
    text: str = Field(..., max_length=config.MAX_TEXT_LENGTH)
    predicted: str
    correct_category: str

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


# ---------- app ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(title="Complaint Category Classifier", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    model = _state["model"] or load_model()
    return {"status": "ok", "model_loaded": model is not None}


@app.get("/categories")
def categories():
    return {"categories": [str(c) for c in get_model().classes_]}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    model = get_model()
    cleaned = clean_text(req.text)
    if not cleaned:
        raise HTTPException(422, "Text has no usable words after cleaning")
    proba = model.predict_proba([cleaned])[0]
    order = np.argsort(proba)[::-1]
    top3 = [CategoryScore(category=str(model.classes_[i]), confidence=round(float(proba[i]), 4))
            for i in order[:3]]
    best = top3[0]
    needs_review = best.confidence < config.CONFIDENCE_THRESHOLD
    append_row(config.PREDICTIONS_LOG_PATH, PRED_FIELDS, {
        "timestamp": now(), "text": req.text.strip(), "predicted": best.category,
        "confidence": best.confidence, "needs_review": needs_review,
    })
    return PredictResponse(category=best.category, confidence=best.confidence,
                           needs_review=needs_review, top3=top3)


@app.post("/correct", dependencies=[Depends(require_admin)])
def correct(req: CorrectionRequest):
    valid = [str(c) for c in get_model().classes_]
    if req.correct_category not in valid:
        raise HTTPException(422, f"correct_category must be one of {valid}")
    append_row(config.CORRECTIONS_PATH, CORR_FIELDS, {
        "timestamp": now(), "text": req.text.strip(),
        "predicted": req.predicted, "correct_category": req.correct_category,
    })
    return {"status": "saved"}


@app.post("/retrain", dependencies=[Depends(require_admin)])
def retrain():
    with _lock:
        metrics = train_model()
    load_model()
    return {
        "status": "retrained",
        "before_accuracy": metrics["before_accuracy"],
        "after_accuracy": metrics["accuracy"],
        "n_samples": metrics["n_samples"],
        "n_corrections_used": metrics["n_corrections_used"],
    }


@app.get("/metrics")
def metrics():
    if not config.METRICS_PATH.exists():
        raise HTTPException(404, "metrics.json not found. Train the model first.")
    return json.loads(config.METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/predictions", dependencies=[Depends(require_admin)])
def predictions(needs_review: bool = True, limit: int = Query(200, ge=1, le=1000)):
    """Logged predictions (newest first), excluding ones an admin already corrected."""
    if not config.PREDICTIONS_LOG_PATH.exists():
        return {"items": []}
    df = pd.read_csv(config.PREDICTIONS_LOG_PATH)
    if needs_review:
        df = df[df["needs_review"].astype(str).str.lower() == "true"]
    if config.CORRECTIONS_PATH.exists():
        done = set(pd.read_csv(config.CORRECTIONS_PATH)["text"].astype(str))
        df = df[~df["text"].astype(str).isin(done)]
    df = df.drop_duplicates(subset="text", keep="last").iloc[::-1].head(limit)
    return {"items": json.loads(df.to_json(orient="records"))}


@app.get("/export/predictions", dependencies=[Depends(require_admin)])
def export_predictions():
    return csv_response(config.PREDICTIONS_LOG_PATH, PRED_FIELDS, "predictions.csv")


@app.get("/export/corrections", dependencies=[Depends(require_admin)])
def export_corrections():
    return csv_response(config.CORRECTIONS_PATH, CORR_FIELDS, "corrections.csv")
