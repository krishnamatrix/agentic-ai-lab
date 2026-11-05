from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    id: str
    type: Literal[
        "fact",
        "preference",
        "decision",
        "goal",
        "constraint",
    ]
    scope: Literal["user", "conversation"] = "user"
    key: str
    value: str
    source: Literal["user", "assistant", "system"] = "user"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    user_id: str | None = None
    conversation_id: str | None = None
    source_message_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)