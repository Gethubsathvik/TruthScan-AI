#!/usr/bin/env python3
"""
CLI entry point for a single prediction.

Usage:
    python predict.py --text "Your news article here"
    python predict.py --title "Some headline" --text "Full article body..."
    python predict.py --file article.txt
    python predict.py --text "..." --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.models.predict import EmptyInputError, ModelNotFoundError, PredictionService
from src.utils.config import config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify a headline/article as REAL or FAKE.")
    parser.add_argument("--title", type=str, default="", help="News headline.")
    parser.add_argument("--text", type=str, default="", help="Article body text.")
    parser.add_argument("--file", type=str, default=None, help="Read the article body from a text file.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a formatted summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    text = args.text
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"[ERROR] File not found: {path}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8", errors="ignore")

    try:
        service = PredictionService(config=config)
    except ModelNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    try:
        result = service.predict(title=args.title, text=text)
    except EmptyInputError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print(f"\nPrediction:       {result.prediction}")
    score_label = "Calibrated probability" if result.is_calibrated_probability else "Model score (uncalibrated)"
    conf_str = f"{result.confidence:.1%}" if result.confidence is not None else "N/A"
    print(f"{score_label}: {conf_str}")
    print(f"Confidence level: {result.confidence_level}")
    print(f"Model used:       {result.model_name}")
    if result.top_features:
        print("\nTop influencing features:")
        for feat in result.top_features:
            print(f"  [{feat.direction:>4}] {feat.feature:<25} weight={feat.weight:+.3f}")
    print(f"\n{result.disclaimer}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
