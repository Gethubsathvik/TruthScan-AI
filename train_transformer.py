#!/usr/bin/env python3
"""
OPTIONAL: fine-tune a DistilBERT transformer as an alternative to the
classical ML models, and compare it against them.

This is a separate, optional track — `python train.py` (classical ML) does
not require this, and does not require PyTorch/transformers to be
installed. Only run this script after installing the extra dependencies:

    pip install -r requirements-transformer.txt

A GPU and internet access (to download the pretrained DistilBERT weights on
first run) are strongly recommended — e.g. run this in Google Colab.

Usage:
    python train_transformer.py
    python train_transformer.py --epochs 3 --batch-size 16
    python train_transformer.py --data-dir data/sample
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.data.loader import DataValidationError
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT for fake news detection.")
    parser.add_argument("--data-dir", type=str, default=None, help="Override the raw data directory.")
    parser.add_argument("--checkpoint", type=str, default="distilbert-base-uncased")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--patience", type=int, default=2, help="Early stopping patience (epochs).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        from src.models.transformer_model import TRANSFORMERS_AVAILABLE, train_transformer
    except ImportError:
        print(
            "[ERROR] Could not import the transformer module. Install extra "
            "dependencies first:\n    pip install -r requirements-transformer.txt",
            file=sys.stderr,
        )
        return 1

    if not TRANSFORMERS_AVAILABLE:
        print(
            "[ERROR] PyTorch/transformers are not installed. Install them with:\n"
            "    pip install -r requirements-transformer.txt",
            file=sys.stderr,
        )
        return 1

    raw_dir = Path(args.data_dir) if args.data_dir else None

    try:
        result = train_transformer(
            config=config,
            raw_dir=raw_dir,
            checkpoint=args.checkpoint,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            early_stopping_patience=args.patience,
        )
    except DataValidationError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        return 1

    print("\n=== Transformer training complete ===")
    print(f"Checkpoint:        {result.checkpoint}")
    print(f"Best epoch:        {result.best_epoch}")
    print(f"Best val F1:       {result.best_val_f1:.4f}")
    print(f"Test metrics:      {json.dumps(result.test_metrics, indent=2)}")
    print(f"\nSaved to: {result.model_dir}")
    print(
        "\nCompare against models/metadata.json (classical ML) to see which "
        "approach performed better on your dataset."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
