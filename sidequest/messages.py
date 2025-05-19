"""Models for SideQuest messages."""

from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel


class QuestMessage(BaseModel):
    """Message dispatched to workers."""

    id: str
    quest: str
    args: Any
    kwargs: Any
    deps: List[str] = []
