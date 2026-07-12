from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Deal


class DealStore:
    """Stockage SQLite des deals déjà vus, pour éviter les doublons."""

    def __init__(self, db_path: str | Path):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                price REAL,
                temperature REAL,
                published_at TEXT,
                fetched_at TEXT NOT NULL,
                matched_watch TEXT
            )
            """
        )
        self._conn.commit()

    def is_seen(self, deal_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM deals WHERE id = ?", (deal_id,)
        ).fetchone()
        return row is not None

    def save(self, deal: Deal, matched_watch: str | None = None) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO deals
                (id, source, title, url, price, temperature,
                 published_at, fetched_at, matched_watch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deal.id,
                deal.source,
                deal.title,
                deal.url,
                deal.price,
                deal.temperature,
                deal.published_at.isoformat() if deal.published_at else None,
                deal.fetched_at.isoformat(),
                matched_watch,
            ),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
