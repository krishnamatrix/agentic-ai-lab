from typing import Any
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    data: list[dict[str, Any]]
    count: int
    truncated: bool = False
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )
    message: str | None = None
