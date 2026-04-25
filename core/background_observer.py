"""Modo observador en segundo plano para FileMaster."""

from __future__ import annotations

import atexit
import logging
import os
import time
from pathlib import Path

from config.logging_config import setup_logging
from config.settings import APP_STATE_DIR
from core.controller import FileMasterController

logger = logging.getLogger(__name__)
OBSERVER_PID_PATH = APP_STATE_DIR / "observer.pid"


def _write_pid() -> None:
    OBSERVER_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    OBSERVER_PID_PATH.write_text(str(os.getpid()), encoding="utf-8")


def _cleanup_pid() -> None:
    try:
        if OBSERVER_PID_PATH.exists():
            OBSERVER_PID_PATH.unlink()
    except OSError:
        pass


def run_background_observer() -> None:
    """Mantiene el watcher activo sin UI."""
    setup_logging()
    _write_pid()
    atexit.register(_cleanup_pid)

    controller = FileMasterController()
    controller.notify_callback = None

    if not controller.has_configuration():
        logger.warning("Observer en segundo plano cancelado: no hay configuración válida.")
        return

    controller.start_agent()
    logger.info("Observer en segundo plano activo.")

    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        logger.info("Observer en segundo plano detenido por señal.")
    finally:
        controller.stop_agent()
        _cleanup_pid()
