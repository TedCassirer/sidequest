"""Utilities for dispatching quests to a message queue."""

from typing import Any, Dict, List, Set

from .quests import QuestContext
from .db import ResultDB
from .runtime import ACTIVE_WORKFLOW, WORKFLOW_MAP


def _serialize(value: Any) -> Any:
    """Serialize arguments, converting result references to dictionaries."""
    if isinstance(value, QuestContext):
        return {"__ref__": value.id}
    if isinstance(value, (list, tuple)):
        return type(value)(_serialize(v) for v in value)
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _collect_messages(
    ctx: QuestContext, workflow_id: str | None, seen: Set[str]
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    deps: Set[str] = set()

    def handle(value: Any) -> None:
        if isinstance(value, QuestContext):
            messages.extend(_collect_messages(value, workflow_id, seen))
            deps.add(value.id)
        elif isinstance(value, (list, tuple)):
            for v in value:
                handle(v)
        elif isinstance(value, dict):
            for v in value.values():
                handle(v)

    for arg in ctx.args:
        handle(arg)
    for arg in ctx.kwargs.values():
        handle(arg)

    if ctx.id not in seen:
        msg = {
            "id": ctx.id,
            "quest": ctx.quest_name,
            "args": _serialize(ctx.args),
            "kwargs": _serialize(ctx.kwargs),
            "deps": list(deps),
        }
        if workflow_id is not None:
            msg["wf"] = workflow_id
        messages.append(msg)
        seen.add(ctx.id)

    return messages


def _collect_contexts(ctx: QuestContext, seen: Set[str]) -> List[QuestContext]:
    """Return quest contexts reachable from ``ctx``."""
    contexts: List[QuestContext] = []

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


async def dispatch(quest: QuestContext, db: ResultDB | None = None) -> None:
    """Asynchronously dispatch a quest and its dependencies."""
    queue = quest.queue
    workflow_id = ACTIVE_WORKFLOW.get(None)
    messages = _collect_messages(quest, workflow_id, set())
    if workflow_id is not None:
        wf_obj = WORKFLOW_MAP.get(workflow_id)
        if wf_obj is not None:
            for ctx in _collect_contexts(quest, set()):
                wf_obj.add_context(ctx)
    if db is not None:
        for msg in messages:
            await db.register_task(
                msg["id"], msg["quest"], msg.get("deps", []), msg.get("wf")
            )
    for message in messages:
        await queue.send(message)
