"""Aplicacion principal de FileMaster — pywebview."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import webview

from core.controller import FileMasterController


# Ruta a la carpeta web
WEB_DIR = Path(__file__).parent / "web"


class FileMasterAPI:
    """Bridge entre JavaScript y el controlador Python."""

    def __init__(self, controller: FileMasterController) -> None:
        self._controller = controller
        self._window: webview.Window | None = None

    def set_window(self, window: webview.Window) -> None:
        self._window = window

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
        if self._window:
            self._window.evaluate_js(f"window.app.navigate('{screen}')")

    def push_snapshot(self) -> None:
        """Empuja el snapshot actualizado a la UI (llamado por el watcher)."""
        if self._window:
            data = json.dumps(self._controller.snapshot(), ensure_ascii=False)
            self._window.evaluate_js(f"window.app.onSnapshotPush({data})")

    # ── Utilidades del sistema ─────────────────────────────────────────────────

    def open_folder_dialog(self) -> str | None:
        """Abre el diálogo nativo del SO para seleccionar carpeta."""
        if self._window:
            result = self._window.create_file_dialog(
                webview.FOLDER_DIALOG,
                allow_multiple=False,
            )
            if result:
                return result[0]
        return None


def _notify_factory(api: FileMasterAPI):
    """Crea el callback que el controller llama cuando hay cambios."""
    def _notify():
        threading.Thread(target=api.push_snapshot, daemon=True).start()
    return _notify


def run_app() -> None:
    from config.logging_config import setup_logging
    setup_logging()

    # Controller
    controller = FileMasterController()
    api = FileMasterAPI(controller)
    controller.notify_callback = api.push_snapshot

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

    def on_closing():
        controller.stop_agent()

    window.events.closing += on_closing

    webview.start(debug=False)