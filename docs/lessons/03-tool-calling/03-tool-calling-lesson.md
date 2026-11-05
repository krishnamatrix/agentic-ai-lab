# Lesson 3 --- Tool Calling and the Agent Loop

## Overview

Lesson 2 established that an LLM can produce structured data.

This lesson takes the next step:

> The model can produce a structured request for the application to
> perform an action.

That is tool calling.

We deliberately build the mechanism ourselves before introducing
LangGraph or another agent framework.

The final architecture is:

``` text
User
 ↓
LLM
 ↓
Tool call
 ↓
Application validates and executes tool
 ↓
Tool result
 ↓
LLM
 ↓
Final answer
```

------------------------------------------------------------------------

# 1. What tool calling actually means

A model does not directly execute Python functions.

Instead, it produces structured data describing an action:

``` json
{
  "name": "search_companies",
  "arguments": {
    "name": "Acme Corp"
  }
}
```

The application receives that request and decides whether and how to
execute it.

Therefore:

``` text
LLM
 ≠
Python runtime
```

The LLM proposes an action.

The application executes the action.

This distinction is fundamental to agent architecture and security.

------------------------------------------------------------------------

# 2. First tool

We started with an intentionally simple in-memory CRM tool.

``` python
from pydantic import BaseModel


class SearchCompaniesInput(BaseModel):
    name: str


def search_companies(
    input: SearchCompaniesInput,
) -> list[dict]:
    companies = [
        {
            "id": "company-001",
            "name": "Acme Corp",
            "industry": "Technology",
        },
        {
            "id": "company-002",
            "name": "Globex",
            "industry": "Finance",
        },
        {
            "id": "company-003",
            "name": "Initech",
            "industry": "Software",
        },
    ]

    return [
        company
        for company in companies
        if input.name.lower()
        in company["name"].lower()
    ]
```

The in-memory dataset is intentional.

At this stage we are learning the agent protocol, not database
engineering.

------------------------------------------------------------------------

# 3. Tool definitions vs tool registry

We introduced two separate concepts.

## `definitions.py`

This is the LLM-facing contract.

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

It answers:

> What tools can the model request, and what arguments do they accept?

## `registry.py`

This is the application runtime mapping.

``` python
TOOLS = {
    "search_companies": {
        "input_model": SearchCompaniesInput,
        "handler": search_companies,
    },
}
```

It answers:

> When the model requests this tool, which Python function executes?

A useful mental model is:

``` text
definitions.py
    = LLM/API contract

registry.py
    = runtime implementation mapping
```

The separation becomes valuable when runtime metadata grows to include
authorization, timeouts, retry policy, audit policy, or dependencies.

------------------------------------------------------------------------

# 4. Native Ollama tool calling

The Ollama request includes:

``` json
{
  "tools": [...]
}
```

The successful Gemma 4 response produced:

``` json
{
  "message": {
    "tool_calls": [
      {
        "function": {
          "name": "search_companies",
          "arguments": {
            "name": "Acme Corp"
          }
        }
      }
    ]
  }
}
```

Our LLM abstraction converts that provider response into:

``` python
class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]
```

This prevents provider-specific response structures from leaking into
the agent layer.

------------------------------------------------------------------------

# 5. Tool execution boundary

The application owns execution.

Our executor performs:

1.  Tool lookup
2.  Argument validation
3.  Handler execution

Conceptually:

``` python
def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
):
    tool = TOOLS.get(tool_name)

    if tool is None:
        raise ToolExecutionError(
            f"Unknown tool: {tool_name}"
        )

    input_model = tool["input_model"]
    handler = tool["handler"]

    validated_input = input_model.model_validate(arguments)

    return handler(validated_input)
```

This is the beginning of a security boundary.

The LLM is untrusted input.

------------------------------------------------------------------------

# 6. The tool result must go back to the LLM

A single tool call is not yet an agent.

The application must append the tool result to the conversation and call
the LLM again.

The conversation becomes:

``` text
USER
Who is the CEO of Acme Corporation?

ASSISTANT
tool_call:
  search_people(
      company_name="Acme Corporation"
  )

TOOL
[
  {
    "name": "John Doe",
    "company_name": "Acme Corporation",
    "role": "CEO"
  }
]

ASSISTANT
The CEO of Acme Corporation is John Doe.
```

The second LLM invocation is what allows the model to turn the raw tool
result into a user-facing answer.

------------------------------------------------------------------------

# 7. The first real agent loop

Our simple runtime is conceptually:

``` python
while True:
    response = await llm.chat(
        messages=messages,
        tools=tools,
    )

    if not response.tool_calls:
        return response.content

    messages.append(assistant_tool_request)

    for tool_call in response.tool_calls:
        result = execute_tool(
            tool_call.name,
            tool_call.arguments,
        )

        messages.append(tool_result)
```

This is the fundamental agent loop.

An agent is not fundamentally a framework.

At this level it is:

``` text
LLM
+
tools
+
state
+
execution loop
+
termination condition
```

------------------------------------------------------------------------

# 8. Conversation state is explicit

Before the second LLM invocation, the application constructs state
similar to:

``` python
[
    {
        "role": "user",
        "content": "Who is the CEO of Acme Corporation",
    },
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_yhka025h",
                "function": {
                    "name": "search_people",
                    "arguments": {
                        "company_name": "Acme Corporation"
                    },
                },
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "call_yhka025h",
        "content": "...",
    },
]
```

The model does not magically know that Python executed the function.

The application explicitly records:

``` text
assistant requested action
        ↓
tool executed
        ↓
tool produced observation
```

That state transition is central to agent systems.

------------------------------------------------------------------------

# 9. Tool-call IDs

Initially we used the tool name as the call ID:

``` text
tool_call_id = "search_people"
```

That is insufficient.

The same tool may be called multiple times:

``` text
call_001 → search_people("Acme")
call_002 → search_people("Globex")
call_003 → search_people("Initech")
```

The correct protocol preserves a unique ID.

Our successful Gemma trace produced:

``` text
call_yhka025h
```

and the same ID appeared in:

``` text
assistant.tool_calls[].id
```

and:

``` text
tool.tool_call_id
```

This establishes a precise relationship between an action request and
its result.

------------------------------------------------------------------------

# 10. Multiple tools

We introduced:

``` text
search_companies
search_people
```

The conceptual relationship is:

``` text
search_companies
       ↓
company information
       ↓
search_people
       ↓
people
```

This demonstrated that tool outputs can become information needed for
subsequent tool calls.

------------------------------------------------------------------------

# 11. Tool design matters

We initially designed:

``` python
search_people(company_id: str)
```

This exposed an implementation-oriented interface.

The model struggled with:

> Who is the CEO of Acme Corporation?

It attempted incorrect calls such as:

``` text
search_people(name="Acme Corporation")
```

and repeatedly failed to obtain the intended data.

We changed the tool contract to:

``` python
class SearchPeopleInput(BaseModel):
    company_name: str
```

This better matches the domain-level capability:

> Search for people associated with a company.

The successful invocation became:

``` json
{
  "name": "search_people",
  "arguments": {
    "company_name": "Acme Corporation"
  }
}
```

and returned:

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

The final model response was:

``` text
The CEO of Acme Corporation is John Doe.
```

### Lesson

Tool design is part of prompt/agent engineering.

A useful tool should make clear:

-   what it does
-   when it should be used
-   what arguments it accepts
-   what type of information it returns

Expose domain capabilities rather than unnecessary database
implementation details.

------------------------------------------------------------------------

# 12. Tool descriptions influence model behavior

The model only sees the tool contract.

It does not see the Python function implementation.

Therefore:

``` text
Tool name
+
Description
+
Input schema
```

are effectively part of the model's action space.

A weak description:

``` text
Find people using a company ID.
```

may make a user-facing question difficult to translate into the right
action.

A stronger description:

``` text
Search for people associated with a company.
Use this when the user asks for a CEO, CTO, executive,
contact, employee, or other person at a company.
```

makes the capability much clearer.

------------------------------------------------------------------------

# 13. Agent termination

An unrestricted:

``` python
while True:
```

is dangerous.

A model can theoretically keep requesting tools indefinitely.

We therefore introduce:

``` python
MAX_ITERATIONS = 5
```

and:

``` python
iteration = 0

while iteration < MAX_ITERATIONS:
    iteration += 1
    ...
```

If the limit is reached:

``` python
raise RuntimeError(
    f"Agent exceeded maximum iterations: {MAX_ITERATIONS}"
)
```

Important principle:

> The LLM can request another action. The application decides whether
> the agent is allowed to continue.

Termination is an application responsibility.

------------------------------------------------------------------------

# 14. Tool execution is a security boundary

Never think of:

``` text
LLM → execute Python function
```

as a trusted operation.

The model is an untrusted decision-maker.

The safer model is:

``` text
LLM
 ↓
Tool request
 ↓
Tool execution boundary
 ├── tool exists?
 ├── arguments valid?
 ├── authorized?
 ├── allowed in current context?
 ├── timeout?
 └── execute
 ↓
Tool result
```

This becomes critical when tools eventually perform:

``` text
send_email
create_invoice
update_customer
delete_record
issue_refund
execute_sql
```

A model being allowed to request a tool does not automatically mean it
should be allowed to execute it.

------------------------------------------------------------------------

# 15. Important failure experiments

## Failure 1 --- Tool contract mismatch

The model repeatedly produced:

``` text
search_people(name="Acme Corporation")
```

while the implementation expected a company ID.

Result:

``` text
[]
```

The agent then oscillated between:

``` text
search_people
search_companies
search_people
```

before terminating.

### Lesson

Do not immediately solve agent failures by adding more prompt
instructions.

First inspect:

-   tool name
-   description
-   schema
-   implementation
-   expected domain behavior

The tool contract itself may be the problem.

------------------------------------------------------------------------

## Failure 2 --- Missing tool capability

Initially the model searched for the company but could not answer who
the CEO was.

The company record contained no CEO information, and the available tool
set did not provide a reliable people lookup.

### Lesson

Agent capability is bounded by its tools and data.

A model cannot reliably retrieve information that the tool layer cannot
provide.

------------------------------------------------------------------------

## Failure 3 --- Infinite/repetitive tool calls

The model can request the same tool repeatedly.

Therefore the runtime requires:

``` text
iteration limit
```

and eventually more sophisticated controls such as:

-   duplicate-call detection
-   time budgets
-   tool budgets
-   per-tool limits
-   cancellation
-   maximum conversation state
-   authorization policies

These will be introduced later.

------------------------------------------------------------------------

# 16. Successful end-to-end experiment

The final successful experiment was:

``` text
User:
Who is the CEO of Acme Corporation?

        ↓

LLM:
search_people(
    company_name="Acme Corporation"
)

        ↓

Tool:
[
    {
        "id": "john-doe",
        "name": "John Doe",
        "company_name": "Acme Corporation",
        "role": "CEO"
    }
]

        ↓

LLM:
The CEO of Acme Corporation is John Doe.
```

This verifies:

-   native tool calling
-   structured tool arguments
-   tool-call IDs
-   application-side execution
-   tool result injection
-   second LLM invocation
-   final natural-language response
-   termination

------------------------------------------------------------------------

# 17. Current architecture

After Lesson 3:

``` text
                         User
                           │
                           ▼
                    ┌─────────────┐
                    │     LLM     │
                    └──────┬──────┘
                           │
                     Tool Call
                           │
                           ▼
                ┌────────────────────┐
                │  Tool Executor     │
                ├────────────────────┤
                │ tool lookup        │
                │ argument validation│
                │ authorization      │
                │ execution policy   │
                └─────────┬──────────┘
                          │
                          ▼
                    Tool Handler
                          │
                       result
                          │
                          ▼
                    Conversation
                       State
                          │
                          ▼
                         LLM
                          │
                          ▼
                    Final Answer
```

The next architectural evolution is to replace the in-memory CRM
handlers with PostgreSQL-backed application tools.

------------------------------------------------------------------------

# 18. Why we did not use LangGraph yet

A framework would hide much of the mechanism we needed to understand.

We first implemented:

``` text
tool definitions
tool registry
tool execution
conversation state
tool results
tool-call IDs
execution loop
termination
```

Once these concepts are understood, a framework becomes an
implementation choice rather than magic.

Later we can compare:

``` text
Our Python loop
        vs
LangGraph
        vs
MCP-based tools
```

and understand exactly what the framework is providing.

------------------------------------------------------------------------

# 19. Engineering principles

### 1. The LLM does not execute tools

It requests actions.

### 2. The application owns execution

The runtime validates and executes.

### 3. Tool definitions are contracts

They define the model-visible action space.

### 4. Tool registries map contracts to implementations

They provide runtime behavior.

### 5. Tool results must become conversation state

Otherwise the next LLM call cannot use the observation.

### 6. Tool-call IDs establish request/result identity

Names alone are insufficient.

### 7. Tool design affects agent behavior

Domain-oriented capabilities are generally easier for the model to use
than database-oriented mechanics.

### 8. Termination must be enforced outside the model

Never trust an unrestricted agent loop.

### 9. Tool execution is a security boundary

The model is an untrusted source of action requests.

### 10. Agents are control loops

At this level:

``` text
LLM
→ action
→ observation
→ LLM
→ action/answer
```

That is the core mechanism behind the more sophisticated agent
architectures we will build later.

------------------------------------------------------------------------

# 20. Transition to Lesson 4

The next lesson replaces:

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

The agent architecture remains the same.

Only the tool implementation becomes production-like.
