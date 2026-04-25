"""Configuración centralizada de logging para FileMaster."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import LOG_FILE_PATH, ensure_data_files

# Librerías externas que son muy verbosas — las silenciamos a WARNING
_NOISY_LOGGERS = (
    "sentence_transformers",
    "transformers",
    "torch",
    "huggingface_hub",
    "watchdog",
    "PIL",
    "fitz",          # PyMuPDF
    "pdfminer",
)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False  # Guarda para no llamar basicConfig dos veces


def setup_logging(
    level: int = logging.INFO,
    *,
    console_level: int | None = None,
) -> None:
    """Configura el sistema de logging de FileMaster.

    Establece dos handlers:
    - Archivo rotativo (1 MB, 3 backups) en LOG_FILE_PATH — nivel `level`
    - Consola (stream) — nivel `console_level` o `level` si no se especifica

    Las librerías externas ruidosas (sentence_transformers, watchdog, torch)
    se silencian automáticamente a WARNING para mantener los logs limpios.

    Args:
        level: Nivel mínimo para el handler de archivo (default INFO).
        console_level: Nivel para la consola. Si None, usa el mismo que `level`.
                       En producción conviene pasar `logging.WARNING` para
                       reducir el output en terminal.
    """
    global _configured
    if _configured:
        return
    _configured = True

    ensure_data_files()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Handler de archivo — guarda todo desde `level`
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=1_048_576,   # 1 MB por archivo
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Handler de consola — opcionalmente más silencioso que el archivo
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(console_level if console_level is not None else level)

    logging.basicConfig(
        level=logging.DEBUG,   # El root logger acepta todo; los handlers filtran
        handlers=[file_handler, stream_handler],
        force=True,
    )

    # Silenciar librerías externas ruidosas
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Primera línea del log — confirma que el sistema arrancó
    logger = logging.getLogger("filemaster")
    logger.info("=" * 60)
    logger.info("FileMaster iniciado — nivel de log: %s", logging.getLevelName(level))
    logger.info("Log guardado en: %s", LOG_FILE_PATH)
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """Atajo para obtener un logger con el prefijo 'filemaster.'.

    Uso recomendado en cada módulo:
        from config.logging_config import get_logger
        logger = get_logger(__name__)

    Esto asegura que todos los loggers del proyecto viven bajo
    el namespace 'filemaster.*', facilitando filtrarlos en el archivo de log.

    Args:
        name: Normalmente `__name__` del módulo que llama.

    Returns:
        Logger listo para usar.
    """
    # Si ya viene con el prefijo no lo duplicamos
    if name.startswith("filemaster.") or name == "filemaster":
        return logging.getLogger(name)
    return logging.getLogger(f"filemaster.{name}")