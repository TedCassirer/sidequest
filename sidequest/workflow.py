"""Workflow utilities for groups of dependent quests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, List, Set, TypeVar

from .quests import QuestContext
from .dispatch import dispatch
from .db import ResultDB

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
        await dispatch(self.root, db)

    async def result(self, db: ResultDB) -> T_result | None:
        """Fetch the result of the root quest from the database."""
        return await db.fetch_result(self.root.id)

    async def statuses(self, db: ResultDB) -> List[tuple[str, str, str]]:
        """Return ``(id, quest_name, status)`` for all quests in the workflow."""
        states: List[tuple[str, str, str]] = []
        for ctx in self.contexts():
            record = await db.fetch_record(ctx.id)
            if record is None:
                continue
            quest_name, status, _err, deps = record
            if status == "PENDING":
                waiting = False
                for dep in deps:
                    dep_status = await db.fetch_status(dep)
                    if dep_status not in ("SUCCESS", "FAILED"):
                        waiting = True
                        break
                status = "WAITING" if waiting else "PENDING"
            states.append((ctx.id, quest_name, status))
        return states
