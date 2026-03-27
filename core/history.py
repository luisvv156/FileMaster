"""Persistencia del historial en SQLite."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class HistoryRecord:
    source: str
    destination: str
    action: str
    category: str = ""
    confidence: float = 0.0
    details: str = ""


class HistoryRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    action TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    details TEXT NOT NULL
                )
                """
            )

    def add_record(self, record: HistoryRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO history (timestamp, source, destination, action, category, confidence, details)
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

    def recent_records(self, limit: int = 8) -> list[dict[str, object]]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT timestamp, source, destination, action, category, confidence, details
                FROM history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        return [
            {
                "timestamp": row[0],
                "source": row[1],
                "destination": row[2],
                "action": row[3],
                "category": row[4],
                "confidence": row[5],
                "details": json.loads(row[6]) if row[6].startswith("{") else row[6],
            }
            for row in rows
        ]

    def overall_stats(self) -> dict[str, float]:
        with self._connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM history WHERE action IN ('organized', 'manual_classified')"
            ).fetchone()[0]
            duplicates = connection.execute(
                "SELECT COUNT(*) FROM history WHERE action = 'duplicate_moved'"
            ).fetchone()[0]
            average_confidence = connection.execute(
                "SELECT AVG(confidence) FROM history WHERE action IN ('organized', 'manual_classified')"
            ).fetchone()[0]

        return {
            "total_organized": float(total or 0),
            "duplicates_detected": float(duplicates or 0),
            "average_confidence": float(average_confidence or 0.0),
        }
