"""
OPTIONAL transformer (DistilBERT) fine-tuning pipeline.

This is entirely separate from, and not required by, the classical ML
pipeline (src/models/train.py / src/models/predict.py) — the base
application works fully without PyTorch or transformers installed. This
module is only imported by the optional `train_transformer.py` script.

Pipeline: raw text -> DistilBertTokenizerFast -> DistilBertForSequenceClassification
-> 2-class head -> REAL / FAKE, fine-tuned with early stopping on validation
F1, using the SAME train/val/test split logic as the classical pipeline
(src/models/train.split_dataset) so the two approaches are compared fairly
on identical data.

Requires: pip install -r requirements-transformer.txt (torch, transformers,
datasets). Fine-tuning a transformer needs meaningfully more compute than
the classical models — a GPU is strongly recommended, and an environment
with internet access to download the pretrained DistilBERT weights on
first run (e.g. Google Colab).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import numpy as np
    import torch
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    from torch.utils.data import DataLoader, Dataset
    from transformers import (
        DistilBertForSequenceClassification,
        DistilBertTokenizerFast,
        get_linear_schedule_with_warmup,
    )

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


DEFAULT_CHECKPOINT = "distilbert-base-uncased"


def _require_transformers() -> None:
    if not TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "PyTorch and/or transformers are not installed. Install the optional "
            "transformer dependencies with:\n"
            "    pip install -r requirements-transformer.txt\n"
            "The rest of this application (classical ML, Streamlit, API) works "
            "fully without them."
        )


if TRANSFORMERS_AVAILABLE:

    class FakeNewsDataset(Dataset):
        """Wraps pre-tokenized encodings + labels for use with DataLoader."""

        def __init__(self, encodings: dict, labels: list[int]):
            self.encodings = encodings
            self.labels = labels

        def __len__(self) -> int:
            return len(self.labels)

        def __getitem__(self, idx: int) -> dict:
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item


@dataclass
class TransformerTrainingResult:
    checkpoint: str
    best_epoch: int
    best_val_f1: float
    test_metrics: dict
    model_dir: Path


def _tokenize_split(tokenizer, texts: list[str], max_length: int = 256) -> dict:
    return tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors=None,
    )


def _evaluate(model, loader, device) -> dict:
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0.0
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            total_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
            all_preds.extend(preds.tolist())
            all_labels.extend(batch["labels"].cpu().numpy().tolist())

    return {
        "loss": total_loss / max(len(loader), 1),
        "accuracy": float(accuracy_score(all_labels, all_preds)),
        "precision": float(precision_score(all_labels, all_preds, zero_division=0)),
        "recall": float(recall_score(all_labels, all_preds, zero_division=0)),
        "f1": float(f1_score(all_labels, all_preds, zero_division=0)),
    }


def train_transformer(
    config: Config,
    raw_dir: Path | None = None,
    checkpoint: str = DEFAULT_CHECKPOINT,
    epochs: int = 4,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 256,
    early_stopping_patience: int = 2,
    output_dir: Path | None = None,
) -> TransformerTrainingResult:
    """Fine-tune DistilBERT for REAL/FAKE classification with early
    stopping on validation F1. Uses the same load/split logic as the
    classical pipeline so results are directly comparable."""
    _require_transformers()

    from src.data.loader import load_and_prepare_dataset
    from src.models.train import split_dataset

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Transformer training on device: %s", device)

    df = load_and_prepare_dataset(raw_dir=raw_dir, config=config)
    # The transformer reads its own text directly (it does its own
    # subword tokenization), so it uses `content` (raw combined text)
    # rather than the classical pipeline's cleaned/stopword-stripped
    # `clean_text` — stripping stopwords/punctuation would only remove
    # information a transformer can otherwise use.
    train_df, val_df, test_df = split_dataset(df, config)

    tokenizer = DistilBertTokenizerFast.from_pretrained(checkpoint)
    model = DistilBertForSequenceClassification.from_pretrained(checkpoint, num_labels=2).to(device)

    train_ds = FakeNewsDataset(
        _tokenize_split(tokenizer, train_df["content"].tolist(), max_length), train_df["label"].tolist()
    )
    val_ds = FakeNewsDataset(
        _tokenize_split(tokenizer, val_df["content"].tolist(), max_length), val_df["label"].tolist()
    )
    test_ds = FakeNewsDataset(
        _tokenize_split(tokenizer, test_df["content"].tolist(), max_length), test_df["label"].tolist()
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)

    output_dir = Path(output_dir) if output_dir else config.model_dir / "transformer"
    output_dir.mkdir(parents=True, exist_ok=True)

    best_val_f1 = -1.0
    best_epoch = -1
    epochs_without_improvement = 0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            running_loss += loss.item()

        val_metrics = _evaluate(model, val_loader, device)
        logger.info(
            "Epoch %d/%d: train_loss=%.4f val_loss=%.4f val_f1=%.4f val_acc=%.4f",
            epoch,
            epochs,
            running_loss / max(len(train_loader), 1),
            val_metrics["loss"],
            val_metrics["f1"],
            val_metrics["accuracy"],
        )

        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_epoch = epoch
            epochs_without_improvement = 0
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
            logger.info("New best model (val_f1=%.4f) saved to %s", best_val_f1, output_dir)
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= early_stopping_patience:
                logger.info("Early stopping at epoch %d (no improvement for %d epochs).", epoch, early_stopping_patience)
                break

    # Reload the best checkpoint (not necessarily the last epoch) before
    # the final, single test-set evaluation.
    best_model = DistilBertForSequenceClassification.from_pretrained(output_dir).to(device)
    test_metrics = _evaluate(best_model, test_loader, device)
    logger.info("TEST metrics (best checkpoint, epoch %d): %s", best_epoch, test_metrics)

    import json

    with open(output_dir / "transformer_metadata.json", "w") as f:
        json.dump(
            {
                "checkpoint": checkpoint,
                "best_epoch": best_epoch,
                "best_val_f1": best_val_f1,
                "test_metrics": {k: v for k, v in test_metrics.items() if k != "loss"},
                "max_length": max_length,
            },
            f,
            indent=2,
        )

    return TransformerTrainingResult(
        checkpoint=checkpoint,
        best_epoch=best_epoch,
        best_val_f1=best_val_f1,
        test_metrics=test_metrics,
        model_dir=output_dir,
    )


def predict_transformer(text: str, model_dir: Path, max_length: int = 256) -> dict:
    """Run inference with a fine-tuned transformer checkpoint saved by
    `train_transformer`. Returns the same REAL/FAKE + confidence shape as
    the classical PredictionResult.to_dict(), for easy comparison."""
    _require_transformers()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = DistilBertTokenizerFast.from_pretrained(model_dir)
    model = DistilBertForSequenceClassification.from_pretrained(model_dir).to(device)
    model.eval()

    encoded = tokenizer(text, truncation=True, padding="max_length", max_length=max_length, return_tensors="pt")
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        logits = model(**encoded).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

    pred_label = int(np.argmax(probs))
    label_map = {0: "REAL", 1: "FAKE"}
    return {
        "prediction": label_map[pred_label],
        "confidence": round(float(probs[pred_label]), 4),
        "is_calibrated_probability": True,
        "model": "DistilBERT (fine-tuned)",
    }
