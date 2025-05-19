"""Utilities for dispatching quests to a message queue."""

from typing import Any, Dict

from .quests import QuestContext


def dispatch(quest: QuestContext) -> None:
    """Dispatch a quest using the queue stored in the context."""
    queue = quest.queue
    quest_name = quest.quest_name
    args = quest.args
    kwargs = quest.kwargs
    message: Dict[str, Any] = {
        "quest": quest_name,
        "args": args,
        "kwargs": kwargs,
    }
    queue.send(message)


async def adispatch(quest: QuestContext) -> None:
    """Asynchronously dispatch a quest using the queue stored in the context."""
    queue = quest.queue
    quest_name = quest.quest_name
    args = quest.args
    kwargs = quest.kwargs
    message: Dict[str, Any] = {
        "quest": quest_name,
        "args": args,
        "kwargs": kwargs,
    }
    await queue.send(message)
