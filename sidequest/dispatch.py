"""Utilities for dispatching quests to a message queue."""

from typing import Any, Dict, List, Set

from .quests import QuestContext


def _serialize(value: Any) -> Any:
    """Serialize arguments, converting result references to dictionaries."""
    if isinstance(value, QuestContext):
        return {"__ref__": value.id}
    if isinstance(value, (list, tuple)):
        return type(value)(_serialize(v) for v in value)
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _collect_messages(ctx: QuestContext, seen: Set[str]) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    deps: Set[str] = set()

    def handle(value: Any) -> None:
        if isinstance(value, QuestContext):
            messages.extend(_collect_messages(value, seen))
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
        messages.append(
            {
                "id": ctx.id,
                "quest": ctx.quest_name,
                "args": _serialize(ctx.args),
                "kwargs": _serialize(ctx.kwargs),
                "deps": list(deps),
            }
        )
        seen.add(ctx.id)

    return messages


async def dispatch(quest: QuestContext) -> None:
    """Asynchronously dispatch a quest and its dependencies."""
    queue = quest.queue
    messages = _collect_messages(quest, set())
    for message in messages:
        await queue.send(message)
