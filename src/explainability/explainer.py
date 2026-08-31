"""
Explainability for the linear/Naive-Bayes models used in this project.

Two kinds of explanation are produced:
  * Global: the overall top positive (FAKE-leaning) and negative
    (REAL-leaning) weighted features the model learned across the whole
    training set — useful for the Model Performance / About pages.
  * Local: for one specific input, which of its *active* features
    contributed most to that particular prediction (coefficient x feature
    value) — this is what the Streamlit app and API surface per prediction.

IMPORTANT: everything returned by this module is a learned statistical
association from the training data, not independent evidence that a claim
is true or false. Every caller must present these alongside that caveat
(see DISCLAIMER in src/models/predict.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FeatureContribution:
    feature: str
    weight: float
    direction: str  # "FAKE" or "REAL"


def _feature_importance_vector(model) -> np.ndarray | None:
    """Best-effort extraction of a per-feature importance vector, where a
    higher value is more indicative of FAKE (label=1). Returns None (rather
    than raising) for model types this project doesn't know how to explain,
    so callers can degrade gracefully instead of crashing."""
    if hasattr(model, "coef_"):
        coef = np.asarray(model.coef_)
        return coef[0] if coef.ndim == 2 else coef

    if hasattr(model, "feature_log_prob_"):
        # MultinomialNB: log P(feature | class). The difference in
        # log-probability between FAKE and REAL approximates a coefficient:
        # positive => the feature is relatively more common in FAKE text.
        log_prob = np.asarray(model.feature_log_prob_)
        if log_prob.shape[0] == 2:
            return log_prob[1] - log_prob[0]

    logger.warning("Explainability not supported for model type %s", type(model).__name__)
    return None


def global_top_features(model, feature_names: list[str], top_n: int = 15) -> dict:
    """Top global FAKE- and REAL-indicative features the model learned."""
    weights = _feature_importance_vector(model)
    if weights is None:
        return {"fake_indicators": [], "real_indicators": [], "supported": False}

    order = np.argsort(weights)
    top_fake_idx = order[::-1][:top_n]
    top_real_idx = order[:top_n]

    return {
        "fake_indicators": [
            {"feature": feature_names[i], "weight": round(float(weights[i]), 4)}
            for i in top_fake_idx
            if weights[i] > 0
        ],
        "real_indicators": [
            {"feature": feature_names[i], "weight": round(float(weights[i]), 4)}
            for i in top_real_idx
            if weights[i] < 0
        ],
        "supported": True,
    }


def explain_prediction(
    model, feature_row: sp.csr_matrix, feature_names: list[str], top_n: int = 10
) -> list[FeatureContribution]:
    """Explain one prediction: rank only the *active* (non-zero) features
    present in this specific input by |coefficient x value|, so the
    explanation reflects what was actually present in this text — not the
    model's global vocabulary."""
    weights = _feature_importance_vector(model)
    if weights is None:
        return []

    row = feature_row.toarray().ravel() if sp.issparse(feature_row) else np.asarray(feature_row).ravel()
    active_idx = np.nonzero(row)[0]
    if active_idx.size == 0:
        return []

    contributions = weights[active_idx] * row[active_idx]
    ranked = active_idx[np.argsort(-np.abs(contributions))][:top_n]

    results = []
    for i in ranked:
        contribution = float(weights[i] * row[i])
        results.append(
            FeatureContribution(
                feature=feature_names[i],
                weight=round(contribution, 4),
                direction="FAKE" if contribution > 0 else "REAL",
            )
        )
    return results
