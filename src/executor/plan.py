from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionPlan:
    sheet: str
    operation: str
    column: str | None = None
    filters: list[dict[str, Any]] | None = None
    query: str | None = None