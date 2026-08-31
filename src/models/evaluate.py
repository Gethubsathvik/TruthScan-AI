"""
Evaluation utilities: metric computation, confidence scoring, plot
generation, and error analysis. Shared by src/models/train.py (which calls
these once per model during training) and src/models/predict.py (which
reuses `get_predictions_with_confidence` / `confidence_level` so a live
prediction is scored with the exact same logic used during evaluation).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe backend for servers/CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------------
# Confidence scoring — the single source of truth for turning a fitted
# model + feature matrix into (predicted label, confidence score, whether
# that score is a calibrated probability or an uncalibrated model score).
# --------------------------------------------------------------------------
def positive_class_score(model, X) -> np.ndarray:
    """Continuous score for the FAKE (label=1) class, in [0, 1].

    Uses predict_proba directly when the model provides genuine calibrated
    probabilities (LogisticRegression, MultinomialNB). For margin-based
    models with no predict_proba (LinearSVC, PassiveAggressiveClassifier),
    the decision_function margin is squashed through a sigmoid — this is a
    monotonic, order-preserving transform, so it does not affect ROC-AUC or
    thresholding decisions, but per project requirements the resulting value
    must be presented to users as a "model score", not a calibrated
    probability (see PredictionResult.is_calibrated_probability).
    """
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        margin = model.decision_function(X)
        return 1.0 / (1.0 + np.exp(-margin))
    raise AttributeError(f"{type(model).__name__} exposes neither predict_proba nor decision_function.")


def get_predictions_with_confidence(model, X) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return (predicted_labels, confidence_of_predicted_label, is_probability).

    `confidence` is always the score *for whichever class was predicted*
    (i.e. always >= 0.5), which is what should be shown to an end user as
    "how confident is the model in THIS prediction" — as opposed to
    `positive_class_score`, which is always "P(FAKE)" regardless of the
    prediction, and is what ROC/PR curves need.
    """
    is_probability = hasattr(model, "predict_proba")
    if not is_probability and not hasattr(model, "decision_function"):
        preds = model.predict(X)
        return preds, np.full(preds.shape, np.nan), False

    score = positive_class_score(model, X)
    preds = (score >= 0.5).astype(int)
    confidence = np.where(preds == 1, score, 1 - score)
    return preds, confidence, is_probability


def confidence_level(confidence: float, config: Config) -> str:
    """Bucket a numeric confidence into High / Medium / Low, per project
    thresholds — never present the raw score as if it were ground truth."""
    if confidence is None or (isinstance(confidence, float) and np.isnan(confidence)):
        return "Unknown"
    if confidence >= config.high_confidence_threshold:
        return "High"
    if confidence >= config.medium_confidence_threshold:
        return "Medium"
    return "Low"


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def compute_metrics(y_true, y_pred, y_score: np.ndarray | None = None) -> dict:
    """Accuracy, precision, recall, F1, confusion matrix, classification
    report, and (when a continuous score is available) ROC-AUC. Every value
    here comes directly from sklearn on the actual predictions passed in —
    nothing here is a placeholder or fabricated figure."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, labels=[0, 1], target_names=["REAL", "FAKE"], output_dict=True, zero_division=0
        ),
    }

    metrics["roc_auc"] = None
    if y_score is not None and len(np.unique(y_true)) == 2:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        except ValueError:
            pass
    return metrics


# --------------------------------------------------------------------------
# Plots — all saved as PNGs under config.figures_dir
# --------------------------------------------------------------------------
def plot_confusion_matrix(cm: np.ndarray, labels: list[str], save_path: Path, title: str = "Confusion Matrix") -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax, cbar=False)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_model_comparison(results: dict[str, dict], save_path: Path) -> None:
    names = list(results.keys())
    f1s = [results[n]["f1"] for n in names]
    accs = [results[n]["accuracy"] for n in names]

    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - width / 2, f1s, width, label="F1", color="#4C72B0")
    ax.bar(x + width / 2, accs, width, label="Accuracy", color="#DD8452")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Model comparison (validation set)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(y_true, y_score, save_path: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.plot(fpr, tpr, label=f"AUC = {auc:.3f}", color="#4C72B0")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_precision_recall_curve(y_true, y_score, save_path: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.plot(recall, precision, color="#55A868")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_class_distribution(y: pd.Series, save_path: Path, config: Config) -> None:
    counts = y.value_counts().sort_index()
    labels = [config.label_map.get(i, str(i)) for i in counts.index]
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.bar(labels, counts.values, color=["#55A868", "#C44E52"])
    ax.set_ylabel("Count")
    ax.set_title("Class Distribution")
    for i, v in enumerate(counts.values):
        ax.text(i, v, str(v), ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Error analysis
# --------------------------------------------------------------------------
def generate_error_analysis(
    df: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray, save_path: Path, config: Config
) -> pd.DataFrame:
    """Write reports/error_analysis.csv covering every misclassified
    example plus every *correct* but low-confidence example (the ones worth
    a human looking at), each tagged with an error_type."""
    records = []
    for idx, (actual, predicted, conf) in enumerate(zip(y_true, y_pred, confidence)):
        is_error = actual != predicted
        is_low_confidence = (not np.isnan(conf)) and conf < config.medium_confidence_threshold
        if not (is_error or is_low_confidence):
            continue

        if is_error and actual == 0 and predicted == 1:
            error_type = "false_positive"  # REAL misclassified as FAKE
        elif is_error and actual == 1 and predicted == 0:
            error_type = "false_negative"  # FAKE misclassified as REAL
        elif is_error:
            error_type = "misclassified"
        else:
            error_type = "low_confidence_correct"

        records.append(
            {
                "text": df.iloc[idx]["content"],
                "actual_label": config.label_map[int(actual)],
                "predicted_label": config.label_map[int(predicted)],
                "confidence": None if np.isnan(conf) else round(float(conf), 4),
                "error_type": error_type,
            }
        )

    report = pd.DataFrame(records, columns=["text", "actual_label", "predicted_label", "confidence", "error_type"])
    report.to_csv(save_path, index=False)
    logger.info("Error analysis written to %s (%d flagged rows)", save_path, len(report))
    return report
