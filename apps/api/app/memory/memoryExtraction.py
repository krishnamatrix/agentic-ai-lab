from pydantic import BaseModel, Field
from typing import Literal


class ExtractedMemory(BaseModel):
    type: Literal[
        "fact",
        "preference",
        "decision",
        "goal",
        "constraint",
    ]

    key: str = Field(
        min_length=1,
        max_length=100,
    )

    value: str = Field(
        min_length=1,
        max_length=500,
    )

    scope: Literal["user", "conversation"]


class MemoryOperation(BaseModel):
    operation: Literal[
        "create",
        "update",
        "delete",
    ]

    memory: ExtractedMemory | None = None

    key: str | None = Field(
        default=None,
        max_length=100,
    )


class MemoryExtraction(BaseModel):
    operations: list[MemoryOperation] = Field(
        default_factory=list,
    )