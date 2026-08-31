"""
Small text utilities shared between training-time data loading and
inference-time prediction. This is what prevents train/serve skew: both
src/data/loader.py (training) and src/models/predict.py (inference) call
this exact function rather than each re-implementing "combine headline and
body" slightly differently.
"""
from __future__ import annotations


def combine_title_text(title: str | None, text: str | None) -> str:
    """Combine a headline and article body into one string.

    Handles all three supported input modes: headline only, article only,
    or headline + article. Always returns a stripped string ("" if both
    inputs are empty/whitespace).
    """
    title = (title or "").strip()
    text = (text or "").strip()
    if title and text:
        return f"{title}. {text}"
    return title or text
