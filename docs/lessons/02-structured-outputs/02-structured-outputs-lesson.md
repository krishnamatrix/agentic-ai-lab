# Lesson 2 --- Structured Outputs

## Overview

In Lesson 1, the LLM returned natural-language text. That is useful for
conversation, but application code needs reliable data structures.

This lesson introduces structured outputs and establishes an important
application boundary:

``` text
LLM
 ↓
JSON text
 ↓
Parse
 ↓
Pydantic validation
 ↓
Domain validation
 ↓
Application
```

The goal is not merely to make an LLM return JSON. The goal is to
understand the difference between:

-   syntactically valid JSON
-   schema-valid data
-   semantically valid domain data
-   reliable application behavior

We deliberately implement these mechanisms without LangChain or another
LLM framework.

------------------------------------------------------------------------

## Learning objectives

By the end of this lesson, you should understand:

1.  Why free-form LLM output is difficult for application code.
2.  How prompted JSON differs from schema-constrained generation.
3.  How Pydantic provides an application-level validation boundary.
4.  Why valid JSON does not imply valid business data.
5.  The difference between schema validation and semantic/domain
    validation.
6.  Which failures are appropriate for retry/repair.
7.  Why deterministic domain failures should not blindly trigger LLM
    retries.
8.  How to build a reusable `StructuredLLM` abstraction.
9.  Why structured outputs are conceptually related to future tool
    calls.

------------------------------------------------------------------------

# 1. The problem with free-form output

Suppose we ask:

> Extract CRM information from this interaction.

A model may return:

``` text
John from Acme Corp is interested in the enterprise plan.
They want a demo next week.
```

A human can understand this.

Python cannot safely assume a structure.

We want:

``` json
{
  "person_name": "John",
  "company_name": "Acme Corp",
  "interest": "enterprise plan",
  "next_action": "demo",
  "next_action_time": "next week"
}
```

This gives application code something deterministic to parse.

------------------------------------------------------------------------

# 2. First approach --- prompted JSON

Our first implementation uses a normal LLM request with explicit
instructions:

``` text
Return ONLY valid JSON.
Do not use markdown.
Do not add explanations.

The JSON must contain exactly these fields:
...
```

The important observation is that this is still just a prompt.

The model is being asked to follow a convention.

It is not a guarantee.

Conceptually:

``` text
LLM
 ↓
text
 ↓
json.loads()
```

Implementation:

``` python
import json

response = await llm.chat(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    temperature=0.0,
)

data = json.loads(response.content)
```

This works when the model complies, but the application still needs to
handle malformed or unexpected output.

------------------------------------------------------------------------

# 3. Pydantic as the application boundary

We define the expected structure explicitly:

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

Now the pipeline becomes:

``` text
LLM
 ↓
JSON
 ↓
Pydantic
 ↓
InteractionExtraction
```

Instead of:

``` python
data = json.loads(response.content)
```

we can use:

``` python
data = json.loads(response.content)

result = InteractionExtraction.model_validate(data)
```

Or, when the response is JSON text:

``` python
result = InteractionExtraction.model_validate_json(
    response.content
)
```

The important principle is:

> The LLM proposes data. The application validates it.

The LLM is not the authority on whether the data is acceptable.

------------------------------------------------------------------------

# 4. Schema validation is not semantic validation

Consider:

``` json
{
  "person_name": "John",
  "company_name": "Acme Corp",
  "interest": "enterprise plan",
  "next_action": "demo",
  "next_action_time": null
}
```

This can be perfectly valid according to the Pydantic schema.

Every field has an allowed type.

But the application may have a business rule:

> A demo must have a scheduled time.

That is a different kind of validation.

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

Therefore:

``` text
Schema validation
    ≠
Domain validation
```

This distinction becomes increasingly important as our agent gains
access to real CRM data.

------------------------------------------------------------------------

# 5. Extra fields

We use:

``` python
ConfigDict(extra="forbid")
```

because unexpected fields can indicate that the model produced
information outside the contract.

For example:

``` json
{
  "person_name": "John",
  "company_name": "Acme Corp",
  "secret_field": "unexpected"
}
```

With `extra="forbid"`, this fails validation.

This makes the boundary explicit rather than silently accepting model
drift.

------------------------------------------------------------------------

# 6. Schema-constrained generation

Ollama supports structured generation through the `format` request
field.

Our LLM client therefore accepts:

``` python
response_format: str | dict | None = None
```

and adds:

``` python
if response_format is not None:
    payload["format"] = response_format
```

A Pydantic schema can be supplied:

``` python
schema = InteractionExtraction.model_json_schema()

response = await llm.chat(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    temperature=0.0,
    response_format=schema,
)
```

The conceptual difference is:

``` text
Prompted JSON:

LLM → "please return JSON"

Schema constrained:

LLM → generate according to supplied schema
```

This moves part of the structural constraint closer to generation.

However, application validation is still required.

------------------------------------------------------------------------

# 7. An experiment that did not work cleanly

During this lesson, the schema-constrained `StructuredExtractor` did not
initially return a useful response with our local Gemma/Ollama
configuration.

Rather than hiding that failure, we treat it as an experiment.

The lesson is:

> Provider/model support for structured generation is an implementation
> detail that must be tested, not assumed.

Our architecture therefore keeps the structured-output mechanism behind
an abstraction.

We can continue using prompted JSON + Pydantic while separately testing
native schema-constrained generation.

This prevents a provider-specific feature from becoming a prerequisite
for the rest of the course.

------------------------------------------------------------------------

# 8. Retry and repair

Structured generation can fail for several reasons:

### Generation failure

The model did not produce usable JSON.

Potentially retry.

### Parsing failure

``` python
json.loads(...)
```

failed.

Potentially retry.

### Schema validation failure

The JSON is valid, but does not match the expected model.

Potentially retry.

### Domain validation failure

The structure is valid, but the business data is invalid.

Do not blindly retry.

For example:

``` text
LLM:
next_action = "demo"
next_action_time = null

Pydantic:
VALID

Domain validation:
INVALID
```

If the source text never supplied a meeting time, repeatedly asking the
LLM to generate one does not solve the problem.

The correct response may be:

``` text
next_action_time = unknown
```

or require a user/application workflow.

------------------------------------------------------------------------

# 9. A reusable StructuredLLM abstraction

Once the mechanism is understood, we can hide the transport details.

Conceptually:

``` python
class StructuredLLM:
    async def generate(
        self,
        prompt: str,
        output_model: type[T],
    ) -> T:
        ...
```

The caller should only need to specify:

``` python
result = await structured_llm.generate(
    prompt=prompt,
    output_model=InteractionExtraction,
)
```

The abstraction owns:

-   schema generation
-   LLM invocation
-   JSON parsing
-   Pydantic validation
-   retry policy
-   structured-output errors

The domain layer owns:

-   what information to extract
-   what the information means
-   domain-specific validation

This is separation of concerns.

------------------------------------------------------------------------

# 10. Error boundaries

A useful hierarchy is:

``` text
LLM transport failure
        ↓
Structured generation failure
        ↓
JSON parsing failure
        ↓
Schema validation failure
        ↓
Domain validation failure
```

Do not collapse these into one generic exception.

Different failures imply different recovery strategies.

For example:

``` text
network timeout
    → retry

invalid JSON
    → retry/repair

invalid schema
    → retry/repair

missing required business information
    → application/user workflow
```

------------------------------------------------------------------------

# 11. Why this matters for agents

Structured output is not a separate concept from tool calling.

A tool request is itself structured data.

For example:

``` json
{
  "name": "search_people",
  "arguments": {
    "company_name": "Acme Corporation"
  }
}
```

The model is producing a structured instruction that the application
must validate.

So the progression is:

``` text
Lesson 1
LLM → text

Lesson 2
LLM → structured data

Lesson 3
LLM → structured action
```

This is why structured-output work belongs immediately before tool
calling.

------------------------------------------------------------------------

# 12. Engineering principles

The main lessons are:

### 1. JSON is not validation

Valid JSON only means the syntax is valid.

### 2. Schema is not business logic

Pydantic validates structure and types.

Domain validators enforce business rules.

### 3. The application owns correctness

The model proposes.

The application decides.

### 4. Retries need classification

Not every failure should trigger another model call.

### 5. Provider features should be isolated

Native structured generation is useful, but it should not leak through
the application architecture.

### 6. Structured output is a stepping stone to tool calling

Tool calls are structured outputs with executable consequences.

------------------------------------------------------------------------

# 13. Resulting architecture

After Lesson 2:

``` text
                 ┌─────────────┐
                 │     LLM     │
                 └──────┬──────┘
                        │
                     JSON
                        │
                        ▼
                ┌──────────────┐
                │    Parser    │
                └──────┬───────┘
                       │
                  Pydantic
                       │
                       ▼
                ┌──────────────┐
                │    Domain    │
                │  Validation  │
                └──────┬───────┘
                       │
                       ▼
                 Application
```

The next lesson turns the structured output into an executable action:

``` text
LLM
 ↓
Tool Call
 ↓
Application
 ↓
Tool
 ↓
Tool Result
 ↓
LLM
```

That is the beginning of the agent loop.
