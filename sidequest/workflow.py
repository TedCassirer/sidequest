"""Workflow utilities for groups of dependent quests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, List, Set, TypeVar

from .quests import QuestContext
from .dispatch import dispatch
from .db import ResultDB, QuestStatus

T_result = TypeVar("T_result")


def _collect_contexts(
    ctx: QuestContext[Any],
    seen: Set[str],
) -> List[QuestContext[Any]]:
    """Recursively gather quest contexts, deduplicating by id."""
    contexts: List[QuestContext[Any]] = []

    def handle(value: Any) -> None:
        if isinstance(value, QuestContext):
            contexts.extend(_collect_contexts(value, seen))

    for arg in ctx.args:
        handle(arg)
    for arg in ctx.kwargs.values():
        handle(arg)

    if ctx.id not in seen:
        contexts.append(ctx)
        seen.add(ctx.id)

    return contexts


@dataclass
class Workflow(Generic[T_result]):
    """Collection of quests that form a workflow."""

    root: QuestContext[T_result]

    def contexts(self) -> List[QuestContext[Any]]:
        """Return all quest contexts in the workflow."""
        return _collect_contexts(self.root, set())

    async def dispatch(self, db: ResultDB | None = None) -> None:
        """Dispatch all quests in the workflow."""
        if db is not None:
            for ctx in self.contexts():
                await db.register(ctx.id, ctx.quest_name)
        await dispatch(self.root)

    async def status(self, db: ResultDB) -> dict[str, str | None]:
        """Return the execution status of all quests."""
        states = {}
        for ctx in self.contexts():
            states[ctx.quest_name] = await db.fetch_status(ctx.id)
        return states

    async def failed_quests(self, db: ResultDB) -> list[str]:
        """Return names of quests that have failed."""
        failed: list[str] = []
        for ctx in self.contexts():
            if await db.fetch_status(ctx.id) == QuestStatus.FAILED.value:
                failed.append(ctx.quest_name)
        return failed

    async def result(self, db: ResultDB) -> T_result | None:
        """Fetch the result of the root quest from the database."""
        return await db.fetch_result(self.root.id)
