"""Point the app at a temporary data/model folder BEFORE importing it, and train there."""
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="cc_test_"))
(TMP / "data").mkdir()
(TMP / "model").mkdir()
shutil.copy(ROOT / "data" / "complaints.csv", TMP / "data" / "complaints.csv")
os.environ["DATA_DIR"] = str(TMP / "data")
os.environ["MODEL_DIR"] = str(TMP / "model")
os.environ["MAX_TEXT_LENGTH"] = "1000"
os.environ.pop("ADMIN_API_KEY", None)

from app.train import train_model  # noqa: E402

train_model()


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(TMP, ignore_errors=True)
