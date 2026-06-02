from fastapi.testclient import TestClient

from fraudlens.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint_returns_complete_result():
    response = client.post(
        "/analyze",
        json={"text": "Urgent KYC update required at http://bank-kyc-verify.example/login or account block today."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_label"] in {"kyc_scam", "unknown"}
    assert payload["risk_level"] in {"low", "medium", "high"}
    assert isinstance(payload["entities"], list)
    assert payload["explanation"]

