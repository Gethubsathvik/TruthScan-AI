"""Tests for src/data/loader.py."""
from __future__ import annotations

import pandas as pd
import pytest

from src.data.loader import DataValidationError, clean_dataset, load_raw_dataset


def _make_single_file_dataset(tmp_path, filename="news.csv"):
    df = pd.DataFrame(
        {
            "Title": ["Headline A", "Headline B", "Headline C", "Headline D"],
            "Text": ["Body text A is here.", "Body text B is here.", "Body text C.", "Body text D."],
            "Label": ["FAKE", "REAL", "fake", "real"],
        }
    )
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    df.to_csv(raw_dir / filename, index=False)
    return raw_dir


def _make_fake_true_dataset(tmp_path):
    fake_df = pd.DataFrame({"title": ["F1", "F2"], "text": ["Fake body one.", "Fake body two."]})
    true_df = pd.DataFrame({"title": ["T1", "T2"], "text": ["Real body one.", "Real body two."]})
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    fake_df.to_csv(raw_dir / "Fake.csv", index=False)
    true_df.to_csv(raw_dir / "True.csv", index=False)
    return raw_dir


def test_load_single_file_layout_detects_columns_and_labels(tmp_path):
    raw_dir = _make_single_file_dataset(tmp_path)
    df = load_raw_dataset(raw_dir=raw_dir)
    assert set(df["label"].unique()) <= {0, 1}
    assert len(df) == 4


def test_load_fake_true_layout(tmp_path):
    raw_dir = _make_fake_true_dataset(tmp_path)
    df = load_raw_dataset(raw_dir=raw_dir)
    assert len(df) == 4
    assert (df["label"] == 1).sum() == 2  # Fake.csv rows
    assert (df["label"] == 0).sum() == 2  # True.csv rows


def test_load_raw_dataset_missing_directory_raises(tmp_path):
    with pytest.raises(DataValidationError):
        load_raw_dataset(raw_dir=tmp_path / "does_not_exist")


def test_load_raw_dataset_empty_directory_raises(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    with pytest.raises(DataValidationError):
        load_raw_dataset(raw_dir=raw_dir)


def test_load_single_file_dataset_unrecognizable_columns_raises(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    pd.DataFrame({"foo": [1, 2], "bar": [3, 4]}).to_csv(raw_dir / "weird.csv", index=False)
    with pytest.raises(DataValidationError):
        load_raw_dataset(raw_dir=raw_dir)


def test_clean_dataset_drops_missing_labels_empty_and_duplicates():
    df = pd.DataFrame(
        {
            "title": ["A", "A", "B", "", "D"],
            "text": ["same content", "same content", "unique content", "   ", "more content"],
            "label": [1, 1, 0, 1, None],
        }
    )
    cleaned = clean_dataset(df)
    # Row 0 & 1 are exact duplicates -> collapse to 1
    # Row 3 has empty title AND empty text -> dropped as an empty record
    # Row 4 has a missing label -> dropped
    # Row 2 (B) survives untouched
    assert len(cleaned) == 2


def test_clean_dataset_raises_when_everything_is_dropped():
    df = pd.DataFrame({"title": ["", ""], "text": ["", ""], "label": [1, 0]})
    with pytest.raises(DataValidationError):
        clean_dataset(df)
