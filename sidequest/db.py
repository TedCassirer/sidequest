"""Simple SQLite-based result storage."""

from typing import Optional, Any, List
from datetime import datetime
import json

from sqlalchemy import String, select, update
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .quests import QUEST_REGISTRY

from pydantic import TypeAdapter


class Base(DeclarativeBase):
    """Declarative base class."""

    pass


class Result(Base):
    """ORM model representing stored quest results."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    context_id: Mapped[str] = mapped_column(String, unique=True)
    quest_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    deps: Mapped[str] = mapped_column(String)
    result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[str] = mapped_column(String)


class ResultDB:
    """Asynchronous database using SQLAlchemy."""

    def __init__(self, url: str = "sqlite+aiosqlite:///:memory:") -> None:
        self.engine: AsyncEngine = create_async_engine(url, future=True)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def setup(self) -> None:
        await self._init_tables()

    async def _init_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def register_task(
        self, context_id: str, quest_name: str, deps: List[str]
    ) -> None:
        """Insert a new task with ``PENDING`` status."""
        async with self.session_factory() as session:
            session.add(
                Result(
                    context_id=context_id,
                    quest_name=quest_name,
                    status="PENDING",
                    deps=json.dumps(deps),
                    result=None,
                    error=None,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
            await session.commit()

    async def mark_running(self, context_id: str) -> None:
        """Mark the given task as currently running."""
        async with self.session_factory() as session:
            await session.execute(
                update(Result)
                .where(Result.context_id == context_id)
                .values(status="RUNNING")
            )
            await session.commit()

    async def fetch_status(self, context_id: str) -> Optional[str]:
        """Return the status for the given task id."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Result.status).where(Result.context_id == context_id)
            )
            row = result.first()
            return row[0] if row is not None else None

    async def fetch_record(
        self, context_id: str
    ) -> Optional[tuple[str, str, Optional[str], List[str]]]:
        """Fetch the task entry for the given id."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(
                    Result.quest_name,
                    Result.status,
                    Result.error,
                    Result.deps,
                ).where(Result.context_id == context_id)
            )
            row = result.first()
            if row is None:
                return None
            quest_name, status, error, deps = row
            return quest_name, status, error, json.loads(deps)

    async def store(
        self,
        context_id: str,
        quest_name: str,
        result: Optional[Any],
        error: Optional[str],
        status: str,
    ) -> None:
        async with self.session_factory() as session:
            res = await session.execute(
                update(Result)
                .where(Result.context_id == context_id)
                .values(
                    result=None
                    if result is None
                    else TypeAdapter(Any).dump_json(result).decode(),
                    error=error,
                    status=status,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
            if res.rowcount == 0:
                session.add(
                    Result(
                        context_id=context_id,
                        quest_name=quest_name,
                        status=status,
                        deps=json.dumps([]),
                        result=None
                        if result is None
                        else TypeAdapter(Any).dump_json(result).decode(),
                        error=error,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )
            await session.commit()

    async def fetch_all(self) -> list[tuple]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(
                    Result.context_id,
                    Result.quest_name,
                    Result.result,
                    Result.error,
                    Result.timestamp,
                )
            )
            rows = result.all()
        parsed: list[tuple] = []
        for row in rows:
            quest_name = row[1]
            res_json = row[2]
            if res_json is not None:
                fn = QUEST_REGISTRY.get(quest_name)
                result_type = Any
                if fn is not None:
                    result_type = fn.return_type
                res = TypeAdapter(result_type).validate_json(res_json)
            else:
                res = None
            parsed.append((row[0], quest_name, res, row[3], row[4]))
        return parsed

    async def fetch_result(self, context_id: str) -> Optional[Any]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Result.result, Result.quest_name).where(
                    Result.context_id == context_id
                )
            )
            row = result.first()
            if row is None:
                return None
            value, quest_name = row[0], row[1]
            if value is None:
                return None
            fn = QUEST_REGISTRY.get(quest_name)
            result_type = Any
            if fn is not None:
                result_type = fn.return_type
            return TypeAdapter(result_type).validate_json(value)

    async def exists(self, context_id: str) -> bool:
        """Return ``True`` if a result entry with the given context id exists."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Result.id).where(
                    Result.context_id == context_id,
                    Result.status.in_(["SUCCESS", "FAILED"]),
                )
            )
            row = result.first()
            return row is not None

    async def teardown(self) -> None:
        """Drop all tables and dispose of the engine."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
