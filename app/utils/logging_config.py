"""Rotating file + console logging setup."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.config import LOG_LEVEL, LOGS_DIR


def configure_logging() -> None:
    root = logging.getLogger("real_estate")
    if root.handlers:
        return  # already configured (e.g. reload)

    root.setLevel(LOG_LEVEL)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    app_log = RotatingFileHandler(LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=3)
    app_log.setFormatter(fmt)
    root.addHandler(app_log)

    error_log = RotatingFileHandler(LOGS_DIR / "errors.log", maxBytes=2_000_000, backupCount=3)
    error_log.setLevel(logging.ERROR)
    error_log.setFormatter(fmt)
    root.addHandler(error_log)

    # Quiet down noisy third-party loggers a little
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
