"""
Tests for src/models/predict.py, using a tiny model trained on synthetic
data via the `trained_service_config` fixture (see conftest.py) — these
tests never require the real dataset or a pre-trained model on disk.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.models.predict import EmptyInputError, ModelNotFoundError, PredictionService
from src.utils.config import Config


def test_predict_returns_valid_result(trained_service_config: Config):
    service = PredictionService(config=trained_service_config)
    result = service.predict(title="", text="Officials released the annual budget report on Tuesday.")
    assert result.prediction in {"REAL", "FAKE"}
    assert result.confidence is None or 0.0 <= result.confidence <= 1.0
    assert result.confidence_level in {"High", "Medium", "Low", "Unknown"}
    assert result.model_name
    assert "fact" in result.disclaimer.lower()


def test_predict_raises_on_empty_input(trained_service_config: Config):
    service = PredictionService(config=trained_service_config)
    with pytest.raises(EmptyInputError):
        service.predict(title="", text="")
    with pytest.raises(EmptyInputError):
        service.predict(title="   ", text="\n\t")


def test_predict_missing_model_raises_clear_error(temp_config: Config):
    # temp_config has no trained artifacts yet (that's the point of this test)
    with pytest.raises(ModelNotFoundError):
        PredictionService(config=temp_config)


def test_predict_batch_adds_expected_columns(trained_service_config: Config):
    service = PredictionService(config=trained_service_config)
    df = pd.DataFrame(
        {
            "headline": ["City council approves new budget", "SHOCKING secret exposed"],
            "article": [
                "The council met on Tuesday to review spending on public services.",
                "You won't believe this insane shocking truth they are hiding from you!!!",
            ],
        }
    )
    result = service.predict_batch(df)
    assert "prediction" in result.columns
    assert "confidence" in result.columns
    assert len(result) == len(df)
    assert set(result["prediction"].dropna().unique()) <= {"REAL", "FAKE"}


def test_predict_batch_raises_when_no_text_columns(trained_service_config: Config):
    service = PredictionService(config=trained_service_config)
    df = pd.DataFrame({"unrelated_column": [1, 2, 3]})
    with pytest.raises(EmptyInputError):
        service.predict_batch(df)


def test_predict_batch_handles_blank_rows_gracefully(trained_service_config: Config):
    service = PredictionService(config=trained_service_config)
    df = pd.DataFrame({"title": ["Real headline", ""], "text": ["Some article body text here.", ""]})
    result = service.predict_batch(df)
    # pandas normalizes a missing value assigned into a string column to its
    # own NA representation (which varies by pandas version) rather than
    # preserving the Python `None` object, so pd.isna() is the robust check.
    assert pd.isna(result.loc[1, "prediction"])
    assert result.loc[1, "confidence_level"] == "Unknown"
