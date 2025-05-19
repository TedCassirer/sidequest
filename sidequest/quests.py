"""Quest decorator and registry."""

from dataclasses import dataclass, field
from inspect import Signature
from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
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
    _signature: Signature

    def __call__(self, *args: P_params.args, **kwargs: P_params.kwargs) -> QuestContext[T_result]:
        """Invoke the quest with the given arguments."""
        return QuestContext(self._func.__name__, self._queue, args, kwargs)

    async def accept(self, *args: P_params.args, **kwargs: P_params.kwargs) -> T_result:
        """Accept and execute the quest with the given arguments."""
        return await self._func(*args, **kwargs)

    @property
    def return_type(self) -> type:
        """Return the return type of the quest."""
        return self._signature.return_annotation


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
        quest_wrapper = QuestWrapper(func, queue, Signature.from_callable(func))
        QUEST_REGISTRY[func.__name__] = quest_wrapper
        return quest_wrapper

    return decorator
