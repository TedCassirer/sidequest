"""Simple message queue abstraction."""

from queue import Queue
from typing import Any


class InMemoryQueue:
    """A basic in-memory queue using :class:`queue.Queue`."""

    def __init__(self) -> None:
        self._queue: Queue[Any] = Queue()

    def send(self, message: Any) -> None:
        self._queue.put(message)

    def receive(self) -> Any:
        return self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()
