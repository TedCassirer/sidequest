"""Simple SQLite-based result storage."""

from typing import Optional, Any, get_type_hints
from datetime import datetime

from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, \
    async_sessionmaker
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

    async def store(
        self,
        context_id: str,
        quest_name: str,
        result: Optional[Any],
        error: Optional[str],
    ) -> None:
        async with self.session_factory() as session:
            session.add(
                Result(
                    context_id=context_id,
                    quest_name=quest_name,
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
                    try:
                        result_type = get_type_hints(fn).get("return", Any)
                    except Exception:  # pragma: no cover - ignore typing issues
                        result_type = Any
                res = TypeAdapter(result_type).validate_json(res_json)
            else:
                res = None
            parsed.append((row[0], quest_name, res, row[3], row[4]))
        return parsed

    async def fetch_result(self, context_id: str) -> Optional[Any]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Result.result, Result.quest_name).where(Result.context_id == context_id)
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
                try:
                    result_type = get_type_hints(fn).get("return", Any)
                except Exception:  # pragma: no cover
                    result_type = Any
            return TypeAdapter(result_type).validate_json(value)
          
    async def teardown(self) -> None:
        """Drop all tables and dispose of the engine."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
