import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app

PAYLOAD = {
    "Hospital County": "Kings",
    "Facility Name": "Mount Sinai Hospital",
    "Age Group": "50 to 69",
    "Gender": "M",
    "Race": "White",
    "Ethnicity": "Not Span/Hispanic",
    "Type of Admission": "Emergency",
    "Patient Disposition": "Home or Self Care",
    "APR MDC Description": "Diseases and Disorders of the Circulatory System",
    "APR Severity of Illness Code": 3,
    "APR Medical Surgical Description": "Medical",
    "Payment Typology 1": "Medicare",
    "Emergency Department Indicator": "Y",
}


def test_health_version_follows_env(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "v9.9.9-test")
    resp = app.test_client().get("/api/health")
    assert resp.get_json()["version"] == "v9.9.9-test"


def test_health_reports_status_and_version():
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] in ("healthy", "degraded")
    assert "model_loaded" in body
    assert "version" in body


def test_predict_happy_path_returns_los():
    client = app.test_client()
    resp = client.post("/api/predict", json=PAYLOAD)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "predicted_los" in body
    assert len(body["confidence_interval"]) == 2
    assert isinstance(body["risk_factors"], list)


def test_predict_metadata_version_follows_env(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "v9.9.9-test")
    resp = app.test_client().post("/api/predict", json=PAYLOAD)
    assert resp.status_code == 200
    assert resp.get_json()["metadata"]["model_version"] == "v9.9.9-test"


def test_predict_rejects_missing_fields_with_400():
    client = app.test_client()
    resp = client.post("/api/predict", json={"Age Group": "50 to 69"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert "missing_fields" in body


def test_model_info_reports_feature_counts():
    client = app.test_client()
    resp = client.get("/api/model-info")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["input_features"] == 13
    assert body["encoded_features"] > 0
    assert "model_type" in body
