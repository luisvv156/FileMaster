"""Watcher por sondeo para el sistema de archivos."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from config.settings import DEFAULT_DUPLICATES_FOLDER_NAME, WATCH_INTERVAL_SECONDS


class FileWatcher:
    def __init__(self, callback, *, interval_seconds: float = WATCH_INTERVAL_SECONDS) -> None:
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
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.interval_seconds)
            if self._paused or self.watch_folder is None:
                continue
            current = self._capture_snapshot(self.watch_folder)
            if current != self._snapshot:
                self._snapshot = current
                self.callback()

    def _capture_snapshot(self, folder: Path) -> dict[str, float]:
        snapshot = {}
        if not folder.exists():
            return snapshot

        for child in folder.iterdir():
            if not child.is_file():
                if child.name == DEFAULT_DUPLICATES_FOLDER_NAME:
                    continue
                continue
            snapshot[str(child)] = child.stat().st_mtime
        return snapshot
