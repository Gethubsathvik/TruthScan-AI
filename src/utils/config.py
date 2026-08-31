"""
Centralized configuration for the Fake News Detection System.

Every path, split ratio, hyperparameter default, and threshold used
anywhere in this project is defined here and can be overridden via
environment variables (see .env.example). No other module should
hard-code a path or a "magic number" — import `config` from here instead.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is a convenience, not a hard requirement — if it isn't
    # installed we simply fall back to whatever is already in os.environ.
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    val = os.getenv(name)
    return Path(val) if val else default


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val not in (None, "") else default


def _env_float(name: str, default: float) -> float:
    val = os.getenv(name)
    return float(val) if val not in (None, "") else default


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_ngram_range(name: str, default: tuple[int, int]) -> tuple[int, int]:
    val = os.getenv(name)
    if not val:
        return default
    try:
        lo, hi = (int(p.strip()) for p in val.split(","))
        return lo, hi
    except (ValueError, TypeError):
        return default


@dataclass(frozen=True)
class Config:
    """Immutable application configuration.

    Paths default to environment-variable overrides of sensible
    project-relative locations. Every other module receives its Config
    either via the module-level `config` singleton below, or (in tests) via
    an explicitly constructed instance pointed at a temp directory — this is
    what lets the test suite run without touching the real data/models
    directories.
    """

    # ---- Paths -----------------------------------------------------
    project_root: Path = PROJECT_ROOT
    raw_data_dir: Path = field(default_factory=lambda: _env_path("RAW_DATA_DIR", PROJECT_ROOT / "data" / "raw"))
    processed_data_dir: Path = field(
        default_factory=lambda: _env_path("PROCESSED_DATA_DIR", PROJECT_ROOT / "data" / "processed")
    )
    sample_data_dir: Path = field(
        default_factory=lambda: _env_path("SAMPLE_DATA_DIR", PROJECT_ROOT / "data" / "sample")
    )
    model_dir: Path = field(default_factory=lambda: _env_path("MODEL_DIR", PROJECT_ROOT / "models"))
    reports_dir: Path = field(default_factory=lambda: _env_path("REPORTS_DIR", PROJECT_ROOT / "reports"))
    figures_dir: Path = field(
        default_factory=lambda: _env_path("FIGURES_DIR", PROJECT_ROOT / "reports" / "figures")
    )
    metrics_dir: Path = field(
        default_factory=lambda: _env_path("METRICS_DIR", PROJECT_ROOT / "reports" / "metrics")
    )
    log_dir: Path = field(default_factory=lambda: _env_path("LOG_DIR", PROJECT_ROOT / "logs"))

    # ---- Train / val / test split -----------------------------------
    test_size: float = field(default_factory=lambda: _env_float("TEST_SIZE", 0.15))
    validation_size: float = field(default_factory=lambda: _env_float("VALIDATION_SIZE", 0.15))
    random_state: int = field(default_factory=lambda: _env_int("RANDOM_STATE", 42))

    # ---- TF-IDF -------------------------------------------------------
    max_features: int = field(default_factory=lambda: _env_int("MAX_FEATURES", 20000))
    ngram_range: tuple[int, int] = field(default_factory=lambda: _env_ngram_range("NGRAM_RANGE", (1, 2)))
    min_df: int = field(default_factory=lambda: _env_int("MIN_DF", 2))
    max_df: float = field(default_factory=lambda: _env_float("MAX_DF", 0.95))
    sublinear_tf: bool = field(default_factory=lambda: _env_bool("SUBLINEAR_TF", True))
    strip_accents: str = field(default_factory=lambda: _env_str("STRIP_ACCENTS", "unicode"))

    # ---- Preprocessing --------------------------------------------------
    use_lemmatization: bool = field(default_factory=lambda: _env_bool("USE_LEMMATIZATION", True))
    remove_stopwords: bool = field(default_factory=lambda: _env_bool("REMOVE_STOPWORDS", True))
    max_input_chars: int = field(default_factory=lambda: _env_int("MAX_INPUT_CHARS", 50000))

    # ---- Confidence bucketing --------------------------------------------
    high_confidence_threshold: float = field(
        default_factory=lambda: _env_float("HIGH_CONFIDENCE_THRESHOLD", 0.85)
    )
    medium_confidence_threshold: float = field(
        default_factory=lambda: _env_float("MEDIUM_CONFIDENCE_THRESHOLD", 0.65)
    )

    # ---- Hyperparameter tuning --------------------------------------------
    enable_tuning: bool = field(default_factory=lambda: _env_bool("ENABLE_TUNING", True))
    cv_folds: int = field(default_factory=lambda: _env_int("CV_FOLDS", 5))
    tuning_search_type: str = field(default_factory=lambda: _env_str("TUNING_SEARCH_TYPE", "grid"))
    random_search_iterations: int = field(default_factory=lambda: _env_int("RANDOM_SEARCH_ITERATIONS", 20))

    # ---- Labels — single source of truth used everywhere -------------------
    label_map: dict = field(default_factory=lambda: {0: "REAL", 1: "FAKE"})
    inverse_label_map: dict = field(default_factory=lambda: {"REAL": 0, "FAKE": 1})

    # ---- Logging / serving ------------------------------------------------
    log_level: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))
    api_host: str = field(default_factory=lambda: _env_str("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: _env_int("API_PORT", 8000))

    # ---- Derived model artifact paths (always in sync with model_dir) -----
    @property
    def model_path(self) -> Path:
        return self.model_dir / "best_model.joblib"

    @property
    def vectorizer_path(self) -> Path:
        return self.model_dir / "tfidf_vectorizer.joblib"

    @property
    def scaler_path(self) -> Path:
        return self.model_dir / "numeric_scaler.joblib"

    @property
    def metadata_path(self) -> Path:
        return self.model_dir / "metadata.json"

    @property
    def error_analysis_path(self) -> Path:
        return self.reports_dir / "error_analysis.csv"

    def ensure_directories(self) -> None:
        """Create every directory this project writes to, if missing."""
        for directory in (
            self.raw_data_dir,
            self.processed_data_dir,
            self.sample_data_dir,
            self.model_dir,
            self.reports_dir,
            self.figures_dir,
            self.metrics_dir,
            self.log_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


config = Config()
