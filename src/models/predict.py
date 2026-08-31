"""
Prediction service: the single code path used by both app.py (Streamlit)
and api.py (FastAPI), so prediction logic is never duplicated or allowed to
drift between the two front ends (see FASTAPI: "Keep prediction logic
independent from Streamlit and FastAPI").
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp

from src.data.loader import detect_columns
from src.explainability.explainer import FeatureContribution, explain_prediction
from src.features.numeric_features import NUMERIC_FEATURE_NAMES, extract_stylistic_features
from src.features.tfidf_features import get_feature_names
from src.models.evaluate import confidence_level, get_predictions_with_confidence
from src.preprocessing.text_cleaner import build_default_cleaner
from src.utils.config import Config
from src.utils.config import config as default_config
from src.utils.logger import get_logger, safe_preview
from src.utils.text_utils import combine_title_text

logger = get_logger(__name__)

DISCLAIMER = (
    "This is a machine-learning text classifier trained to recognize linguistic "
    "patterns associated with fake or real news in its training data. It is NOT "
    "an authoritative fact-checker and does not verify claims against real-world "
    "evidence. Always cross-check important claims with trusted, independent "
    "sources."
)


class ModelNotFoundError(Exception):
    """Raised when trained model artifacts can't be found on disk."""


class EmptyInputError(Exception):
    """Raised when there is no usable text to classify."""


@dataclass
class PredictionResult:
    prediction: str
    confidence: float | None
    confidence_level: str
    is_calibrated_probability: bool
    model_name: str
    top_features: list[FeatureContribution] = field(default_factory=list)
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "prediction": self.prediction,
            "confidence": None if self.confidence is None or np.isnan(self.confidence) else round(float(self.confidence), 4),
            "confidence_level": self.confidence_level,
            "is_calibrated_probability": self.is_calibrated_probability,
            "model": self.model_name,
            "top_features": [
                {"feature": c.feature, "weight": c.weight, "direction": c.direction} for c in self.top_features
            ],
            "disclaimer": self.disclaimer,
        }


class PredictionService:
    """Loads persisted model artifacts once and serves predictions.

    Both app.py (behind st.cache_resource) and api.py (behind an
    lru_cache-backed FastAPI dependency) construct exactly one instance of
    this per process.
    """

    def __init__(self, config: Config = default_config):
        self.config = config
        self.cleaner = build_default_cleaner()
        self.model = self._load_artifact(config.model_path, "model")
        self.vectorizer = self._load_artifact(config.vectorizer_path, "TF-IDF vectorizer")
        self.scaler = self._load_artifact(config.scaler_path, "numeric feature scaler")
        self.metadata = self._load_metadata(config.metadata_path)
        self.feature_names = get_feature_names(self.vectorizer)
        self.model_name = self.metadata.get("model_name", type(self.model).__name__)

    @staticmethod
    def _load_artifact(path: Path, label: str):
        if not path.exists():
            raise ModelNotFoundError(
                f"Could not find the trained {label} at {path}. Run `python train.py` "
                f"first to train and save the model."
            )
        return joblib.load(path)

    @staticmethod
    def _load_metadata(path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _build_feature_row(self, title: str, text: str) -> tuple[sp.csr_matrix, str]:
        content = combine_title_text(title, text)[: self.config.max_input_chars]

        clean_text = self.cleaner.clean(content)
        numeric = extract_stylistic_features(content)

        tfidf_row = self.vectorizer.transform([clean_text])
        numeric_row = self.scaler.transform(pd.DataFrame([numeric])[NUMERIC_FEATURE_NAMES].to_numpy(dtype=float))
        fused = sp.hstack([tfidf_row, sp.csr_matrix(numeric_row)], format="csr")
        return fused, content

    def predict(self, title: str = "", text: str = "") -> PredictionResult:
        content = combine_title_text(title, text)
        if not content.strip():
            raise EmptyInputError("Please provide a headline and/or article body to classify.")

        logger.info("Prediction requested for %s", safe_preview(content))

        feature_row, _content = self._build_feature_row(title, text)
        preds, confidence, is_prob = get_predictions_with_confidence(self.model, feature_row)
        pred_label = int(preds[0])
        conf_value = float(confidence[0])

        top_features = explain_prediction(self.model, feature_row, self.feature_names, top_n=10)

        result = PredictionResult(
            prediction=self.config.label_map[pred_label],
            confidence=conf_value,
            confidence_level=confidence_level(conf_value, self.config),
            is_calibrated_probability=is_prob,
            model_name=self.model_name,
            top_features=top_features,
        )
        logger.info(
            "Prediction result: %s (confidence=%.4f, level=%s)",
            result.prediction,
            conf_value,
            result.confidence_level,
        )
        return result

    @staticmethod
    def _detect_batch_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
        cols = detect_columns(df)
        return cols["title"], cols["text"]

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized batch prediction for CSV upload: builds the fused
        feature matrix for the whole DataFrame in one pass (rather than
        looping per row), so this scales to realistically-sized uploads."""
        title_col, text_col = self._detect_batch_columns(df)
        if title_col is None and text_col is None:
            raise EmptyInputError(
                "Could not find a title/headline or text/article column in the "
                "uploaded CSV. Expected a column such as 'title', 'headline', "
                "'text', 'article', or 'content'."
            )

        titles = df[title_col].fillna("").astype(str) if title_col else pd.Series([""] * len(df), index=df.index)
        texts = df[text_col].fillna("").astype(str) if text_col else pd.Series([""] * len(df), index=df.index)
        contents = [
            combine_title_text(t, x)[: self.config.max_input_chars] for t, x in zip(titles, texts)
        ]
        valid_mask = [bool(c.strip()) for c in contents]

        clean_texts = [self.cleaner.clean(c) if v else "" for c, v in zip(contents, valid_mask)]
        numeric_records = [
            extract_stylistic_features(c) if v else {k: 0.0 for k in NUMERIC_FEATURE_NAMES}
            for c, v in zip(contents, valid_mask)
        ]

        tfidf_matrix = self.vectorizer.transform(clean_texts)
        numeric_matrix = self.scaler.transform(
            pd.DataFrame(numeric_records)[NUMERIC_FEATURE_NAMES].to_numpy(dtype=float)
        )
        fused = sp.hstack([tfidf_matrix, sp.csr_matrix(numeric_matrix)], format="csr")

        preds, confidence, _is_prob = get_predictions_with_confidence(self.model, fused)

        out = df.copy()
        out["prediction"] = [self.config.label_map[int(p)] if v else None for p, v in zip(preds, valid_mask)]
        out["confidence"] = [
            round(float(c), 4) if v and not np.isnan(c) else None for c, v in zip(confidence, valid_mask)
        ]
        out["confidence_level"] = [
            confidence_level(c, self.config) if v and not np.isnan(c) else "Unknown"
            for c, v in zip(confidence, valid_mask)
        ]
        logger.info("Batch prediction: %d rows (%d valid)", len(df), sum(valid_mask))
        return out
