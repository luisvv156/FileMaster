"""Configuracion persistente y rutas globales de FileMaster."""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCE_BASE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
APP_NAME = "FileMaster"


def _resolve_app_state_dir() -> Path:
    override = os.getenv("FILEMASTER_HOME", "").strip()
    if override:
        return Path(override).expanduser()

    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / APP_NAME


APP_STATE_DIR = _resolve_app_state_dir()
CONFIG_STATE_DIR = APP_STATE_DIR / "config"
DATA_DIR = APP_STATE_DIR / "data"
LOG_DIR = APP_STATE_DIR / "logs"
ASSETS_DIR = RESOURCE_BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
WINDOWS_ICON_PATH = ASSETS_DIR / "logo.ico"

LEGACY_CONFIG_DIR = BASE_DIR / "config"
LEGACY_DATA_DIR = BASE_DIR / "data"

USER_CONFIG_PATH = CONFIG_STATE_DIR / "user_config.json"
CATEGORIES_PATH = DATA_DIR / "categories.json"
RUNTIME_STATE_PATH = DATA_DIR / "runtime_state.json"
HISTORY_DB_PATH = DATA_DIR / "file_history.db"
EMBEDDINGS_CACHE_PATH = DATA_DIR / "embeddings_cache.pkl"
LOG_FILE_PATH = LOG_DIR / "filemaster.log"

DEFAULT_DUPLICATES_FOLDER_NAME = "_Duplicados"
WATCH_INTERVAL_SECONDS = 3.0
DEFAULT_SIMILARITY_THRESHOLD = 0.26

SUPPORTED_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".log",
    ".py",
    ".docx",
    ".pptx",
    ".pdf",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


@dataclass
class UserConfig:
    watch_folder: str = ""
    auto_rename: bool = True
    detect_duplicates: bool = True
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD

    @property
    def is_configured(self) -> bool:
        return bool(self.watch_folder.strip())

    @property
    def watch_path(self) -> Path | None:
        if not self.is_configured:
            return None
        return Path(self.watch_folder).expanduser()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _copy_if_needed(legacy_path: Path, target_path: Path) -> None:
    if target_path.exists() or not legacy_path.exists() or legacy_path.resolve() == target_path.resolve():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_path, target_path)


def ensure_data_files() -> None:
    CONFIG_STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    _copy_if_needed(LEGACY_CONFIG_DIR / "user_config.json", USER_CONFIG_PATH)
    _copy_if_needed(LEGACY_DATA_DIR / "categories.json", CATEGORIES_PATH)
    _copy_if_needed(LEGACY_DATA_DIR / "runtime_state.json", RUNTIME_STATE_PATH)
    _copy_if_needed(LEGACY_DATA_DIR / "file_history.db", HISTORY_DB_PATH)
    _copy_if_needed(LEGACY_DATA_DIR / "embeddings_cache.pkl", EMBEDDINGS_CACHE_PATH)

    if not USER_CONFIG_PATH.exists():
        _write_json(USER_CONFIG_PATH, asdict(UserConfig()))
    if not CATEGORIES_PATH.exists():
        _write_json(CATEGORIES_PATH, [])
    if not RUNTIME_STATE_PATH.exists():
        _write_json(RUNTIME_STATE_PATH, {})
    if not EMBEDDINGS_CACHE_PATH.exists():
        EMBEDDINGS_CACHE_PATH.write_bytes(b"")
    if not HISTORY_DB_PATH.exists():
        HISTORY_DB_PATH.touch()


def load_user_config() -> UserConfig:
    ensure_data_files()
    try:
        payload = json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return UserConfig()

    threshold = float(payload.get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD))
    if threshold < 0.1 or threshold > 0.65:
        threshold = DEFAULT_SIMILARITY_THRESHOLD

    return UserConfig(
        watch_folder=str(payload.get("watch_folder", "")),
        auto_rename=bool(payload.get("auto_rename", True)),
        detect_duplicates=bool(payload.get("detect_duplicates", True)),
        similarity_threshold=threshold,
    )


def save_user_config(config: UserConfig) -> None:
    ensure_data_files()
    _write_json(USER_CONFIG_PATH, asdict(config))


def load_categories() -> list[dict[str, object]]:
    ensure_data_files()
    try:
        payload = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def save_categories(categories: list[dict[str, object]]) -> None:
    ensure_data_files()
    _write_json(CATEGORIES_PATH, categories)


def load_runtime_state() -> dict[str, object]:
    ensure_data_files()
    try:
        payload = json.loads(RUNTIME_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_runtime_state(state: dict[str, object]) -> None:
    ensure_data_files()
    _write_json(RUNTIME_STATE_PATH, state)
