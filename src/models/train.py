"""
Training orchestration for the four classical ML models.

Methodology (see EVALUATION / DATA LEAKAGE / HYPERPARAMETER TUNING
requirements):
  1. Split into stratified train/validation/test (default 70/15/15), fixed
     random_state, computed BEFORE any deduplication-sensitive step runs
     again (dedup already happened once, upstream, in src/data/loader.py).
  2. Fit TF-IDF + numeric scaler on TRAIN ONLY.
  3. For each of the four models, tune hyperparameters with
     GridSearchCV/RandomizedSearchCV using k-fold CV *within the training
     set only* (scoring="f1"), then fit the tuned model on the full
     training set.
  4. Evaluate every tuned model on the VALIDATION set; select the model
     with the best validation F1-score as `best_model`.
  5. Evaluate `best_model` on the TEST set exactly once — those numbers are
     the ones reported as this run's final performance. The test set is
     never touched before this point.
  6. Persist best_model.joblib, tfidf_vectorizer.joblib, numeric_scaler.joblib,
     metadata.json, evaluation reports, figures, and error_analysis.csv.
"""
from __future__ import annotations

import json
import platform
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from src.data.loader import load_and_prepare_dataset
from src.features.numeric_features import NUMERIC_FEATURE_NAMES
from src.features.tfidf_features import fit_transform_features, transform_features
from src.models.evaluate import (
    compute_metrics,
    generate_error_analysis,
    get_predictions_with_confidence,
    plot_class_distribution,
    plot_confusion_matrix,
    plot_model_comparison,
    plot_precision_recall_curve,
    plot_roc_curve,
    positive_class_score,
)
from src.utils.config import Config
from src.utils.config import config as default_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# scikit-learn >= 1.8 deprecates PassiveAggressiveClassifier in favor of
# SGDClassifier(loss="hinge", penalty=None, learning_rate="pa1", eta0=1.0),
# with removal planned for 1.10. It is used here because the project spec
# explicitly calls for a Passive-Aggressive Classifier by name and the class
# is still fully functional — requirements.txt pins scikit-learn<1.10 so
# this keeps working. If you're on scikit-learn>=1.10, swap in the
# SGDClassifier equivalent shown above.
warnings.filterwarnings("ignore", message=".*PassiveAggressiveClassifier is deprecated.*")


@dataclass
class TrainingResult:
    best_model_name: str
    best_params: dict
    val_metrics: dict
    test_metrics: dict
    all_model_val_metrics: dict
    dataset_info: dict


def split_dataset(df: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified 70/15/15 (by default) train/validation/test split with a
    fixed random_state for reproducibility."""
    train_val_df, test_df = train_test_split(
        df, test_size=config.test_size, stratify=df["label"], random_state=config.random_state
    )
    relative_val_size = config.validation_size / (1 - config.test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=relative_val_size,
        stratify=train_val_df["label"],
        random_state=config.random_state,
    )
    for name, part in (("train", train_df), ("validation", val_df), ("test", test_df)):
        logger.info("%s split: %d rows (%.1f%% FAKE)", name, len(part), 100 * part["label"].mean())
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def _build_model_registry(config: Config, quick: bool) -> dict:
    """Model zoo + hyperparameter grids. `quick=True` shrinks the grids for
    fast smoke runs / CI (see HYPERPARAMETER TUNING: "keep tuning
    computationally reasonable")."""
    if quick:
        return {
            "LogisticRegression": {
                "estimator": LogisticRegression(max_iter=1000, random_state=config.random_state),
                "param_grid": {"C": [0.1, 1], "class_weight": [None, "balanced"]},
            },
            "MultinomialNB": {
                "estimator": MultinomialNB(),
                "param_grid": {"alpha": [0.1, 1.0]},
            },
            "LinearSVC": {
                "estimator": LinearSVC(max_iter=2000, random_state=config.random_state),
                "param_grid": {"C": [0.1, 1]},
            },
            "PassiveAggressiveClassifier": {
                "estimator": PassiveAggressiveClassifier(random_state=config.random_state, max_iter=1000),
                "param_grid": {"C": [0.1, 1]},
            },
        }
    return {
        "LogisticRegression": {
            "estimator": LogisticRegression(max_iter=2000, random_state=config.random_state),
            "param_grid": {
                "C": [0.01, 0.1, 1, 10],
                "class_weight": [None, "balanced"],
                "solver": ["liblinear", "lbfgs"],
            },
        },
        "MultinomialNB": {
            "estimator": MultinomialNB(),
            "param_grid": {"alpha": [0.01, 0.1, 0.5, 1.0]},
        },
        "LinearSVC": {
            "estimator": LinearSVC(max_iter=5000, random_state=config.random_state),
            "param_grid": {"C": [0.01, 0.1, 1, 10], "class_weight": [None, "balanced"]},
        },
        "PassiveAggressiveClassifier": {
            "estimator": PassiveAggressiveClassifier(random_state=config.random_state),
            "param_grid": {"C": [0.01, 0.1, 1, 10], "max_iter": [1000, 2000]},
        },
    }


def _grid_size(param_grid: dict) -> int:
    size = 1
    for values in param_grid.values():
        size *= len(values)
    return size


def _tune_or_fit(name: str, spec: dict, X_train, y_train, config: Config, do_tune: bool):
    estimator = spec["estimator"]
    param_grid = spec["param_grid"]

    if not do_tune:
        estimator.fit(X_train, y_train)
        return estimator, {}

    cv = StratifiedKFold(n_splits=config.cv_folds, shuffle=True, random_state=config.random_state)
    if config.tuning_search_type == "random":
        search = RandomizedSearchCV(
            estimator,
            param_grid,
            n_iter=min(config.random_search_iterations, _grid_size(param_grid)),
            scoring="f1",
            cv=cv,
            random_state=config.random_state,
            n_jobs=-1,
        )
    else:
        search = GridSearchCV(estimator, param_grid, scoring="f1", cv=cv, n_jobs=-1)

    logger.info("Tuning %s over %d parameter combination(s)...", name, _grid_size(param_grid))
    search.fit(X_train, y_train)
    logger.info("%s best params: %s (cv f1=%.4f)", name, search.best_params_, search.best_score_)
    return search.best_estimator_, search.best_params_


def _package_versions() -> dict:
    versions = {
        "python": platform.python_version(),
        "scikit-learn": sklearn.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
    }
    try:
        import nltk

        versions["nltk"] = nltk.__version__
    except ImportError:
        versions["nltk"] = "not installed (fallback preprocessing used)"
    return versions


def _build_metadata(
    model_name: str,
    best_params: dict,
    dataset_info: dict,
    config: Config,
    vectorizer,
    val_metrics: dict,
    test_metrics: dict,
    is_calibrated_probability: bool,
) -> dict:
    return {
        "model_name": model_name,
        "model_version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "best_hyperparameters": best_params,
        "dataset_info": dataset_info,
        "feature_config": {
            "ngram_range": list(config.ngram_range),
            "max_features": config.max_features,
            "min_df": config.min_df,
            "max_df": config.max_df,
            "sublinear_tf": config.sublinear_tf,
            "tfidf_vocabulary_size": len(vectorizer.get_feature_names_out()),
            "numeric_features": NUMERIC_FEATURE_NAMES,
        },
        "evaluation_metrics": {
            "validation": {k: v for k, v in val_metrics.items() if k != "classification_report"},
            "test": {k: v for k, v in test_metrics.items() if k != "classification_report"},
        },
        "confidence_is_calibrated_probability": is_calibrated_probability,
        "label_map": {str(k): v for k, v in config.label_map.items()},
        "package_versions": _package_versions(),
    }


def run_training_pipeline(
    config: Config = default_config,
    raw_dir: Path | None = None,
    quick: bool = False,
    tune: bool | None = None,
) -> TrainingResult:
    """Full training pipeline: load -> split -> vectorize -> tune/fit all
    four models -> select best by validation F1 -> evaluate once on test ->
    persist everything. Returns a TrainingResult summarizing the run."""
    config.ensure_directories()
    do_tune = config.enable_tuning if tune is None else tune

    df = load_and_prepare_dataset(raw_dir=raw_dir, config=config)
    train_df, val_df, test_df = split_dataset(df, config)

    X_train, vectorizer, scaler = fit_transform_features(train_df, config)
    y_train = train_df["label"].to_numpy()
    X_val = transform_features(val_df, vectorizer, scaler)
    y_val = val_df["label"].to_numpy()
    X_test = transform_features(test_df, vectorizer, scaler)
    y_test = test_df["label"].to_numpy()

    registry = _build_model_registry(config, quick=quick)

    all_val_metrics: dict[str, dict] = {}
    fitted_models: dict[str, object] = {}
    best_params_by_model: dict[str, dict] = {}

    for name, spec in registry.items():
        model, best_params = _tune_or_fit(name, spec, X_train, y_train, config, do_tune)
        fitted_models[name] = model
        best_params_by_model[name] = best_params

        y_pred, _confidence, _is_prob = get_predictions_with_confidence(model, X_val)
        score = positive_class_score(model, X_val)
        metrics = compute_metrics(y_val, y_pred, y_score=score)
        all_val_metrics[name] = metrics
        logger.info(
            "%s validation: accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f",
            name,
            metrics["accuracy"],
            metrics["precision"],
            metrics["recall"],
            metrics["f1"],
        )

    best_model_name = max(all_val_metrics, key=lambda n: all_val_metrics[n]["f1"])
    best_model = fitted_models[best_model_name]
    logger.info("Selected best model by validation F1: %s", best_model_name)

    y_test_pred, test_confidence, test_is_prob = get_predictions_with_confidence(best_model, X_test)
    test_score = positive_class_score(best_model, X_test)
    test_metrics = compute_metrics(y_test, y_test_pred, y_score=test_score)
    logger.info(
        "%s TEST metrics (held-out, evaluated once): accuracy=%.4f f1=%.4f roc_auc=%s",
        best_model_name,
        test_metrics["accuracy"],
        test_metrics["f1"],
        test_metrics["roc_auc"],
    )

    # --- Reports & figures --------------------------------------------
    plot_class_distribution(df["label"], config.figures_dir / "class_distribution.png", config)
    plot_model_comparison(all_val_metrics, config.figures_dir / "model_comparison.png")
    plot_confusion_matrix(
        np.array(test_metrics["confusion_matrix"]),
        ["REAL", "FAKE"],
        config.figures_dir / "confusion_matrix_test.png",
        title=f"{best_model_name} — Test Confusion Matrix",
    )
    plot_roc_curve(y_test, test_score, config.figures_dir / "roc_curve_test.png")
    plot_precision_recall_curve(y_test, test_score, config.figures_dir / "pr_curve_test.png")

    generate_error_analysis(test_df, y_test, y_test_pred, test_confidence, config.error_analysis_path, config)

    with open(config.metrics_dir / "validation_metrics_all_models.json", "w") as f:
        json.dump(all_val_metrics, f, indent=2)
    with open(config.metrics_dir / "test_metrics_best_model.json", "w") as f:
        json.dump(test_metrics, f, indent=2)

    # --- Persist model artifacts ----------------------------------------
    joblib.dump(best_model, config.model_path)
    joblib.dump(vectorizer, config.vectorizer_path)
    joblib.dump(scaler, config.scaler_path)

    dataset_info = {
        "n_total": len(df),
        "n_train": len(train_df),
        "n_validation": len(val_df),
        "n_test": len(test_df),
        "class_distribution": {config.label_map[k]: int(v) for k, v in df["label"].value_counts().items()},
    }

    metadata = _build_metadata(
        model_name=best_model_name,
        best_params=best_params_by_model[best_model_name],
        dataset_info=dataset_info,
        config=config,
        vectorizer=vectorizer,
        val_metrics=all_val_metrics[best_model_name],
        test_metrics=test_metrics,
        is_calibrated_probability=test_is_prob,
    )
    with open(config.metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Saved model to %s", config.model_path)
    logger.info("Saved vectorizer to %s", config.vectorizer_path)
    logger.info("Saved metadata to %s", config.metadata_path)

    return TrainingResult(
        best_model_name=best_model_name,
        best_params=best_params_by_model[best_model_name],
        val_metrics=all_val_metrics[best_model_name],
        test_metrics=test_metrics,
        all_model_val_metrics=all_val_metrics,
        dataset_info=dataset_info,
    )
