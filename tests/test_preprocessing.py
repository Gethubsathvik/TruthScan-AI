"""Tests for src/preprocessing/text_cleaner.py and src/features/numeric_features.py."""
from __future__ import annotations

from src.features.numeric_features import NUMERIC_FEATURE_NAMES, extract_stylistic_features
from src.preprocessing.text_cleaner import TextCleaner, TextCleanerConfig
from src.utils.text_utils import combine_title_text


def test_clean_removes_html_and_urls():
    cleaner = TextCleaner(TextCleanerConfig())
    result = cleaner.clean("<b>Breaking</b> news at http://example.com/story now!")
    assert "http" not in result
    assert "<b>" not in result
    assert "breaking" in result


def test_clean_removes_emails():
    cleaner = TextCleaner(TextCleanerConfig())
    result = cleaner.clean("Contact tips@example.com for more information.")
    assert "@" not in result


def test_clean_is_lowercased():
    cleaner = TextCleaner(TextCleanerConfig())
    result = cleaner.clean("SHOCKING Breaking NEWS")
    assert result == result.lower()


def test_clean_handles_empty_and_none_input():
    cleaner = TextCleaner(TextCleanerConfig())
    assert cleaner.clean("") == ""
    assert cleaner.clean(None) == ""  # type: ignore[arg-type]


def test_clean_removes_stopwords_when_enabled():
    cleaner = TextCleaner(TextCleanerConfig(remove_stopwords_flag=True))
    result = cleaner.clean("this is a test of the system")
    tokens = result.split()
    assert "is" not in tokens
    assert "the" not in tokens
    assert "test" in tokens


def test_clean_keeps_stopwords_when_disabled():
    cleaner = TextCleaner(TextCleanerConfig(remove_stopwords_flag=False))
    result = cleaner.clean("this is a test")
    assert "is" in result.split()


def test_numeric_features_returns_all_keys_for_empty_input():
    feats = extract_stylistic_features("")
    assert set(feats.keys()) == set(NUMERIC_FEATURE_NAMES)
    assert all(v == 0.0 for v in feats.values())


def test_numeric_features_handles_none():
    feats = extract_stylistic_features(None)  # type: ignore[arg-type]
    assert set(feats.keys()) == set(NUMERIC_FEATURE_NAMES)


def test_numeric_features_counts_signals_correctly():
    feats = extract_stylistic_features("WOW!!! Is this real? Yes!!")
    assert feats["exclamation_count"] == 5
    assert feats["question_count"] == 1
    assert feats["uppercase_ratio"] > 0
    assert feats["word_count"] == 5


def test_combine_title_text_variants():
    assert combine_title_text("Title", "Body") == "Title. Body"
    assert combine_title_text("Title", "") == "Title"
    assert combine_title_text("", "Body") == "Body"
    assert combine_title_text("", "") == ""
    assert combine_title_text(None, None) == ""
    assert combine_title_text("  ", "  ") == ""
