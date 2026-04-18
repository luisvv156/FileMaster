"""
Reset completo de FileMaster para desarrollo.
Ejecutar: python reset_dev.py  (o automático con FILEMASTER_DEV_RESET=1)
"""

from __future__ import annotations

import pickle
import shutil
import sqlite3
from pathlib import Path

# Importar rutas del proyecto
from config.settings import (
    APP_STATE_DIR,
    CATEGORIES_PATH,
    EMBEDDINGS_CACHE_PATH,
    HISTORY_DB_PATH,
    RUNTIME_STATE_PATH,
    USER_CONFIG_PATH,
    DEFAULT_ACADEMIC_CATEGORIES,
    _write_json,
    ensure_data_files,
)
from dataclasses import asdict
from config.settings import UserConfig


def reset():
    print("\n🔄 Iniciando reset completo de FileMaster...\n")

    # 1. Recrear carpetas base (por si no existen)
    ensure_data_files()

    # 2. Limpiar categories.json → vacío para que cargue las predeterminadas
    CATEGORIES_PATH.write_text("[]", encoding="utf-8")
    print(f"  ✅ categories.json  → []")

    # 3. Limpiar runtime_state.json → estado inicial limpio
    RUNTIME_STATE_PATH.write_text(
        """{
  "pending_groups": [],
  "duplicate_groups": [],
  "unclassified": [],
  "last_summary": {
    "detected": 0,
    "organized": 0,
    "renamed": 0,
    "unclassified": 0,
    "duplicates": 0,
    "precision": 0.0,
    "duration_seconds": 0.0,
    "folders": []
  },
  "agent_started_at": "",
  "last_run": ""
}""",
        encoding="utf-8",
    )
    print(f"  ✅ runtime_state.json → estado inicial")

    # 4. Resetear user_config.json → config vacía (sin carpeta configurada)
    _write_json(USER_CONFIG_PATH, asdict(UserConfig()))
    print(f"  ✅ user_config.json → config limpia")

    # 5. Limpiar base de datos de historial
    if HISTORY_DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(HISTORY_DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            count = 0
            for (table_name,) in tables:
                # ✅ Saltar tablas internas de SQLite
                if table_name.startswith("sqlite_"):
                    continue
                cursor.execute(f"DROP TABLE IF EXISTS [{table_name}]")
                count += 1
            conn.commit()
            conn.close()  # ✅ Cerrar ANTES de cualquier operación con el archivo
            print(f"  ✅ file_history.db → {count} tablas eliminadas")
        except Exception as exc:
            try:
                conn.close()  # Asegurar que se cierra antes de borrar
            except Exception:
                pass
            HISTORY_DB_PATH.unlink()
            HISTORY_DB_PATH.touch()
            print(f"  ✅ file_history.db → recreado (falló SQL: {exc})")
    else:
        HISTORY_DB_PATH.touch()
        print(f"  ✅ file_history.db → creado vacío")

    # 6. Limpiar caché de embeddings
    EMBEDDINGS_CACHE_PATH.write_bytes(b"")
    print(f"  ✅ embeddings_cache.pkl → vacío")

    # 7. Limpiar logs (opcional — comentar si prefieres conservarlos)
    log_dir = APP_STATE_DIR / "logs"
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            log_file.write_text("", encoding="utf-8")
        print(f"  ✅ logs → vaciados")

    print(f"\n📁 Estado guardado en: {APP_STATE_DIR}")
    print("✨ Reset completo. La app iniciará como instalación nueva.\n")


if __name__ == "__main__":
    reset()