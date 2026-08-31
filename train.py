#!/usr/bin/env python3
"""
CLI entry point for training.

Usage:
    python train.py
    python train.py --data-dir data/sample --quick
    python train.py --no-tune
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.data.loader import DataValidationError
from src.models.train import run_training_pipeline
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the fake news detection models.")
    parser.add_argument(
        "--data-dir", type=str, default=None, help="Override the raw data directory (default: data/raw)."
    )
    parser.add_argument(
        "--quick", action="store_true", help="Use smaller hyperparameter grids for a fast smoke run."
    )
    parser.add_argument("--no-tune", action="store_true", help="Skip hyperparameter tuning entirely.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.data_dir) if args.data_dir else None
    tune = False if args.no_tune else None

    try:
        result = run_training_pipeline(config=config, raw_dir=raw_dir, quick=args.quick, tune=tune)
    except DataValidationError as exc:
        logger.error("Training aborted: %s", exc)
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        return 1

    print("\n=== Training complete ===")
    print(f"Best model:      {result.best_model_name}")
    print(f"Validation F1:   {result.val_metrics['f1']:.4f}")
    print(f"Validation Acc:  {result.val_metrics['accuracy']:.4f}")
    print(f"Test F1:         {result.test_metrics['f1']:.4f}")
    print(f"Test Accuracy:   {result.test_metrics['accuracy']:.4f}")
    if result.test_metrics.get("roc_auc") is not None:
        print(f"Test ROC-AUC:    {result.test_metrics['roc_auc']:.4f}")
    print(f"\nArtifacts saved under: {config.model_dir}")
    print(f"Reports saved under:   {config.reports_dir}")
    print("\nTry it now:  python predict.py --text \"Your news article here\"")
    print("Or the UI:   streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
