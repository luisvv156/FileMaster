"""Persistencia del historial de operaciones en SQLite."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HistoryRecord:
    """Representa una operación realizada por FileMaster sobre un archivo."""
    source: str
    destination: str
    action: str
    category: str = ""
    confidence: float = 0.0
    details: str = ""


class HistoryRepository:
    """Repositorio SQLite para el historial de operaciones de FileMaster.

    Almacena cada movimiento, renombrado o clasificación para permitir:
    - Visualización en la pantalla de historial de la GUI.
    - Estadísticas en la pantalla de resumen.
    - Deshacer la última operación.
    - Búsqueda por nombre o categoría.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row          # Acceso por nombre de columna
        conn.execute("PRAGMA journal_mode=WAL") # Write-Ahead Logging: más rápido en escrituras concurrentes
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ------------------------------------------------------------------
    # Esquema
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   TEXT    NOT NULL,
                    source      TEXT    NOT NULL,
                    destination TEXT    NOT NULL,
                    action      TEXT    NOT NULL,
                    category    TEXT    NOT NULL DEFAULT '',
                    confidence  REAL    NOT NULL DEFAULT 0.0,
                    details     TEXT    NOT NULL DEFAULT ''
                )
            """)
            # Índices para queries frecuentes de la GUI
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_action ON history(action)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_source ON history(source)"
            )
        logger.debug("Esquema de historial verificado en: %s", self.database_path)

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def add_record(self, record: HistoryRecord) -> int:
        """Inserta un registro de operación en el historial.

        Args:
            record: Datos de la operación realizada.

        Returns:
            El ID (rowid) del registro insertado.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO history
                    (timestamp, source, destination, action, category, confidence, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    record.source,
                    record.destination,
                    record.action,
                    record.category,
                    record.confidence,
                    record.details,
                ),
            )
            record_id = cursor.lastrowid
            logger.debug(
                "Historial [%s]: '%s' → '%s'",
                record.action, Path(record.source).name, Path(record.destination).name,
            )
            return record_id or -1

    def delete_record(self, record_id: int) -> bool:
        """Elimina un registro específico por ID (usado al deshacer).

        Returns:
            True si se eliminó correctamente.
        """
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def clear_history(self) -> int:
        """Borra todo el historial. Retorna el número de registros eliminados."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM history")
            count = cursor.rowcount
            logger.info("Historial borrado: %d registros eliminados.", count)
            return count

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def recent_records(self, limit: int = 50) -> list[dict]:
        """Retorna los registros más recientes para la pantalla de historial.

        Args:
            limit: Número máximo de registros (default 50 para la GUI).

        Returns:
            Lista de dicts con claves: id, timestamp, source, destination,
            action, category, confidence, details.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, source, destination, action,
                       category, confidence, details
                FROM history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_last_record(self) -> dict | None:
        """Obtiene el registro más reciente. Útil para el botón 'Deshacer'."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def search(self, query: str, limit: int = 100) -> list[dict]:
        """Busca registros por nombre de archivo o categoría.

        Args:
            query: Texto a buscar (parcial, insensible a mayúsculas).
            limit: Número máximo de resultados.

        Returns:
            Lista de registros que coinciden con la búsqueda.
        """
        pattern = f"%{query.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, source, destination, action,
                       category, confidence, details
                FROM history
                WHERE LOWER(source) LIKE ?
                   OR LOWER(destination) LIKE ?
                   OR LOWER(category) LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def records_by_action(self, action: str, limit: int = 200) -> list[dict]:
        """Filtra registros por tipo de acción.

        Args:
            action: Ej. 'organized', 'duplicate_moved', 'manual_classified', 'trash'
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, source, destination, action,
                       category, confidence, details
                FROM history
                WHERE action = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (action, limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Estadísticas (pantalla de resumen)
    # ------------------------------------------------------------------

    def overall_stats(self) -> dict[str, float]:
        """Retorna estadísticas agregadas para la pantalla de resumen.

        Returns:
            Dict con: total_organized, duplicates_detected, average_confidence,
            total_records, trash_count.
        """
        with self._connect() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE action IN ('organized', 'manual_classified'))
                        AS total_organized,
                    COUNT(*) FILTER (WHERE action = 'duplicate_moved')
                        AS duplicates_detected,
                    AVG(confidence) FILTER (WHERE action IN ('organized', 'manual_classified'))
                        AS average_confidence,
                    COUNT(*) AS total_records,
                    COUNT(*) FILTER (WHERE action = 'trash')
                        AS trash_count
                FROM history
            """).fetchone()

        return {
            "total_organized":    float(row["total_organized"] or 0),
            "duplicates_detected": float(row["duplicates_detected"] or 0),
            "average_confidence":  float(row["average_confidence"] or 0.0),
            "total_records":       float(row["total_records"] or 0),
            "trash_count":         float(row["trash_count"] or 0),
        }

    def category_breakdown(self) -> list[dict]:
        """Retorna el conteo de archivos organizados por categoría.

        Útil para el gráfico de pastel en la pantalla de resumen de la GUI.

        Returns:
            Lista de {'category': str, 'count': int} ordenada de mayor a menor.
        """
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT category, COUNT(*) AS count
                FROM history
                WHERE action IN ('organized', 'manual_classified')
                  AND category != ''
                GROUP BY category
                ORDER BY count DESC
            """).fetchall()
        return [{"category": row["category"], "count": row["count"]} for row in rows]

    # ------------------------------------------------------------------
    # Helper interno
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convierte una fila SQLite en dict, parseando el campo details si es JSON."""
        d = dict(row)
        raw_details = d.get("details", "")
        if raw_details:
            try:
                d["details"] = json.loads(raw_details)
            except (json.JSONDecodeError, TypeError):
                pass  # Dejar como string si no es JSON válido
        return d