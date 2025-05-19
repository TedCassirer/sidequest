"""Worker implementation to execute quests from a queue."""

from typing import Any, Dict
import traceback

from .queue import InMemoryQueue
from .quests import QUEST_REGISTRY
from .db import ResultDB




class Worker:
    """Asynchronous worker that consumes quests from a queue."""

    def __init__(self, queue: InMemoryQueue, db: ResultDB) -> None:
        self.queue = queue
        self.db = db

    async def run_once(self) -> None:
        """Process a single quest if available."""
        if self.queue.empty():
            return
        message: Dict[str, Any] = await self.queue.receive()
        quest_name: str = message["quest"]
        args = message.get("args", [])
        kwargs = message.get("kwargs", {})
        fn = QUEST_REGISTRY.get(quest_name)
        if not fn:
            await self.db.store(quest_name, None, f"Unknown quest: {quest_name}")
            return
        try:
            import inspect

            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            await self.db.store(quest_name, result, None)
        except Exception:  # pylint: disable=broad-except
            tb = traceback.format_exc()
            await self.db.store(quest_name, None, tb)

    async def run_forever(self) -> None:
        """Continuously process quests until queue is empty."""
        while not self.queue.empty():
            await self.run_once()
