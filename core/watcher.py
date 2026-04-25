"""Watcher por sondeo para el sistema de archivos de FileMaster."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from config.settings import DEFAULT_DUPLICATES_FOLDER_NAME, WATCH_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

_IGNORED_FOLDER_NAMES = frozenset({
    DEFAULT_DUPLICATES_FOLDER_NAME,
    "_Papelera",
    "_Trash",
    ".filemaster",
})


class FileWatcher:
    """Monitorea una carpeta por sondeo y notifica cambios al controller.

    El callback no recibe argumentos — el controller lee el estado
    directamente desde el disco al ser invocado.
    """

    def __init__(
        self,
        callback,
        *,
        interval_seconds: float = WATCH_INTERVAL_SECONDS,
    ) -> None:
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.watch_folder: Path | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._paused = False
        self._snapshot: dict[str, float] = {}

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def paused(self) -> bool:
        return self._paused

    def start(self, folder: Path) -> None:
        self.stop()
        self.watch_folder = folder
        self._snapshot = self._capture_snapshot(folder)
        self._stop_event.clear()
        self._paused = False
        self._thread = threading.Thread(target=self._loop, daemon=True, name="FileWatcher")
        self._thread.start()
        logger.info("Watcher iniciado en: %s (intervalo: %.1fs)", folder, self.interval_seconds)

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 1.0)
        self._thread = None
        logger.info("Watcher detenido.")

    def pause(self) -> None:
        self._paused = True
        logger.debug("Watcher pausado.")

    def resume(self) -> None:
        # Actualizar snapshot para no re-detectar archivos ya organizados
        if self.watch_folder:
            self._snapshot = self._capture_snapshot(self.watch_folder)
        self._paused = False
        logger.debug("Watcher reanudado.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.interval_seconds)

            if self._paused or self.watch_folder is None:
                continue

            if not self.watch_folder.exists():
                logger.warning("Carpeta monitoreada no existe: %s", self.watch_folder)
                continue

            current = self._capture_snapshot(self.watch_folder)

            has_new = any(p not in self._snapshot for p in current)
            has_modified = any(
                self._snapshot.get(p) != mtime
                for p, mtime in current.items()
                if p in self._snapshot
            )

            if has_new or has_modified:
                self._snapshot = current
                logger.debug("Cambios detectados — disparando callback")
                try:
                    # ✅ FIX: callback sin argumentos, igual que controller espera
                    self.callback()
                except Exception as exc:
                    logger.error("Error en callback del watcher: %s", exc, exc_info=True)

    def _capture_snapshot(self, folder: Path) -> dict[str, float]:
        snapshot: dict[str, float] = {}
        if not folder.exists():
            return snapshot
        try:
            entries = list(folder.iterdir())
        except PermissionError:
            logger.warning("Sin permiso para leer: %s", folder)
            return snapshot

        for entry in entries:
            if entry.is_dir():
                continue
            if not entry.is_file():
                continue
            # Ignorar archivos temporales de Windows/Office
            if entry.name.startswith("~$") or entry.name.startswith("."):
                continue
            try:
                snapshot[str(entry)] = entry.stat().st_mtime
            except (OSError, PermissionError):
                logger.debug("No se pudo stat: %s", entry.name)

        return snapshot