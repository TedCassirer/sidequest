"""Quest decorator and registry."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Tuple, Optional

from .queue import AsyncInMemoryQueue
from functools import wraps

QUEST_REGISTRY: Dict[str, Callable] = {}


@dataclass
class QuestContext:
    """Container for quest execution details."""

    quest_name: str
    queue: AsyncInMemoryQueue
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)


def quest(
    fn: Optional[Callable] = None,
    *,
    queue: Optional[AsyncInMemoryQueue] = None,
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
