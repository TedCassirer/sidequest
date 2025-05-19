"""Simple SQLite-based result storage."""

from typing import Optional, Any
from datetime import datetime

try:
    from sqlalchemy import Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        async_sessionmaker,
        create_async_engine,
    )
    SQLALCHEMY_AVAILABLE = True
except Exception:  # pragma: no cover - sqlalchemy may not be installed
    SQLALCHEMY_AVAILABLE = False




if SQLALCHEMY_AVAILABLE:
    class Base(DeclarativeBase):
        """Declarative base for ORM models."""

    class Result(Base):
        """ORM model representing stored quest results."""

        __tablename__ = "results"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        quest_name: Mapped[str] = mapped_column(String)
        result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        timestamp: Mapped[str] = mapped_column(String)


    class AsyncResultDB:
        """Asynchronous database using SQLAlchemy."""

        def __init__(self, url: str = "sqlite+aiosqlite:///:memory:") -> None:
            self.engine: AsyncEngine = create_async_engine(url, future=True)
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

            import asyncio

            asyncio.run(self._init_tables())

        async def _init_tables(self) -> None:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        async def store(self, quest_name: str, result: Optional[Any], error: Optional[str]) -> None:
            async with self.session_factory() as session:
                session.add(
                    Result(
                        quest_name=quest_name,
                        result=None if result is None else str(result),
                        error=error,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )
                await session.commit()

        async def fetch_all(self) -> list[tuple]:
            async with self.session_factory() as session:
                result = await session.execute(
                    select(
                        Result.quest_name,
                        Result.result,
                        Result.error,
                        Result.timestamp,
                    )
                )
                rows = result.all()
            return [tuple(row) for row in rows]
else:  # pragma: no cover - used when sqlalchemy is unavailable
    class AsyncResultDB:  # type: ignore
        """Placeholder for missing SQLAlchemy dependency."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            raise ImportError("SQLAlchemy is required for AsyncResultDB")
