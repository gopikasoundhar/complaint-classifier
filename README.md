# Complaint Category Classifier (PRJ-076)

A machine learning service that reads a citizen complaint and assigns it to a category
(Water Supply, Roads, Electricity, Sanitation, Public Transport, Healthcare). Predictions
come with a confidence score; low-confidence ones are flagged for an admin, who can correct
them and retrain the model from a dashboard.

**Author:** Gopika S, Cyber Department, PDKV (Reg No 411623149012)

- Live API: `<add Render URL>` (docs at `/docs`)
- Live dashboard: `<add Streamlit URL>`
- Demo video: `<add link>`

## Features
- TF-IDF (1-2 grams) + Logistic Regression text classifier
- FastAPI backend with input validation (empty, symbols-only, over-length text rejected)
- Confidence score, top-3 categories, and a `needs_review` flag (confidence below 0.6)
- Admin correction loop: save corrections, retrain, compare accuracy before and after
- Streamlit dashboard: Predict, Admin Review, Evaluation (per-class table, confusion matrix)
- CSV export of predictions and corrections
- Optional API-key protection for admin endpoints
- 17 pytest tests

## Project structure
```
app/            config, preprocessing, training, FastAPI app
dashboard/      Streamlit dashboard
data/           complaints.csv (dataset), corrections.csv / predictions_log.csv (created at runtime)
model/          model.joblib + metrics.json (created by training)
scripts/        generate_dataset.py
tests/          pytest suite
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python -m app.train            # creates model/model.joblib and model/metrics.json
python -m uvicorn app.main:app --reload
```
In a second terminal:
```bash
streamlit run dashboard/streamlit_app.py
```
API docs: http://localhost:8000/docs

Optional configuration (see `.env.example`): `ADMIN_API_KEY`, `CONFIDENCE_THRESHOLD`,
`MAX_TEXT_LENGTH`, `API_URL` (dashboard). Never commit a real `.env`.

## API examples
```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
     -d '{"text": "No water in my house since morning"}'
```
```json
{"category": "Water Supply", "confidence": 0.7424, "needs_review": false,
 "top3": [{"category": "Water Supply", "confidence": 0.7424},
          {"category": "Healthcare", "confidence": 0.0634},
          {"category": "Sanitation", "confidence": 0.0633}]}
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and model status |
| GET | `/categories` | Known categories |
| POST | `/predict` | Classify a complaint |
| POST | `/correct` | Save an admin correction `{text, predicted, correct_category}` |
| POST | `/retrain` | Merge corrections, retrain, return before/after accuracy |
| GET | `/metrics` | Contents of `metrics.json` |
| GET | `/predictions` | Logged predictions awaiting review |
| GET | `/export/predictions`, `/export/corrections` | CSV downloads |

`/correct`, `/retrain`, `/predictions` and `/export/*` require the `X-API-Key` header when
`ADMIN_API_KEY` is set.

## Results
Hold-out test set: 20% of the data, stratified, `random_state=42`.

| Metric | Value |
|---|---|
| Accuracy | 99.4% (156 test rows) |
| Per-class F1 | 0.98 to 1.00 |

**Important caveat:** the bundled dataset is a starter set generated from hand-written
complaint phrases with varied wording (`scripts/generate_dataset.py`). Because test rows share
phrases with training rows, this accuracy is optimistic. Real complaints are messier, so expect
lower numbers; adding real or self-written complaints is the best way to improve the model.

## Tests
```bash
python -m pytest -v
```
Covers text cleaning (empty text, symbols, non-English), the API (valid, empty, over-long,
gibberish, non-English input), and the correct, retrain and export flow. Result: 17 passed.

## Deployment
- **API (Render):** `render.yaml` installs dependencies, trains the model at build time, and
  starts uvicorn. Set `ADMIN_API_KEY` in Render's environment settings. The free tier sleeps
  when idle (first request is slow) and its disk is reset on redeploy, so corrections saved
  there are temporary.
- **Dashboard (Streamlit Community Cloud):** main file `dashboard/streamlit_app.py`; in the
  app's Secrets set `API_URL` and `ADMIN_API_KEY` (see `.streamlit/secrets.toml.example`).

## Screenshots
`<add: Predict page, review flag, Admin Review, Evaluation page, /docs>`

## Limitations
- Six fixed categories; a complaint outside them is forced into the closest one (low confidence
  helps flag these).
- English only; Tamil or mixed-language text is flagged for review rather than understood.
- Single-label classification: a complaint covering two issues gets one category.
