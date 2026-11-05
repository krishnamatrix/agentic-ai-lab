from anyio import functools
from collections.abc import AsyncIterator
import json
import time
import uuid

import httpx

from app.llm.pricing import estimate_cost
from app.llm.types import LLMResponse

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:e4b"


class OllamaClient:
    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = DEFAULT_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format: str | dict | None = None,
        tools: list[dict] | None = None
    ) -> LLMResponse:
        request_id = str(uuid.uuid4())

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if tools is not None:
            payload["tools"] = tools

        if response_format is not None:
            payload["format"] = response_format

        start = time.perf_counter()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )

        latency_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()

        data = response.json()

        raw_tool_calls = (
            data.get("message", {})
                .get("tool_calls", [])
        )

        tool_calls = []

        for index, tool_call in enumerate(raw_tool_calls):
            function = tool_call.get(
                "function",
                {},
            )

            tool_calls.append(
                {
                    "id": tool_call.get(
                        "id",
                        f"call_{index+1}"
                    ),
                    "name": function.get("name"),
                    "arguments": function.get(
                        "arguments",
                        {},
                    ),
                }
            )

        input_tokens = data.get(
            "prompt_eval_count",
            0,
        )

        cached_input_tokens = data.get(
            "prompt_eval_cached_count",
            0,
        )

        output_tokens = data.get(
            "eval_count",
            0,
        )

        total_tokens = input_tokens + output_tokens

        model_load_ms = data.get("load_duration", 0) / 1_000_000

        prompt_eval_ms = data.get("prompt_eval_duration", 0) / 1_000_000

        generation_ms = data.get("eval_duration", 0) / 1_000_000

        end_to_end_tokens_per_second = None

        if latency_ms > 0 and output_tokens > 0:
            end_to_end_tokens_per_second = output_tokens / (latency_ms / 1000)

        generation_tokens_per_second = None

        if generation_ms > 0 and output_tokens > 0:
            generation_tokens_per_second = output_tokens / (generation_ms / 1000)

        estimated_cost = estimate_cost(
            input_tokens,
            output_tokens,
        )

        return LLMResponse(
            request_id=request_id,
            provider="ollama",
            model=self.model,
            content=data["message"]["content"],
            tool_calls=tool_calls,
            usage={
                "input_tokens": input_tokens,
                "cached_input_tokens": cached_input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_ms": round(
                    latency_ms,
                    2,
                ),
                "model_load_ms": round(
                    model_load_ms,
                    2,
                ),
                "prompt_eval_ms": round(
                    prompt_eval_ms,
                    2,
                ),
                "generation_ms": round(
                    generation_ms,
                    2,
                ),
                "end_to_end_tokens_per_second": (
                    round(
                        end_to_end_tokens_per_second,
                        2,
                    )
                    if end_to_end_tokens_per_second is not None
                    else None
                ),
                "generation_tokens_per_second": (
                    round(
                        generation_tokens_per_second,
                        2,
                    )
                    if generation_tokens_per_second is not None
                    else None
                ),
                "estimated_api_cost_usd": (estimated_cost),
            },
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                chunk_count = 0

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    data = json.loads(line)

                    if chunk_count < 10:
                        print(f"\nRAW CHUNK {chunk_count}:")
                        print(data)

                    chunk_count += 1

                    content = data.get(
                        "message",
                        {},
                    ).get(
                        "content",
                        "",
                    )

                    if content:
                        yield content

                    if data.get("done"):
                        break