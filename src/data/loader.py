"""
Dataset loading, column-format detection, normalization, and cleaning.

Supports two raw dataset layouts, auto-detected from what's in
config.raw_data_dir:

  1. The classic Kaggle "Fake and Real News Dataset" layout: separate
     Fake.csv and True.csv files (label implied by which file a row is in).
  2. A single CSV/TSV (or several) with title/text/label-style columns,
     auto-detected from common name variants — this also covers datasets
     like LIAR once its 6-way label has been collapsed to binary REAL/FAKE
     (see data/raw/README.md for a ready-to-run conversion snippet).

The output of `load_and_prepare_dataset()` always has columns:
    title, text, content, label (0=REAL, 1=FAKE),
    clean_text, and the NUMERIC_FEATURE_NAMES columns,
ready to be split and vectorized by src/models/train.py.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.features.numeric_features import extract_stylistic_features
from src.preprocessing.text_cleaner import build_default_cleaner
from src.utils.config import Config
from src.utils.config import config as default_config
from src.utils.logger import get_logger
from src.utils.text_utils import combine_title_text

logger = get_logger(__name__)

_TITLE_COLUMN_ALIASES = {"title", "headline", "news_title", "head"}
_TEXT_COLUMN_ALIASES = {"text", "article", "content", "body", "news_text", "articles", "statement"}
_LABEL_COLUMN_ALIASES = {"label", "class", "target", "type", "news_type"}

_FAKE_LABEL_STRINGS = {"fake", "false", "unreliable"}
_REAL_LABEL_STRINGS = {"real", "true", "reliable"}


class DataValidationError(Exception):
    """Raised when a raw dataset cannot be located or normalized into a
    usable title/text/label schema. Callers (CLI, Streamlit, API) should
    catch this and show the message directly — it's always written to be
    actionable."""


def _normalize_col_name(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Map a raw DataFrame's actual column names to the logical roles
    (title/text/label) they play, using case-insensitive alias matching.
    Shared by the training-time loader and the batch-prediction path in
    src/models/predict.py, so both recognize the same column variants."""
    normalized = {c: _normalize_col_name(c) for c in df.columns}
    title_col = next((c for c, n in normalized.items() if n in _TITLE_COLUMN_ALIASES), None)
    text_col = next((c for c, n in normalized.items() if n in _TEXT_COLUMN_ALIASES), None)
    label_col = next((c for c, n in normalized.items() if n in _LABEL_COLUMN_ALIASES), None)
    return {"title": title_col, "text": text_col, "label": label_col}


def _coerce_label(value) -> int | None:
    """Normalize many possible label encodings to 0 (REAL) / 1 (FAKE) /
    None (unrecognized). Tries a numeric interpretation first (handles
    0/1, 0.0/1.0, and numpy numeric dtypes uniformly), then falls back to
    string matching for text labels like 'FAKE'/'real'/'Unreliable'."""
    if pd.isna(value):
        return None

    try:
        as_float = float(value)
    except (TypeError, ValueError):
        as_float = None

    if as_float is not None:
        if as_float == 1.0:
            return 1
        if as_float == 0.0:
            return 0
        return None

    key = str(value).strip().lower()
    if key in _FAKE_LABEL_STRINGS:
        return 1
    if key in _REAL_LABEL_STRINGS:
        return 0
    return None


def _read_table(path: Path) -> pd.DataFrame:
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    return pd.read_csv(path, sep=sep)


def _load_single_file_dataset(path: Path) -> pd.DataFrame:
    df = _read_table(path)
    cols = detect_columns(df)
    if cols["label"] is None:
        raise DataValidationError(
            f"Could not find a label column in '{path.name}'. Expected one of "
            f"{sorted(_LABEL_COLUMN_ALIASES)} (case-insensitive). See data/raw/README.md."
        )
    if cols["text"] is None and cols["title"] is None:
        raise DataValidationError(
            f"Could not find a title or text column in '{path.name}'. Expected one of "
            f"{sorted(_TITLE_COLUMN_ALIASES | _TEXT_COLUMN_ALIASES)}. See data/raw/README.md."
        )

    out = pd.DataFrame()
    out["title"] = df[cols["title"]] if cols["title"] else ""
    out["text"] = df[cols["text"]] if cols["text"] else ""
    out["label"] = df[cols["label"]].map(_coerce_label)
    return out


def _load_fake_true_dataset(fake_path: Path, true_path: Path) -> pd.DataFrame:
    fake_df = _read_table(fake_path)
    true_df = _read_table(true_path)

    fake_cols = detect_columns(fake_df)
    true_cols = detect_columns(true_df)

    if fake_cols["title"] is None and fake_cols["text"] is None:
        raise DataValidationError(f"Could not find a title or text column in '{fake_path.name}'.")
    if true_cols["title"] is None and true_cols["text"] is None:
        raise DataValidationError(f"Could not find a title or text column in '{true_path.name}'.")

    def _standardize(df: pd.DataFrame, cols: dict, label: int) -> pd.DataFrame:
        out = pd.DataFrame()
        out["title"] = df[cols["title"]] if cols["title"] else ""
        out["text"] = df[cols["text"]] if cols["text"] else ""
        out["label"] = label
        return out

    fake_std = _standardize(fake_df, fake_cols, label=1)
    true_std = _standardize(true_df, true_cols, label=0)
    return pd.concat([fake_std, true_std], ignore_index=True)


def _find_raw_files(raw_dir: Path) -> dict:
    """Detect which of the supported raw layouts is present in raw_dir."""
    all_tables = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.tsv"))

    fake_path = next((p for p in all_tables if p.stem.lower() == "fake"), None)
    true_path = next((p for p in all_tables if p.stem.lower() == "true"), None)
    if fake_path and true_path:
        return {"mode": "fake_true", "fake": fake_path, "true": true_path}

    single_candidates = [p for p in all_tables if p.stem.lower() not in {"fake", "true"}]
    if single_candidates:
        return {"mode": "single", "files": sorted(single_candidates)}

    return {"mode": "none"}


def load_raw_dataset(raw_dir: Path | None = None, config: Config = default_config) -> pd.DataFrame:
    """Load the raw dataset, auto-detecting the layout in raw_dir (defaults
    to config.raw_data_dir). Raises DataValidationError with an actionable
    message if no usable file is found or the schema can't be normalized."""
    raw_dir = Path(raw_dir) if raw_dir else config.raw_data_dir
    if not raw_dir.exists():
        raise DataValidationError(
            f"Raw data directory not found: {raw_dir}. Create it and add your dataset "
            f"(see data/raw/README.md)."
        )

    layout = _find_raw_files(raw_dir)
    if layout["mode"] == "fake_true":
        logger.info("Detected Fake.csv / True.csv layout in %s", raw_dir)
        return _load_fake_true_dataset(layout["fake"], layout["true"])
    if layout["mode"] == "single":
        frames = []
        for path in layout["files"]:
            logger.info("Loading single-file dataset: %s", path.name)
            frames.append(_load_single_file_dataset(path))
        return pd.concat(frames, ignore_index=True)

    raise DataValidationError(
        f"No usable CSV/TSV files found in {raw_dir}. Place either 'Fake.csv' + "
        f"'True.csv', or a CSV with title/text/label columns, in this directory. "
        f"See data/raw/README.md for details."
    )


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values, remove empty/duplicate records, and log the
    resulting class distribution. This is where DATA LEAKAGE guarantees
    around duplicates are enforced: dedup happens here, once, before any
    train/val/test split, so the same article can never land in two splits.
    """
    n_start = len(df)
    df = df.copy()

    df["title"] = df["title"].fillna("").astype(str)
    df["text"] = df["text"].fillna("").astype(str)

    n_missing_label = int(df["label"].isna().sum())
    df = df[df["label"].notna()].copy()
    df["label"] = df["label"].astype(int)

    df["content"] = [combine_title_text(t, x) for t, x in zip(df["title"], df["text"])]

    n_before_empty = len(df)
    df = df[df["content"].str.strip().str.len() > 0]
    n_empty_removed = n_before_empty - len(df)

    n_before_dup = len(df)
    df = df.drop_duplicates(subset=["content"], keep="first")
    n_duplicates_removed = n_before_dup - len(df)

    df = df.reset_index(drop=True)

    logger.info(
        "Dataset cleaned: start=%d, dropped_missing_label=%d, dropped_empty=%d, "
        "dropped_duplicates=%d, final=%d",
        n_start,
        n_missing_label,
        n_empty_removed,
        n_duplicates_removed,
        len(df),
    )

    if df.empty:
        raise DataValidationError(
            "Dataset is empty after cleaning. Check that the raw file(s) actually "
            "contain readable title/text and label values (see data/raw/README.md)."
        )

    distribution = df["label"].value_counts().to_dict()
    readable = {default_config.label_map.get(k, k): v for k, v in distribution.items()}
    logger.info("Class distribution: %s", readable)

    return df


def add_engineered_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add `clean_text` (for TF-IDF) and the stylistic numeric feature
    columns (computed from the raw `content`, before cleaning strips
    punctuation/case) — the exact same functions predict.py calls at
    inference time, so training and serving stay in sync."""
    df = df.copy()
    cleaner = build_default_cleaner()

    df["clean_text"] = df["content"].apply(cleaner.clean)

    numeric_records = df["content"].apply(extract_stylistic_features)
    numeric_df = pd.DataFrame(list(numeric_records), index=df.index)
    df = pd.concat([df, numeric_df], axis=1)

    n_empty_clean = int((df["clean_text"].str.len() == 0).sum())
    if n_empty_clean:
        logger.warning(
            "%d record(s) became empty after text cleaning (e.g. content was "
            "only stopwords/punctuation). They are kept so numeric-only signal "
            "can still be used, but contribute no TF-IDF terms.",
            n_empty_clean,
        )
    return df


def load_and_prepare_dataset(raw_dir: Path | None = None, config: Config = default_config) -> pd.DataFrame:
    """Full pipeline: load raw -> clean -> engineer columns. This is the
    single entry point src/models/train.py calls."""
    df = load_raw_dataset(raw_dir=raw_dir, config=config)
    df = clean_dataset(df)
    df = add_engineered_columns(df)
    return df
