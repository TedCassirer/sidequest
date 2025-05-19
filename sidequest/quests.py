"""Quest decorator and registry."""

from typing import Callable, Dict

QUEST_REGISTRY: Dict[str, Callable] = {}


def quest(fn: Callable) -> Callable:
    """Decorator to register a function as a quest."""
    QUEST_REGISTRY[fn.__name__] = fn
    return fn
