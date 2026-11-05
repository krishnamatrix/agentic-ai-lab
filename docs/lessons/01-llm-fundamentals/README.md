# Lesson 1 — LLM Fundamentals: Hands-on Lab Guide

## Objective

In this lesson we make our first local LLM call using:

* Python
* FastAPI
* `httpx`
* Ollama
* Gemma 4 `gemma4:e4b`

We deliberately do **not** use LangChain, LangGraph, an agent framework, or an Ollama SDK.

The objective is to understand the underlying request/response lifecycle before introducing abstractions.

We will also introduce the first version of our LLM Gateway with:

* model configuration
* request IDs
* token usage
* latency measurement
* tokens/second
* estimated API-equivalent cost
* error handling

---

# 1. Verify Ollama

Run:

```bash
ollama list
```

Confirm that the model exists:

```text
gemma4:e4b
```

Then verify the Ollama API:

```bash
curl http://localhost:11434/api/tags
```

You should receive JSON describing the installed models.

---

# 2. Test Gemma directly

Before involving our application, verify that Ollama itself works:

```bash
ollama run gemma4:e4b
```

Ask:

```text
Explain what a CRM is in one sentence.
```

Then exit:

```text
/bye
```

This establishes an important debugging principle:

> Always verify the underlying dependency independently before debugging your application integration.

---

# 3. Install the HTTP client

From:

```text
apps/api
```

run:

```bash
uv add httpx
```

Verify:

```bash
uv run python -c "import httpx; print(httpx.__version__)"
```

---

# 4. Create the LLM package

Create:

```text
apps/api/app/llm/
├── __init__.py
├── types.py
├── pricing.py
└── ollama.py
```

Run:

```bash
mkdir -p app/llm
touch app/llm/__init__.py
touch app/llm/types.py
touch app/llm/pricing.py
touch app/llm/ollama.py
```

---

# 5. Define the LLM response model

Create:

```text
app/llm/types.py
```

```python
from pydantic import BaseModel


class LLMUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    tokens_per_second: float | None = None
    estimated_api_cost_usd: float = 0.0


class LLMResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    content: str
    usage: LLMUsage
```

This is our first important abstraction.

The application should not need to know that Ollama calls its usage fields `prompt_eval_count` and `eval_count`.

Our internal representation is:

```text
input_tokens
output_tokens
total_tokens
```

This will allow us to support other providers later.

---

# 6. Create the pricing registry

Create:

```text
app/llm/pricing.py
```

For Lesson 1 we use a **benchmark pricing profile**.

This is not the actual cost of running Gemma locally.

```python
BENCHMARK_INPUT_PRICE_PER_1M = 0.50
BENCHMARK_OUTPUT_PRICE_PER_1M = 1.50


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
) -> float:
    input_cost = (
        input_tokens / 1_000_000
    ) * BENCHMARK_INPUT_PRICE_PER_1M

    output_cost = (
        output_tokens / 1_000_000
    ) * BENCHMARK_OUTPUT_PRICE_PER_1M

    return input_cost + output_cost
```

The purpose is to answer:

> "What would this workload cost if it were charged using this benchmark token price?"

It is intentionally **not** presented as Ollama's actual pricing.

---

# 7. Implement the Ollama adapter

Create:

```text
app/llm/ollama.py
```

```python
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

        start = time.perf_counter()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        response.raise_for_status()

        data = response.json()

        input_tokens = data.get(
            "prompt_eval_count",
            0,
        )

        output_tokens = data.get(
            "eval_count",
            0,
        )

        total_tokens = (
            input_tokens + output_tokens
        )

        tokens_per_second = None

        if latency_ms > 0 and output_tokens > 0:
            tokens_per_second = (
                output_tokens
                / (latency_ms / 1000)
            )

        estimated_cost = estimate_cost(
            input_tokens,
            output_tokens,
        )

        return LLMResponse(
            request_id=request_id,
            provider="ollama",
            model=self.model,
            content=data["message"]["content"],
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_ms": round(
                    latency_ms,
                    2,
                ),
                "tokens_per_second": (
                    round(
                        tokens_per_second,
                        2,
                    )
                    if tokens_per_second
                    is not None
                    else None
                ),
                "estimated_api_cost_usd": (
                    estimated_cost
                ),
            },
        )
```

---

# 8. Create a simple test script

Create:

```text
apps/api/scripts/test_llm.py
```

First create the directory:

```bash
mkdir -p scripts
touch scripts/test_llm.py
```

Add:

```python
import asyncio

from app.llm.ollama import OllamaClient


async def main():
    client = OllamaClient()

    result = await client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    "Explain what a CRM is "
                    "in one sentence."
                ),
            }
        ]
    )

    print("\nResponse:")
    print(result.content)

    print("\nMetadata:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
uv run python -m scripts.test_llm
```

You should receive a response followed by metadata similar to:

```json
{
  "request_id": "...",
  "provider": "ollama",
  "model": "gemma4:e4b",
  "content": "...",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 30,
    "total_tokens": 45,
    "latency_ms": 1250.42,
    "tokens_per_second": 23.99,
    "estimated_api_cost_usd": 0.0000525
  }
}
```

The exact numbers will vary.

---

# 9. Understand the Ollama response

The important fields are:

```text
prompt_eval_count
eval_count
total_duration
prompt_eval_duration
eval_duration
```

We translate provider-specific information into our own model:

```text
Ollama
    │
    ├── prompt_eval_count
    │       ↓
    │   input_tokens
    │
    └── eval_count
            ↓
        output_tokens
```

This is an intentional abstraction boundary.

Our application should not become dependent on Ollama's terminology.

---

# 10. Experiment 1 — Same prompt

Run the script three times:

```bash
uv run python scripts/test_llm.py
```

Record:

```text
input_tokens
output_tokens
latency_ms
tokens_per_second
estimated_api_cost_usd
```

Create:

```text
docs/experiments/lesson-01-basic-generation.md
```

Record the results.

The exact values are expected to differ because:

* hardware state changes
* model loading can affect latency
* operating-system scheduling changes
* generated output can differ

---

# 11. Experiment 2 — Temperature

Change:

```python
temperature=0.0
```

Then run the same prompt several times.

Compare with:

```python
temperature=0.7
```

Then:

```python
temperature=1.0
```

Observe:

* response variability
* output length
* token usage
* latency

Do not assume that higher temperature automatically means "better."

Temperature controls the sampling behavior of generation.

---

# 12. Experiment 3 — Token economics

Try progressively larger prompts.

For example:

```text
Explain CRM.
```

Then:

```text
Explain CRM systems used by enterprise sales organizations.
```

Then provide a substantially longer CRM scenario.

Record:

```text
input_tokens
output_tokens
total_tokens
estimated_api_cost_usd
```

The goal is to observe:

```text
More context
    ↓
More input tokens
    ↓
More computational work
    ↓
Potentially higher latency
    ↓
Potentially higher cost
```

---

# 13. Experiment 4 — Output length

Ask:

```text
Give me a one-sentence explanation of CRM.
```

Then:

```text
Give me a detailed explanation of CRM.
```

Compare:

```text
output_tokens
latency
tokens_per_second
estimated_cost
```

This demonstrates why output generation is an important part of LLM economics.

---

# 14. Experiment 5 — Failure: invalid model

Temporarily change:

```python
DEFAULT_MODEL = "model-that-does-not-exist"
```

Run:

```bash
uv run python scripts/test_llm.py
```

Observe the failure.

Then restore:

```python
DEFAULT_MODEL = "gemma4:e4b"
```

This is our first reliability experiment.

Do not immediately hide failures behind generic error messages.

At this stage we want to understand the raw failure.

---

# 15. Experiment 6 — Ollama unavailable

Stop Ollama.

Then run:

```bash
uv run python scripts/test_llm.py
```

Observe what happens.

This is different from:

```text
model not found
```

and different again from:

```text
request timeout
```

We will eventually distinguish:

```text
provider unavailable
model unavailable
request timeout
invalid request
provider error
```

---

# 16. Run quality checks

After implementation:

```bash
uv run ruff format .
```

Then:

```bash
uv run ruff check .
```

Then:

```bash
uv run pytest
```

All three should pass.

---

# 17. Git checkpoint

Inspect:

```bash
git status
```

Then:

```bash
git add .
git commit -m "feat: add local LLM gateway"
```

This commit represents our first working LLM integration.

---

# 18. What we deliberately did not build yet

We are **not** adding:

* LangChain
* LangGraph
* agents
* tools
* RAG
* embeddings
* vector databases
* memory
* prompt templates
* multi-agent systems
* MCP

Those come later.

The purpose of this lesson is to understand the primitive underneath all of them:

```text
messages
   ↓
LLM inference
   ↓
generated tokens
   ↓
response
```

---

# Completion criteria

Lesson 1 is complete when:

* [ ] Ollama is running locally
* [ ] `gemma4:e4b` responds
* [ ] Python can call Ollama
* [ ] The response is represented by our own `LLMResponse`
* [ ] Input tokens are captured
* [ ] Output tokens are captured
* [ ] Total tokens are calculated
* [ ] Latency is measured
* [ ] Tokens/second is calculated
* [ ] Benchmark cost is calculated
* [ ] Request IDs are generated
* [ ] Invalid-model behavior has been observed
* [ ] Ollama-unavailable behavior has been observed
* [ ] Ruff passes
* [ ] pytest passes
* [ ] The implementation is committed to Git

Only after this do we move to streaming and the deeper internals of generation.
