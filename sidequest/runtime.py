from contextvars import ContextVar
from typing import Any, Dict

# ID of the currently active workflow during quest execution
ACTIVE_WORKFLOW: ContextVar[str | None] = ContextVar("ACTIVE_WORKFLOW", default=None)

# Mapping of workflow ids to their associated workflow object. Only valid within
# the current process.
WORKFLOW_MAP: Dict[str, Any] = {}
