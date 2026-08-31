"""
TF-IDF vectorizer construction and TF-IDF + stylistic-numeric feature fusion.

Design: TfidfVectorizer and the numeric-feature MinMaxScaler are fit on the
TRAINING split only (`fit_transform_features`), then reused transform-only on
validation/test/live-inference data (`transform_features`) — this is what
guarantees TF-IDF never learns anything from validation or test data (see
DATA LEAKAGE requirements). The two feature blocks are fused via
scipy.sparse.hstack into one sparse matrix that every classifier trains on.

MinMaxScaler (rather than StandardScaler) is used for the numeric block
specifically so its output stays non-negative — MultinomialNB requires
non-negative input, and using MinMaxScaler for every model keeps a single,
uniform feature pipeline shared across all four classifiers.

Note on hyperparameter tuning and leakage: for computational efficiency, the
vectorizer/scaler above are fit ONCE on the training split, and the k-fold
cross-validation used for hyperparameter tuning (see src/models/train.py)
runs *within* that already-vectorized training matrix. This is standard,
widely-used practice and does not leak validation/test data — it is a
distinct question from (and much weaker than) the leakage this project
guards against, which is fitting TF-IDF on validation/test/live data. A
maximally strict alternative would refit TF-IDF inside every CV fold via a
full sklearn Pipeline passed to GridSearchCV; we trade that marginal rigor
for materially faster training here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler

from src.features.numeric_features import NUMERIC_FEATURE_NAMES
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_tfidf_vectorizer(config: Config) -> TfidfVectorizer:
    """Construct a TfidfVectorizer from project configuration.

    Operates on already-cleaned text (see src/preprocessing/text_cleaner.py)
    that is whitespace-tokenized and already lowercased, so lowercase=False
    here to avoid redundant work.
    """
    return TfidfVectorizer(
        ngram_range=config.ngram_range,
        max_features=config.max_features,
        min_df=config.min_df,
        max_df=config.max_df,
        sublinear_tf=config.sublinear_tf,
        strip_accents=config.strip_accents,
        lowercase=False,
    )


def build_numeric_scaler() -> MinMaxScaler:
    return MinMaxScaler(feature_range=(0.0, 1.0), clip=True)


def numeric_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Extract the numeric feature columns from df, in the fixed,
    project-wide NUMERIC_FEATURE_NAMES order."""
    missing = [c for c in NUMERIC_FEATURE_NAMES if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing expected numeric feature columns: {missing}")
    return df[NUMERIC_FEATURE_NAMES].to_numpy(dtype=float)


def fit_transform_features(
    df_train: pd.DataFrame, config: Config
) -> tuple[sp.csr_matrix, TfidfVectorizer, MinMaxScaler]:
    """Fit TF-IDF + numeric scaler on the TRAINING split only, and return the
    fused training feature matrix along with both fitted transformers."""
    vectorizer = build_tfidf_vectorizer(config)
    scaler = build_numeric_scaler()

    tfidf_matrix = vectorizer.fit_transform(df_train["clean_text"].fillna(""))
    numeric_matrix = scaler.fit_transform(numeric_feature_matrix(df_train))

    logger.info(
        "Fitted TF-IDF vocabulary size=%d, numeric feature count=%d",
        len(vectorizer.get_feature_names_out()),
        numeric_matrix.shape[1],
    )

    fused = sp.hstack([tfidf_matrix, sp.csr_matrix(numeric_matrix)], format="csr")
    return fused, vectorizer, scaler


def transform_features(df: pd.DataFrame, vectorizer: TfidfVectorizer, scaler: MinMaxScaler) -> sp.csr_matrix:
    """Transform (never fit) a validation/test/inference split using
    already-fitted transformers."""
    tfidf_matrix = vectorizer.transform(df["clean_text"].fillna(""))
    numeric_matrix = scaler.transform(numeric_feature_matrix(df))
    return sp.hstack([tfidf_matrix, sp.csr_matrix(numeric_matrix)], format="csr")


def get_feature_names(vectorizer: TfidfVectorizer) -> list[str]:
    """Full feature-name list in the exact column order produced by
    fit_transform_features / transform_features: TF-IDF vocabulary terms
    first, then the numeric feature names. Used by the explainability
    module to label which column influenced a prediction."""
    return list(vectorizer.get_feature_names_out()) + list(NUMERIC_FEATURE_NAMES)
