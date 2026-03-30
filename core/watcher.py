"""Watcher por sondeo para el sistema de archivos de FileMaster."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from config.settings import DEFAULT_DUPLICATES_FOLDER_NAME, WATCH_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

# Carpetas internas de FileMaster que nunca deben disparar el callback
_IGNORED_FOLDER_NAMES = frozenset({
    DEFAULT_DUPLICATES_FOLDER_NAME,
    "_Papelera",
    "_Trash",
    ".filemaster",
})


class FileWatcher:
    """Monitorea una carpeta por sondeo y notifica cambios al controller.

    Usa polling en lugar de inotify/FSEvents para mayor compatibilidad
    con Windows y carpetas de red (NAS, OneDrive, etc.).

    El callback recibe los conjuntos de archivos nuevos y modificados:
        def on_change(new_files: set[Path], modified_files: set[Path]) -> None: ...
    """

    def __init__(
        self,
        callback,
        *,
        interval_seconds: float = WATCH_INTERVAL_SECONDS,
    ) -> None:
        """
        Args:
            callback: Función llamada al detectar cambios.
                      Firma: callback(new_files: set[Path], modified_files: set[Path])
            interval_seconds: Segundos entre cada sondeo (default 3.0).
        """
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.watch_folder: Path | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._paused = False
        self._snapshot: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Propiedades públicas
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True si el thread de monitoreo está activo."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def paused(self) -> bool:
        """True si el watcher está pausado temporalmente."""
        return self._paused

    # ------------------------------------------------------------------
    # Control del watcher
    # ------------------------------------------------------------------

    def start(self, folder: Path) -> None:
        """Inicia el monitoreo de la carpeta especificada.

        Si ya había un watcher activo, lo detiene primero.

        Args:
            folder: Carpeta a monitorear.
        """
        self.stop()
        self.watch_folder = folder
        self._snapshot = self._capture_snapshot(folder)
        self._stop_event.clear()
        self._paused = False
        self._thread = threading.Thread(target=self._loop, daemon=True, name="FileWatcher")
        self._thread.start()
        logger.info("Watcher iniciado en: %s (intervalo: %.1fs)", folder, self.interval_seconds)

    def stop(self) -> None:
        """Detiene el watcher y espera a que el thread termine."""
        if not self.is_running:
            return
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 1.0)
        self._thread = None
        logger.info("Watcher detenido.")

    def pause(self) -> None:
        """Pausa el monitoreo sin detener el thread (útil durante organización masiva)."""
        self._paused = True
        logger.debug("Watcher pausado.")

    def resume(self) -> None:
        """Reanuda el monitoreo y actualiza el snapshot para evitar falsos positivos."""
        # Actualizar snapshot antes de reanudar para no detectar cambios
        # que ocurrieron mientras estaba pausado (ej: la propia organización)
        if self.watch_folder:
            self._snapshot = self._capture_snapshot(self.watch_folder)
        self._paused = False
        logger.debug("Watcher reanudado.")

    # ------------------------------------------------------------------
    # Loop interno
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        """Bucle principal del thread de monitoreo."""
        while not self._stop_event.is_set():
            time.sleep(self.interval_seconds)

            if self._paused or self.watch_folder is None:
                continue

            if not self.watch_folder.exists():
                logger.warning("Carpeta monitoreada no existe: %s", self.watch_folder)
                continue

            current = self._capture_snapshot(self.watch_folder)

            # Detectar archivos nuevos y modificados por separado
            new_files: set[Path] = set()
            modified_files: set[Path] = set()

            for path_str, mtime in current.items():
                if path_str not in self._snapshot:
                    new_files.add(Path(path_str))
                elif self._snapshot[path_str] != mtime:
                    modified_files.add(Path(path_str))

            if new_files or modified_files:
                self._snapshot = current
                logger.debug(
                    "Cambios detectados: %d nuevos, %d modificados",
                    len(new_files), len(modified_files),
                )
                try:
                    self.callback(new_files, modified_files)
                except Exception as exc:
                    logger.error("Error en callback del watcher: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def _capture_snapshot(self, folder: Path) -> dict[str, float]:
        """Captura el estado actual de la carpeta como {path: mtime}.

        Solo incluye archivos directos en la raíz monitoreada (no recursivo),
        excluyendo las subcarpetas internas de FileMaster.

        Args:
            folder: Carpeta a escanear.

        Returns:
            Dict de {ruta_str: mtime} para todos los archivos relevantes.
        """
        snapshot: dict[str, float] = {}

        if not folder.exists():
            return snapshot

        try:
            entries = list(folder.iterdir())
        except PermissionError:
            logger.warning("Sin permiso para leer: %s", folder)
            return snapshot

        for entry in entries:
            # Ignorar carpetas (incluyendo las internas de FileMaster)
            if entry.is_dir():
                if entry.name not in _IGNORED_FOLDER_NAMES:
                    pass  # Actualmente no monitoreamos subcarpetas
                continue

            if not entry.is_file():
                continue

            try:
                snapshot[str(entry)] = entry.stat().st_mtime
            except (OSError, PermissionError):
                # Archivo en uso (abierto por otra app en Windows) — lo ignoramos
                logger.debug("No se pudo stat: %s", entry.name)

        return snapshot