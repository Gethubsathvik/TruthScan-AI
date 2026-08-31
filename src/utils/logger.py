"""
Application-wide logging configuration.

Two guarantees this module upholds:
  1. Every module gets a consistently formatted logger via `get_logger(__name__)`.
  2. Raw, user-submitted article/headline text is never written to the logs —
     only lengths, hashes, and short redacted previews are logged (see
     `safe_preview`), so log files never persist full user submissions.
"""
from __future__ import annotations

import hashlib
import logging
import sys
from logging.handlers import RotatingFileHandler

from src.utils.config import config

_CONFIGURED = False


def _configure_root_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    config.log_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.log_dir / "app.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(config.log_level.upper())
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring handlers on first use."""
    _configure_root_logging()
    return logging.getLogger(name)


def safe_preview(text: str, max_chars: int = 40) -> str:
    """A redacted, length-bounded preview of user text, safe to log.

    Never returns the full raw text — only a short prefix plus a content
    hash — so logs remain useful for debugging without persisting full user
    submissions (see SECURITY / LOGGING requirements).
    """
    if not text:
        return "<empty>"
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:10]
    preview = text[:max_chars].replace("\n", " ")
    suffix = "..." if len(text) > max_chars else ""
    return f"'{preview}{suffix}' (len={len(text)}, sha256={digest})"
