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


def test_analyze_endpoint_trims_request_text_and_user_notes():
    response = client.post(
        "/analyze",
        json={"text": "  urgent account verification  ", "user_notes": "  called the sender  "},
    )

    assert response.status_code == 200
    assert response.json()["original_text"] == "urgent account verification"
    assert response.json()["metadata"]["user_notes"] == "called the sender"


def test_analyze_endpoint_rejects_whitespace_only_text():
    response = client.post("/analyze", json={"text": " \t\n "})

    assert response.status_code == 422


def test_analyze_endpoint_rejects_overlong_text():
    response = client.post("/analyze", json={"text": "x" * 20_001})

    assert response.status_code == 422


def test_analyze_endpoint_rejects_unknown_fields():
    response = client.post(
        "/analyze",
        json={"text": "urgent verification", "unexpected": "not accepted"},
    )

    assert response.status_code == 422


def test_analyze_endpoint_converts_whitespace_only_user_notes_to_none():
    response = client.post(
        "/analyze",
        json={"text": "urgent verification", "user_notes": " \n\t "},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["user_notes"] is None


def test_analyze_endpoint_rejects_overlong_user_notes():
    response = client.post(
        "/analyze",
        json={"text": "urgent verification", "user_notes": "x" * 2_001},
    )

    assert response.status_code == 422
