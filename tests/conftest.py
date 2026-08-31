"""
Shared pytest fixtures.

`temp_config` points an entire Config at a scratch tmp_path with a tiny,
fully-synthetic CSV already written to its raw_data_dir — every test in this
suite runs against this, never against the real data/ or models/
directories, so the suite is safe to run repeatedly and never depends on the
real dataset being present.

`trained_service_config` additionally runs the *real* training pipeline
against that synthetic dataset, so prediction/API tests exercise genuine
trained artifacts rather than mocks.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils.config import Config

# Unique-by-construction synthetic examples (topic-templated so every row is
# a distinct string — duplicate rows would be legitimately removed by
# src/data/loader.py's dedup step, which is exactly what we want to test
# elsewhere, just not accidentally trigger here).
_FAKE_TOPICS = [
    "vaccines", "the election", "the economy", "aliens", "the moon landing",
    "5G towers", "the water supply", "celebrities", "the president", "banks",
    "the stock market", "climate scientists", "big tech", "the military",
    "hospitals", "schools", "the internet", "your phone", "social media", "the government",
]
_REAL_TOPICS = [
    "the annual budget", "quarterly earnings", "rainfall patterns", "the bus schedule",
    "the bridge repair project", "interest rates", "the library branch", "vaccination rates",
    "renewable energy research", "the school curriculum", "local elections", "the water treatment plant",
    "public transit funding", "the census report", "a new zoning proposal", "the county fair",
    "highway maintenance", "the parks department budget", "a university grant", "the housing survey",
]


def _build_synthetic_rows() -> list[dict]:
    fake_rows = [
        {
            "title": "",
            "text": f"SHOCKING!!! You won't believe what they don't want you to know about {t}!!! Share before it's DELETED",
            "label": "FAKE",
        }
        for t in _FAKE_TOPICS
    ] + [
        {
            "title": "",
            "text": f"BREAKING: anonymous insider leaks secret documents exposing {t}, mainstream media stays silent",
            "label": "FAKE",
        }
        for t in _FAKE_TOPICS
    ]
    real_rows = [
        {
            "title": "",
            "text": f"City officials released an update on {t} following Tuesday's public session.",
            "label": "REAL",
        }
        for t in _REAL_TOPICS
    ] + [
        {
            "title": "",
            "text": f"A new report on {t} was published this week by the regional planning office.",
            "label": "REAL",
        }
        for t in _REAL_TOPICS
    ]
    return fake_rows + real_rows


@pytest.fixture(scope="session")
def synthetic_dataset() -> pd.DataFrame:
    return pd.DataFrame(_build_synthetic_rows())


@pytest.fixture()
def temp_config(tmp_path: Path, synthetic_dataset: pd.DataFrame) -> Config:
    """A Config pointed entirely at a scratch tmp_path, with the synthetic
    dataset already written to its raw_data_dir. Split/TF-IDF settings are
    loosened (min_df=1 etc.) so they behave sensibly on such a small corpus."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    synthetic_dataset.to_csv(raw_dir / "sample.csv", index=False)

    cfg = Config(
        raw_data_dir=raw_dir,
        processed_data_dir=tmp_path / "data" / "processed",
        sample_data_dir=tmp_path / "data" / "sample",
        model_dir=tmp_path / "models",
        reports_dir=tmp_path / "reports",
        figures_dir=tmp_path / "reports" / "figures",
        metrics_dir=tmp_path / "reports" / "metrics",
        log_dir=tmp_path / "logs",
        test_size=0.2,
        validation_size=0.2,
        min_df=1,
        max_df=1.0,
        cv_folds=2,
        enable_tuning=False,  # keep the fixture fast; tuning itself is exercised elsewhere
    )
    cfg.ensure_directories()
    return cfg


@pytest.fixture()
def trained_service_config(temp_config: Config) -> Config:
    """Runs the real training pipeline against the tiny synthetic dataset
    and returns the Config pointing at the resulting artifacts."""
    from src.models.train import run_training_pipeline

    run_training_pipeline(config=temp_config, quick=True, tune=False)
    return temp_config
