"""Quest decorator and registry."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Tuple, Optional
from uuid import uuid4

from .queue import InMemoryQueue
from functools import wraps

QUEST_REGISTRY: Dict[str, Callable] = {}


@dataclass
class ResultRef:
    """Reference to the result of another quest."""

    context_id: str
    context: Optional["QuestContext"] = None

@dataclass
class QuestContext:
    """Container for quest execution details."""

    quest_name: str
    queue: InMemoryQueue
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def cast(self) -> ResultRef:
        """Return a reference to this context's result."""
        return ResultRef(self.id, self)


def quest(
    fn: Optional[Callable] = None,
    *,
    queue: Optional[InMemoryQueue] = None,
) -> Callable:
    """Decorator to register a function as a quest."""

    def decorator(func: Callable) -> Callable:
        QUEST_REGISTRY[func.__name__] = func

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> QuestContext:
            return QuestContext(func.__name__, queue, args, kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)

    return decorator
