"""Worker implementations to execute quests from a queue."""

from __future__ import annotations

from typing import Any, Dict
from abc import ABC, abstractmethod
import asyncio
import traceback

from .queue import InMemoryQueue
from .quests import QUEST_REGISTRY, QuestWrapper
from .db import ResultDB


class BaseWorker(ABC):
    """Base class for workers that consume quests from a queue."""

    def __init__(self, queue: InMemoryQueue, db: ResultDB) -> None:
        self.queue = queue
        self.db = db
        self._stop = False

    def stop(self) -> None:
        """Signal the worker to stop processing quests."""
        self._stop = True

    async def run_once(self) -> None:
        """Process a single quest if available."""
        if self.queue.empty():
            return
        message: Dict[str, Any] = await self.queue.receive()
        await self.handle_message(message)

    async def run_forever(self) -> None:
        """Continuously process quests until :meth:`stop` is called."""
        while not self._stop:
            await self.run_once()
            if self.queue.empty():
                await self.on_idle()

    async def on_idle(self) -> None:
        """Hook invoked when the worker has no quests to process."""
        await asyncio.sleep(0)

    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle a single quest message."""


class Worker(BaseWorker):
    """Default worker implementation that executes quests.

    Multiple workers can operate on the same queue concurrently. A worker will
    postpone execution of a quest until all of its dependencies have been
    processed.
    """

    async def execute_quest(
        self,
        quest: QuestWrapper[Any, Any],
        args: Any,
        kwargs: Any,
    ) -> Any:
        """Execute the quest function. Subclasses may override."""

        return await quest.accept(*args, **kwargs)

    async def handle_message(self, message: Dict[str, Any]) -> None:
        quest_name: str = message["quest"]
        context_id: str = message["id"]
        deps = message.get("deps", [])
        args = message.get("args", [])
        kwargs = message.get("kwargs", {})
        fn = QUEST_REGISTRY.get(quest_name)
        if not fn:
            await self.db.store(
                context_id, quest_name, None, f"Unknown quest: {quest_name}"
            )
            return
        try:
            for dep in deps:
                if not await self.db.exists(dep):
                    await self.queue.send(message)
                    await asyncio.sleep(0)
                    return

            async def resolve(value: Any) -> Any:
                if isinstance(value, dict) and "__ref__" in value:
                    return await self.db.fetch_result(value["__ref__"])
                if isinstance(value, list):
                    return [await resolve(v) for v in value]
                if isinstance(value, tuple):
                    return tuple([await resolve(v) for v in value])
                if isinstance(value, dict):
                    return {k: await resolve(v) for k, v in value.items()}
                return value

            args = await resolve(args)
            kwargs = await resolve(kwargs)
            result = await self.execute_quest(fn, args, kwargs)
            await self.db.store(context_id, quest_name, result, None)
        except Exception:  # pylint: disable=broad-except
            tb = traceback.format_exc()
            await self.db.store(context_id, quest_name, None, tb)

