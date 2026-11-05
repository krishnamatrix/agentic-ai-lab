from pydantic import Field
from pydantic import BaseModel
from typing import Literal

from app.memory.memoryExtraction import ExtractedMemory

class MemoryOperation(BaseModel):
    operation: Literal["create", "update", "delete"]
    memory: ExtractedMemory | None = None

    key: str | None = Field(
        default=None,
        max_length=100,
    )