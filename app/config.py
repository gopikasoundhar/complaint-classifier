"""Central configuration. Everything overridable through environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "model"))

DATASET_PATH = DATA_DIR / "complaints.csv"
CORRECTIONS_PATH = DATA_DIR / "corrections.csv"
PREDICTIONS_LOG_PATH = DATA_DIR / "predictions_log.csv"
MODEL_PATH = MODEL_DIR / "model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "1000"))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")  # empty = admin endpoints open (local dev only)
