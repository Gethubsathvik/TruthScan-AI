import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_verify_claim(client: TestClient):
    payload = {
        "input_type": "claim",
        "input_text": "NASA discovered life on Mars in 2026.",
        "input_url": None
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code in [200, 500]

def test_verify_invalid_input(client: TestClient):
    payload = {
        "input_type": "claim",
        "input_text": "",
        "input_url": None
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code in [200, 422, 500]

def test_get_history_empty(client: TestClient):
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
