# Lesson 3 --- Tool Calling and the Agent Loop

## Purpose

This lesson teaches the mechanics behind tool-using agents without
relying on LangChain, LangGraph, or another agent framework.

The target architecture is:

``` text
User
 ↓
LLM
 ↓
Tool call
 ↓
Application
 ↓
Tool
 ↓
Tool result
 ↓
LLM
 ↓
Final answer
```

## Prerequisites

Lesson 1 and Lesson 2 should be complete.

Expected environment:

-   Python
-   `uv`
-   Ollama
-   `gemma4:e4b`
-   `httpx`
-   Pydantic
-   pytest
-   Ruff

From `apps/api`:

``` bash
uv run ruff check .
uv run pytest
```

## Relevant files

``` text
apps/api/app/
├── agents/
│   ├── __init__.py
│   ├── simple_agent.py
│   └── tool_executor.py
│
├── llm/
│   ├── ollama.py
│   └── types.py
│
└── tools/
    ├── __init__.py
    ├── crm.py
    ├── definitions.py
    └── registry.py
```

Test script:

``` text
apps/api/scripts/test_tool_call.py
```

## Implementation sequence

``` text
03.1 What tool calling means
03.2 Define a tool
03.3 Define tool schema
03.4 Give tools to LLM
03.5 Parse tool requests
03.6 Execute tool safely
03.7 Return tool result to LLM
03.8 Build tool loop
03.9 Multiple tools
03.10 Tool-call IDs
03.11 Termination and safety boundary
03.12 Prepare for PostgreSQL
```

## First tool

The first tool is intentionally backed by in-memory CRM data:

``` python
class SearchCompaniesInput(BaseModel):
    name: str
```

The implementation:

``` python
def search_companies(
    input: SearchCompaniesInput,
) -> list[dict]:
    ...
```

The purpose is to isolate agent mechanics from database complexity.

## Tool definition

`definitions.py` contains the LLM-facing contract:

``` python
SEARCH_COMPANIES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_companies",
        "description": "Search the CRM for companies by name.",
        "parameters": SearchCompaniesInput.model_json_schema(),
    },
}
```

## Tool registry

`registry.py` maps the LLM-visible tool name to executable Python code:

``` python
TOOLS = {
    "search_companies": {
        "input_model": SearchCompaniesInput,
        "handler": search_companies,
    },
}
```

Keep the two concepts separate:

``` text
definitions.py
    LLM/API contract

registry.py
    runtime implementation
```

## Native tool calling

The Ollama client passes:

``` python
tools=[...]
```

to `/api/chat`.

The response is normalized into:

``` python
class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]
```

## Tool execution

The execution boundary must:

``` text
1. Find the tool
2. Validate arguments
3. Execute handler
4. Return result
```

Do not let the model execute Python directly.

## Agent loop

The basic loop is:

``` python
while iteration < MAX_ITERATIONS:
    response = await llm.chat(...)

    if not response.tool_calls:
        return response.content

    add assistant tool request to messages

    execute each tool call

    add tool result to messages
```

## Tool-call IDs

Every invocation needs a unique ID.

Good:

``` text
call_001
call_002
call_003
```

Bad:

``` text
search_people
search_people
search_people
```

The ID must be preserved between:

``` text
assistant.tool_calls[].id
```

and:

``` text
tool.tool_call_id
```

## Multiple tools

The lesson introduces:

``` text
search_companies
search_people
```

A tool result may provide information needed by a later tool call.

Example:

``` text
search_companies
       ↓
company
       ↓
search_people
       ↓
person
```

## Important tool-design experiment

An initial design used:

``` python
search_people(company_id: str)
```

This was implementation-oriented and caused the model to produce
mismatched calls such as:

``` text
search_people(name="Acme Corporation")
```

The tool was redesigned as:

``` python
class SearchPeopleInput(BaseModel):
    company_name: str
```

This aligned the capability with the user's domain-level question.

The successful call became:

``` json
{
  "name": "search_people",
  "arguments": {
    "company_name": "Acme Corporation"
  }
}
```

## Successful test

User query:

``` text
Who is the CEO of Acme Corporation
```

Tool result:

``` json
[
  {
    "id": "john-doe",
    "name": "John Doe",
    "company_name": "Acme Corporation",
    "role": "CEO"
  }
]
```

Final answer:

``` text
The CEO of Acme Corporation is John Doe.
```

## Debugging

During development, print:

``` text
=== LLM REQUEST ===
=== LLM RESPONSE ===
=== TOOL REQUEST ===
=== TOOL RESULT ===
```

This makes the agent state transition visible.

Once the implementation is stable, reduce noisy diagnostic output and
move structured observability into the application's logging/telemetry
layer.

## Safety controls

At minimum, the runtime needs:

``` python
MAX_ITERATIONS = 5
```

Never rely on:

``` python
while True:
```

without an explicit termination strategy.

Future controls include:

-   maximum tool calls
-   per-tool budgets
-   duplicate-call detection
-   timeout
-   cancellation
-   authorization
-   audit logging
-   tool-specific policies

## Important security principle

Treat all model-generated tool calls as untrusted input.

Never allow the model to directly construct and execute arbitrary SQL,
shell commands, HTTP requests, or privileged operations.

Prefer:

``` text
LLM
 ↓
well-defined tool
 ↓
validated arguments
 ↓
application code
 ↓
parameterized query/API
```

rather than:

``` text
LLM
 ↓
arbitrary code/SQL
 ↓
production system
```

## Completion criteria

Lesson 3 is complete when you can demonstrate:

-   a tool definition
-   a runtime tool registry
-   native Ollama tool calling
-   structured tool arguments
-   Pydantic argument validation
-   tool execution
-   tool result injection
-   a second LLM invocation
-   unique tool-call IDs
-   an iteration limit
-   multiple tools
-   a successful end-to-end tool-using agent

## Evidence

Recommended experiment record:

``` text
docs/experiments/03-tool-calling.md
```

Record both successful and failed experiments.

Important failures from this lesson:

1.  Initial missing `datauri` import in `ollama.py`.
2.  Native tool calls were initially not visible through the wrapper.
3.  Tool schema/implementation mismatch caused repeated incorrect calls.
4.  Missing capability/data prevented the model from answering the CEO
    question.
5.  Reusing the tool name as `tool_call_id` was identified as a protocol
    flaw.
6.  The final `search_people(company_name)` design produced a successful
    end-to-end result.

## Transition to Lesson 4

Next, replace the in-memory tool implementation:

``` text
search_people()
    ↓
Python list
```

with:

``` text
search_people()
    ↓
repository/query layer
    ↓
PostgreSQL
    ↓
CRM data
```

The agent loop itself should remain unchanged.
