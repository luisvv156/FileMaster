"""Aplicacion principal de FileMaster — pywebview."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

import webview

from config.settings import APP_STATE_DIR, BASE_DIR
from core.controller import FileMasterController

logger = logging.getLogger(__name__)


# Ruta a la carpeta web
WEB_DIR = Path(__file__).parent / "web"
OBSERVER_PID_PATH = APP_STATE_DIR / "observer.pid"


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _stop_background_observer() -> None:
    if not OBSERVER_PID_PATH.exists():
        return
    try:
        pid = int(OBSERVER_PID_PATH.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        pid = 0
    if pid > 0 and _pid_running(pid):
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            logger.debug("No se pudo detener observer previo (pid=%s): %s", pid, exc)
    try:
        OBSERVER_PID_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _start_background_observer() -> None:
    if OBSERVER_PID_PATH.exists():
        try:
            pid = int(OBSERVER_PID_PATH.read_text(encoding="utf-8").strip() or "0")
            if pid > 0 and _pid_running(pid):
                return
        except Exception:
            pass

    main_path = str((BASE_DIR / "main.py").resolve())
    observer_cmd: list[str]
    if getattr(sys, "frozen", False):
        # En app empaquetada, reutilizar el ejecutable actual sin consola.
        observer_cmd = [sys.executable, "--observer"]
    else:
        # En desarrollo, preferir pythonw para evitar que aparezca consola.
        py_exe = Path(sys.executable)
        pyw_exe = py_exe.with_name("pythonw.exe")
        runner = str(pyw_exe if pyw_exe.exists() else py_exe)
        observer_cmd = [runner, main_path, "--observer"]

    flags = 0
    for value in ("DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"):
        flags |= int(getattr(subprocess, value, 0))
    startupinfo = None
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        startupinfo.wShowWindow = 0
    try:
        subprocess.Popen(
            observer_cmd,
            cwd=str(BASE_DIR),
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
        )
    except Exception as exc:
        logger.warning("No se pudo iniciar observer en segundo plano: %s", exc)


class FileMasterAPI:
    """Bridge entre JavaScript y el controlador Python."""

    def __init__(self, controller: FileMasterController) -> None:
        self._controller = controller
        self._window: webview.Window | None = None
        self._closing = False

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def set_closing(self, closing: bool = True) -> None:
        self._closing = closing

    # ── Lectura de estado ──────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        return self._controller.snapshot()

    def has_configuration(self) -> bool:
        return self._controller.has_configuration()

    def manual_categories(self) -> list[str]:
        return self._controller.manual_categories()

    # ── Acciones ───────────────────────────────────────────────────────────────

    def update_config(self, watch_folder: str, auto_rename: bool, detect_duplicates: bool) -> None:
        self._controller.update_config(watch_folder, auto_rename, detect_duplicates)

    def analyze_initial(self) -> list:
        return self._controller.analyze_initial()

    def confirm_groups(self, mapping: dict) -> dict:
        return self._controller.confirm_groups(mapping)

    def organize_now(self) -> dict:
        return self._controller.organize_now()

    def toggle_agent(self) -> None:
        self._controller.toggle_agent()

    def manual_classify(self, file_path: str, category_name: str, new_folder_name: str = "") -> None:
        self._controller.manual_classify(file_path, category_name, new_folder_name)

    def delete_duplicates(self, selected_paths: list) -> None:
        self._controller.delete_duplicates(selected_paths)

    def restore_duplicates(self, selected_paths: list) -> None:
        self._controller.restore_duplicates(selected_paths)

    def stop_agent(self) -> None:
        self._controller.stop_agent()

    # ── Navegación ─────────────────────────────────────────────────────────────

    def navigate(self, screen: str) -> None:
        """Navega a una pantalla desde Python (ej: callback del watcher)."""
        if self._window and not self._closing:
            try:
                self._window.evaluate_js(f"window.app.navigate('{screen}')")
            except Exception as exc:
                logger.debug("No se pudo navegar a '%s': %s", screen, exc)

    def push_snapshot(self) -> None:
        """Empuja el snapshot actualizado a la UI (llamado por el watcher)."""
        if self._window and not self._closing:
            try:
                data = json.dumps(self._controller.snapshot(), ensure_ascii=False)
                self._window.evaluate_js(f"window.app.onSnapshotPush({data})")
            except Exception as exc:
                logger.debug("No se pudo enviar snapshot a UI: %s", exc)

    # ── Utilidades del sistema ─────────────────────────────────────────────────

    def open_folder_dialog(self) -> str | None:
        """Abre el diálogo nativo del SO para seleccionar carpeta."""
        if self._window and not self._closing:
            try:
                result = self._window.create_file_dialog(
                    webview.FOLDER_DIALOG,
                    allow_multiple=False,
                )
                if result:
                    return result[0]
            except Exception as exc:
                logger.debug("No se pudo abrir diálogo de carpeta: %s", exc)
        return None


def _notify_factory(api: FileMasterAPI):
    """Crea el callback que el controller llama cuando hay cambios."""
    def _notify():
        threading.Thread(target=api.push_snapshot, daemon=True).start()
    return _notify


def run_app() -> None:
    from config.logging_config import setup_logging
    setup_logging()
    _stop_background_observer()

    # Controller
    controller = FileMasterController()
    api = FileMasterAPI(controller)
    controller.notify_callback = _notify_factory(api)

    # Detectar pantalla inicial
    initial_screen = "welcome"
    snapshot = controller.snapshot()
    if snapshot.get("pending_groups"):
        initial_screen = "groups"
    elif controller.has_configuration():
        initial_screen = "main"

    index_path = str(WEB_DIR / "index.html")

    window = webview.create_window(
        title="FileMaster",
        url=f"file:///{index_path.replace(chr(92), '/')}",
        js_api=api,
        width=1100,
        height=680,
        min_size=(900, 580),
        background_color="#0f1219",
        text_select=False,
    )

    api.set_window(window)

    def on_loaded():
        window.evaluate_js(f"window.app.navigate('{initial_screen}')")

    window.events.loaded += on_loaded

    def on_closing(*_args):
        api.set_closing(True)
        controller.stop_agent()
        if controller.has_configuration():
            _start_background_observer()

    window.events.closing += on_closing

    webview.start(debug=False)
