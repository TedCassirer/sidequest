"""Quest decorator and registry."""

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
    Optional,
    TypeVar,
    ParamSpec,
    Generic,
    cast,
    TypeAlias,
    Awaitable,
)
from uuid import uuid4

from .queue import InMemoryQueue


T_param = TypeVar("T_param")
T_result = TypeVar("T_result")

P_params = ParamSpec("P_params")
QuestImplementation: TypeAlias = Callable[P_params, Awaitable[T_result]]

QUEST_REGISTRY: Dict[str, "QuestWrapper"] = {}


@dataclass
class ResultRef(Generic[T_result]):
    """Reference to the result of another quest."""

    context_id: str
    context: Optional["QuestContext[T_result]"] = None


@dataclass
class QuestContext(Generic[T_result]):
    """Container for quest execution details."""

    quest_name: str
    queue: InMemoryQueue
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def cast(self) -> T_result:
        return cast(T_result, self)


@dataclass
class QuestWrapper(Generic[P_params, T_result]):
    """
    Wrapper around a quest implementation to provide extra functionalities to functions
    registered as quests
    """

    _func: QuestImplementation[P_params, T_result]
    _queue: InMemoryQueue

    def __call__(self, *args, **kwargs) -> QuestContext:
        """Invoke the quest with the given arguments."""
        return QuestContext(self._func.__name__, self._queue, args, kwargs)


def quest(
    *,
    queue: InMemoryQueue,
) -> Callable[
    [QuestImplementation[P_params, T_result]], QuestWrapper[P_params, T_result]
]:
    """Decorator to register a function as a quest."""

    def decorator(
        func: QuestImplementation[P_params, T_result],
    ) -> QuestWrapper[P_params, T_result]:
        quest_wrapper = QuestWrapper(func, queue)
        QUEST_REGISTRY[func.__name__] = quest_wrapper
        return quest_wrapper

    return decorator
