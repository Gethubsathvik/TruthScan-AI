"""
Tests for api.py using FastAPI's TestClient and dependency overrides, so
these tests use the synthetic-data trained fixture model rather than
requiring a real pretrained model to be present on disk.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api
from src.models.predict import PredictionService
from src.utils.config import Config, config as default_config


@pytest.fixture()
def client(trained_service_config: Config) -> TestClient:
    api.app.dependency_overrides[api.get_service] = lambda: PredictionService(config=trained_service_config)
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_health_endpoint_does_not_require_a_trained_model():
    test_client = TestClient(api.app)
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_predict_endpoint_returns_valid_schema(client: TestClient):
    response = client.post(
        "/predict",
        json={"title": "", "text": "The transportation department announced a new bus schedule."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] in {"REAL", "FAKE"}
    assert "confidence" in body
    assert body["model"]
    assert "disclaimer" in body
    assert isinstance(body["top_features"], list)


def test_predict_endpoint_rejects_empty_input(client: TestClient):
    response = client.post("/predict", json={"title": "", "text": ""})
    assert response.status_code == 400


def test_predict_endpoint_503_when_model_missing():
    api.get_service.cache_clear()
    test_client = TestClient(api.app)  # no dependency override
    if default_config.model_path.exists():
        pytest.skip("A real trained model is present at the default path; skipping missing-model check.")
    response = test_client.post("/predict", json={"title": "x", "text": "y"})
    assert response.status_code == 503
