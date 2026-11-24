from fastapi.testclient import TestClient

from app import config
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True


def test_predict_valid():
    r = client.post("/predict", json={"text": "There is no water supply in our street since morning"})
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "Water Supply"
    assert 0 <= body["confidence"] <= 1
    assert isinstance(body["needs_review"], bool)
    assert len(body["top3"]) == 3


def test_predict_empty_rejected():
    assert client.post("/predict", json={"text": ""}).status_code == 422
    assert client.post("/predict", json={"text": "    "}).status_code == 422
    assert client.post("/predict", json={}).status_code == 422


def test_predict_symbols_only_rejected():
    assert client.post("/predict", json={"text": "!!! ??? ###"}).status_code == 422


def test_predict_very_long_rejected():
    r = client.post("/predict", json={"text": "water " * 500})
    assert r.status_code == 422


def test_gibberish_flagged_for_review():
    r = client.post("/predict", json={"text": "asdkjh qwe zxcv plmokn"})
    assert r.status_code == 200
    assert r.json()["needs_review"] is True


def test_non_english_does_not_crash():
    r = client.post("/predict", json={"text": "குடிநீர் வரவில்லை"})
    assert r.status_code == 200
    assert r.json()["needs_review"] is True


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "accuracy" in r.json()


def test_correct_rejects_unknown_category():
    r = client.post("/correct", json={"text": "x y", "predicted": "Roads", "correct_category": "Aliens"})
    assert r.status_code == 422


def test_correct_and_retrain_flow():
    text = "the lamp post outside the library is dark every night"
    r = client.post("/correct", json={"text": text, "predicted": "Roads", "correct_category": "Electricity"})
    assert r.status_code == 200
    assert config.CORRECTIONS_PATH.exists()
    r = client.post("/retrain")
    assert r.status_code == 200
    body = r.json()
    assert body["n_corrections_used"] >= 1
    assert body["after_accuracy"] > 0.5
    assert client.post("/predict", json={"text": text}).json()["category"] == "Electricity"


def test_exports():
    assert client.get("/export/predictions").status_code == 200
    r = client.get("/export/corrections")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")


def test_predictions_listing():
    client.post("/predict", json={"text": "asdkjh qwe zxcv listing test"})
    r = client.get("/predictions", params={"needs_review": True})
    assert r.status_code == 200
    assert any("listing test" in i["text"] for i in r.json()["items"])
