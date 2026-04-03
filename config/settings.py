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

# ── Umbrales de similitud ──────────────────────────────────────────────────
DEFAULT_SIMILARITY_THRESHOLD = 0.70
DEFAULT_CLUSTERING_THRESHOLD = 0.62
DEFAULT_DUPLICATE_SIMILARITY = 0.88
DEFAULT_COSINE_THRESHOLD = 0.70

SUPPORTED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log", ".py",
    ".docx", ".pptx", ".pdf",
    ".xlsx", ".xls",
    ".odt", ".odp", ".ods",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


# ── Categorías académicas predeterminadas ─────────────────────────────────
# Se usan cuando categories.json está vacío (primera ejecución o después de reset).
# Basadas en las materias reales del usuario.
DEFAULT_ACADEMIC_CATEGORIES: list[dict] = [
    {
        "name": "Taller de Investigacion",
        "keywords": [
            "investigacion", "metodologia", "hipotesis", "marco", "teorico",
            "bibliografia", "fuente", "cita", "referencia", "abstract",
            "resumen", "objetivo", "planteamiento", "problema", "justificacion",
            "tesis", "ensayo", "resultado", "conclusion", "encuesta",
            "variable", "apa", "capitulo", "muestra", "instrumento", "raul", "monforte", "chulin"
        ],
        "files": []
    },
    {
        "name": "Tecnologias de Virtualizacion",
        "keywords": [
            "virtualizacion", "maquina", "virtual", "vmware", "virtualbox",
            "hypervisor", "contenedor", "docker", "imagen", "snapshot",
            "vm", "host", "guest", "instancia", "servidor", "cluster", "dagoberto", "quintanilla", "alvarado",
            "proxmox", "hyper", "particion", "iso", "ovf"
        ],
        "files": []
    },
    {
        "name": "Tecnologias en la Nube",
        "keywords": [
            "nube", "cloud", "aws", "azure", "google", "gcp", "s3",
            "bucket", "lambda", "serverless", "iaas", "paas", "saas",
            "storage", "escalabilidad", "microservicio", "api", "rest",
            "despliegue", "kubernetes", "balanceo", "region", "firebase", "omar", "eduardo", "betanzos", "martinez"
        ],
        "files": []
    },
    {
        "name": "Hacking Etico",
        "keywords": [
            "hacking", "etico", "pentest", "penetracion", "vulnerabilidad",
            "exploit", "nmap", "escaneo", "puerto", "reconocimiento",
            "metasploit", "kali", "firewall", "intrusion", "cve",
            "payload", "shell", "privilege", "footprinting", "enumeration",
            "sniffing", "tcp", "udp", "ataque", "defensa", "parche", "jose", "eduardo", "rios", "mendoza"
        ],
        "files": []
    },
    {
        "name": "Administracion de Redes",
        "keywords": [
            "red", "router", "switch", "protocolo", "ip", "mascara",
            "subred", "vlan", "ospf", "bgp", "dns", "dhcp", "nat",
            "gateway", "topologia", "ethernet", "wifi", "inalambrico",
            "monitoreo", "snmp", "cisco", "tracer", "latencia", "banda", "aurora", "moreno", "rodriguez", "ubuntu", "zabbix", "prtg"
        ],
        "files": []
    },
    {
        "name": "Inteligencia Artificial",
        "keywords": [
            "inteligencia", "artificial", "machine", "learning", "neuronal",
            "algoritmo", "clasificacion", "regresion", "clustering",
            "entrenamiento", "modelo", "prediccion", "embedding",
            "transformer", "nlp", "procesamiento", "lenguaje", "natural",
            "deep", "backpropagation", "dataset", "epoch", "perceptron",
            "feature", "overfitting", "tensorflow", "pytorch", "nora", "hilda", "reyes", "ramirez", "filemaster", "tecnicas"
        ],
        "files": []
    },
    {
        "name": "Programacion Logica y Funcional",
        "keywords": [
            "prolog", "haskell", "lisp", "erlang", "funcional", "logica",
            "predicado", "clausula", "recursion", "lambda", "patron",
            "matching", "inmutable", "backtracking", "lazy", "python", "sigvet",
            "inferencia", "declarativo", "vibecoding", "currying", "composicion",
            "arbol", "lista", "higher", "orden", "pureza", "alexis", "ivan", "roman", "chevez"
        ],
        "files": []
    },
]


@dataclass
class UserConfig:
    watch_folder: str = ""
    auto_rename: bool = True
    auto_organize: bool = True
    detect_duplicates: bool = True
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD

    @property
    def is_configured(self) -> bool:
        return bool(self.watch_folder.strip())

    @property
    def watch_path(self) -> Path | None:
        if not self.is_configured:
            return None
        p = Path(self.watch_folder).expanduser()
        return p if p.exists() else None


def reset_user_config() -> None:
    save_user_config(UserConfig())


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
    if threshold < 0.30 or threshold > 1.0:
        threshold = DEFAULT_SIMILARITY_THRESHOLD

    return UserConfig(
        watch_folder=str(payload.get("watch_folder", "")),
        auto_rename=bool(payload.get("auto_rename", True)),
        auto_organize=bool(payload.get("auto_organize", True)),
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
        return list(DEFAULT_ACADEMIC_CATEGORIES)
    # ✅ Si está vacío, usar categorías predeterminadas
    if not payload or not isinstance(payload, list):
        return list(DEFAULT_ACADEMIC_CATEGORIES)
    return payload


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