"""Simple SQLite-based result storage."""

import sqlite3
from typing import Optional, Any
from datetime import datetime


class ResultDB:
    """Database for storing quest results."""

    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest_name TEXT,
                result TEXT,
                error TEXT,
                timestamp TEXT
            )
            """
        )
        self.conn.commit()

    def store(self, quest_name: str, result: Optional[Any], error: Optional[str]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO results (quest_name, result, error, timestamp) VALUES (?, ?, ?, ?)",
            (
                quest_name,
                None if result is None else str(result),
                error,
                datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def fetch_all(self) -> list[tuple]:
        cur = self.conn.cursor()
        cur.execute("SELECT quest_name, result, error, timestamp FROM results")
        return cur.fetchall()
