"""Simple SQLite-based result storage."""

import sqlite3
from typing import Optional, Any
from datetime import datetime

try:
    from sqlalchemy import (
        Column,
        Integer,
        MetaData,
        String,
        Table,
        insert,
        select,
    )
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        create_async_engine,
    )
    SQLALCHEMY_AVAILABLE = True
except Exception:  # pragma: no cover - sqlalchemy may not be installed
    SQLALCHEMY_AVAILABLE = False


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


if SQLALCHEMY_AVAILABLE:
    class AsyncResultDB:
        """Asynchronous database using SQLAlchemy."""

        def __init__(self, url: str = "sqlite+aiosqlite:///:memory:") -> None:
            self.engine: AsyncEngine = create_async_engine(url, future=True)
            self.metadata = MetaData()
            self.results = Table(
                "results",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("quest_name", String),
                Column("result", String),
                Column("error", String),
                Column("timestamp", String),
            )

            import asyncio

            asyncio.run(self._init_tables())

        async def _init_tables(self) -> None:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)

        async def store(self, quest_name: str, result: Optional[Any], error: Optional[str]) -> None:
            async with self.engine.begin() as conn:
                await conn.execute(
                    insert(self.results).values(
                        quest_name=quest_name,
                        result=None if result is None else str(result),
                        error=error,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        async def fetch_all(self) -> list[tuple]:
            async with AsyncSession(self.engine) as session:
                result = await session.execute(
                    select(
                        self.results.c.quest_name,
                        self.results.c.result,
                        self.results.c.error,
                        self.results.c.timestamp,
                    )
                )
                rows = result.all()
            return [tuple(row) for row in rows]
else:  # pragma: no cover - used when sqlalchemy is unavailable
    class AsyncResultDB:  # type: ignore
        """Placeholder for missing SQLAlchemy dependency."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            raise ImportError("SQLAlchemy is required for AsyncResultDB")
