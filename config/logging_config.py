"""Utilidades de logging para FileMaster."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config.settings import LOG_FILE_PATH, ensure_data_files


def setup_logging(level: int = logging.INFO) -> None:
    ensure_data_files()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1_048_576, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[file_handler, stream_handler],
        force=True,
    )
