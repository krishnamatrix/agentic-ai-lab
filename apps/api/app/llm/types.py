from pydantic import BaseModel, Field
from typing import Any

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]

class LLMUsage(BaseModel):
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int

    latency_ms: float

    model_load_ms: float
    prompt_eval_ms: float
    generation_ms: float
    
    time_to_first_token_ms: float | None = None

    end_to_end_tokens_per_second: float | None = None
    generation_tokens_per_second: float | None = None

    estimated_api_cost_usd: float = 0.0


class LLMResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    content: str
    tool_calls: list[ToolCall] = Field(
        default_factory = list
    )
    usage: LLMUsage
