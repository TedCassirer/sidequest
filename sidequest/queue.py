"""Simple message queue abstraction."""

from typing import Any

import asyncio


class InMemoryQueue:
    """Asynchronous in-memory queue using :class:`asyncio.Queue`."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Any] = asyncio.Queue()

    async def send(self, message: Any) -> None:
        await self._queue.put(message)

    async def receive(self) -> Any:
        return await self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()
