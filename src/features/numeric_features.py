"""
Stylistic / numeric features computed directly from the *raw* combined
headline + article text — before the NLP cleaning pipeline lowercases text
and strips punctuation.

Signals such as ALL-CAPS ratio, exclamation-mark density, and punctuation
counts often differ between sensationalized and neutral reporting, so they
are captured here and fused with the TF-IDF representation rather than being
permanently discarded during cleaning (see PREPROCESSING requirements).
"""
from __future__ import annotations

import re

_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+(?:\s|$)")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_PUNCTUATION_RE = re.compile(r"[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~]")

NUMERIC_FEATURE_NAMES: list[str] = [
    "word_count",
    "char_count",
    "sentence_count",
    "avg_word_length",
    "uppercase_ratio",
    "punctuation_count",
    "url_count",
    "exclamation_count",
    "question_count",
]


def extract_stylistic_features(raw_text: str) -> dict[str, float]:
    """Compute stylistic/numeric features from a raw (uncleaned) string.

    Always returns every key in NUMERIC_FEATURE_NAMES (defaulting to 0.0 for
    empty input) so downstream code never has to special-case a missing
    feature — this fixed schema is also what src/features/tfidf_features.py
    relies on to build a consistent feature-matrix column order.
    """
    text = raw_text or ""
    if not text.strip():
        return {name: 0.0 for name in NUMERIC_FEATURE_NAMES}

    words = text.split()
    word_count = len(words)
    char_count = len(text)

    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    sentence_count = max(len(sentences), 1)

    avg_word_length = (sum(len(w) for w in words) / word_count) if word_count else 0.0

    letters = [c for c in text if c.isalpha()]
    uppercase_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if letters else 0.0

    punctuation_count = len(_PUNCTUATION_RE.findall(text))
    url_count = len(_URL_RE.findall(text))
    exclamation_count = text.count("!")
    question_count = text.count("?")

    return {
        "word_count": float(word_count),
        "char_count": float(char_count),
        "sentence_count": float(sentence_count),
        "avg_word_length": round(avg_word_length, 4),
        "uppercase_ratio": round(uppercase_ratio, 4),
        "punctuation_count": float(punctuation_count),
        "url_count": float(url_count),
        "exclamation_count": float(exclamation_count),
        "question_count": float(question_count),
    }
