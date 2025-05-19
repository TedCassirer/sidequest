"""Sidequest task management library."""

from .quests import quest, QUEST_REGISTRY
from .dispatch import dispatch, adispatch
from .worker import Worker, AsyncWorker
from .queue import InMemoryQueue, AsyncInMemoryQueue
from .db import ResultDB, AsyncResultDB, SQLALCHEMY_AVAILABLE

__all__ = [
    "quest",
    "dispatch",
    "adispatch",
    "Worker",
    "AsyncWorker",
    "InMemoryQueue",
    "AsyncInMemoryQueue",
    "ResultDB",
]

if SQLALCHEMY_AVAILABLE:
    __all__.append("AsyncResultDB")
__all__.append("QUEST_REGISTRY")
