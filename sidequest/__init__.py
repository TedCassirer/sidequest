"""Sidequest task management library."""

from .quests import quest, QUEST_REGISTRY, QuestContext
from .dispatch import adispatch
from .worker import AsyncWorker
from .queue import AsyncInMemoryQueue
from .db import AsyncResultDB, SQLALCHEMY_AVAILABLE

__all__ = [
    "quest",
    "adispatch",
    "AsyncWorker",
    "AsyncInMemoryQueue",
    "QuestContext",
]

if SQLALCHEMY_AVAILABLE:
    __all__.append("AsyncResultDB")
__all__.append("QUEST_REGISTRY")
