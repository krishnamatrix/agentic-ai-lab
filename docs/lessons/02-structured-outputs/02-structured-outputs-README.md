# Lesson 2 --- Structured Outputs

## Purpose

This lesson teaches how to turn unreliable natural-language LLM output
into validated application data.

The implementation deliberately avoids LangChain/LangGraph so the
underlying mechanics remain visible.

## Learning sequence

``` text
02.1 Prompted JSON
02.2 Pydantic validation
02.3 Failure cases
02.4 Error boundaries
02.5 Schema-constrained generation
02.6 Schema validation
02.7 Semantic/domain validation
02.8 Retry/repair
02.9 Reusable StructuredLLM abstraction
```

## Prerequisites

Lesson 1 must be complete.

Expected local environment:

-   Python
-   `uv`
-   FastAPI project under `apps/api`
-   Ollama running locally
-   `gemma4:e4b` available
-   `httpx`
-   `pydantic`
-   pytest
-   Ruff

From `apps/api`:

``` bash
uv run ruff check .
uv run pytest
```

## Relevant files

``` text
apps/api/app/extraction/
├── __init__.py
├── models.py
├── naive.py
├── structured.py
└── validation.py
```

## Core model

`models.py`:

``` python
from pydantic import BaseModel, ConfigDict


class InteractionExtraction(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    person_name: str | None = None
    company_name: str | None = None
    interest: str | None = None
    next_action: str | None = None
    next_action_time: str | None = None
```

## Naive extraction

The first implementation asks the LLM to return JSON and then parses it:

``` python
response = await llm.chat(...)

data = json.loads(response.content)

result = InteractionExtraction.model_validate(data)
```

This establishes the basic application boundary.

## Structured generation

The Ollama client supports an optional response format:

``` python
response_format: str | dict | None = None
```

A Pydantic schema can be supplied:

``` python
schema = InteractionExtraction.model_json_schema()

response = await llm.chat(
    messages=[...],
    temperature=0.0,
    response_format=schema,
)
```

## Important experiment

The native/schema-constrained extraction path did not initially return a
useful response with the local Gemma/Ollama setup.

Do not treat this as a reason to block the course.

The intended architecture isolates this provider capability so that
prompted JSON + Pydantic remains a valid fallback.

Record provider-specific behavior in:

``` text
docs/experiments/
```

rather than baking assumptions into the application.

## Domain validation

Example:

``` python
def validate_interaction(
    interaction: InteractionExtraction,
) -> None:
    if (
        interaction.next_action == "demo"
        and not interaction.next_action_time
    ):
        raise ValueError(
            "A demo requires a next_action_time"
        )
```

Remember:

``` text
JSON valid
    ↓
Schema valid
    ↓
Domain valid
```

Each is a separate boundary.

## Retry policy

Retry candidates:

-   transport failures
-   malformed JSON
-   schema validation failures

Do not blindly retry:

-   missing source information
-   deterministic domain violations
-   authorization failures
-   application bugs

## Completion criteria

Lesson 2 is complete when you can explain and demonstrate:

-   prompted JSON
-   Pydantic validation
-   `extra="forbid"`
-   schema-constrained generation
-   domain validation
-   retry classification
-   structured-output abstraction
-   why structured outputs lead naturally to tool calls

## Transition to Lesson 3

The key conceptual transition is:

``` text
Lesson 1:
LLM → text

Lesson 2:
LLM → structured data

Lesson 3:
LLM → structured action
```
