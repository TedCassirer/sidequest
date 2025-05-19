"""Utilities for dispatching quests to a message queue."""

from typing import Any, Dict

from .queue import InMemoryQueue


def dispatch(queue: InMemoryQueue, quest_name: str, *args: Any, **kwargs: Any) -> None:
    """Dispatch a quest to the provided queue."""
    message: Dict[str, Any] = {
        "quest": quest_name,
        "args": args,
        "kwargs": kwargs,
    }
    queue.send(message)
