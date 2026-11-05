# 01 — LLM Fundamentals

## What Actually Happens When an LLM Generates Text?

An LLM application is often introduced with a deceptively simple abstraction:

```text
prompt → LLM → response
```

That abstraction is useful for getting started, but it hides most of the engineering concerns that become important in production systems.

In this chapter, we build the first version of our LLM layer using a locally hosted model through Ollama. Rather than starting with an agent framework, we interact with the model directly over HTTP.

The goal is not simply to make the model answer a question.

The goal is to understand what actually happens between our application and the model.

---

# 1. Learning Objectives

By the end of this chapter, we should understand:

* what an LLM request actually looks like
* the role of the model, messages, and generation parameters
* how an application communicates with an LLM provider
* the difference between input and output tokens
* why output length affects latency and cost
* the difference between cold and warm model execution
* what model-generation telemetry tells us
* the difference between streaming and non-streaming generation
* why provider-specific behavior matters
* why an application should isolate LLM infrastructure behind an abstraction
* why LLM responses should be treated as probabilistic outputs rather than trusted application data

We intentionally do **not** introduce LangChain, LangGraph, RAG, agents, tools, or vector databases in this chapter.

The objective is to understand the primitive first.

---

# 2. The Application We Are Building

Our long-term project is a CRM Intelligence Platform.

The eventual architecture will look approximately like:

```text
                         ┌────────────────────┐
                         │     Next.js UI     │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │     FastAPI        │
                         │                    │
                         │   Agent Runtime    │
                         └──────┬───────┬─────┘
                                │       │
                         ┌──────▼───┐ ┌─▼──────────┐
                         │PostgreSQL│ │ LLM Gateway │
                         └──────────┘ └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │    Ollama   │
                                      │   Gemma 4   │
                                      └─────────────┘
```

However, in this chapter we intentionally simplify the system:

```text
Python
  │
  ▼
LLM Gateway
  │
  ▼
Ollama
  │
  ▼
Gemma 4
```

There is no CRM retrieval yet.

There is no agent.

There are no tools.

There is no RAG.

This isolation allows us to understand the LLM itself before adding application complexity.

---

# 3. Why Start With Ollama?

For this learning project, we want to understand LLM engineering without immediately depending on a hosted API.

Ollama provides a local HTTP interface through which our application can interact with a locally running model.

Our model is:

```text
gemma4:e4b
```

The application therefore communicates with:

```text
http://localhost:11434
```

The important architectural principle is that our application should not become dependent on Ollama-specific behavior.

Instead:

```text
Application
     │
     ▼
LLM abstraction
     │
     ├── Ollama
     ├── OpenAI
     ├── Anthropic
     └── other providers
```

The provider is an implementation detail.

This becomes increasingly important as the project grows.

---

# 4. The First LLM Request

At the HTTP level, the interaction is conceptually:

```json
{
  "model": "gemma4:e4b",
  "messages": [
    {
      "role": "user",
      "content": "Explain what a CRM is in one sentence."
    }
  ],
  "stream": false
}
```

The model then returns a response containing generated content and provider-specific metadata.

Conceptually:

```text
request
   │
   ▼
Ollama
   │
   ▼
Gemma
   │
   ▼
generated response
   +
generation metadata
```

The important realization is that an LLM response is more than a string.

It contains information about how that string was generated.

---

# 5. Tokens

LLMs don't fundamentally process text as words.

They process **tokens**.

For example, a sentence such as:

```text
A CRM manages customer relationships.
```

is converted into a sequence of tokens before being processed by the model.

The exact tokenization depends on the model's tokenizer.

This distinction matters because token counts influence:

* context-window consumption
* latency
* memory requirements
* generation throughput
* API cost for hosted models
* prompt design
* caching strategies

Therefore, an LLM engineer needs to think in terms of tokens rather than simply characters or words.

---

# 6. Input and Output Tokens

A request can be thought of as having two primary token streams:

```text
Input tokens
     │
     ▼
   Model
     │
     ▼
Output tokens
```

The input includes things such as:

* system instructions
* conversation history
* user prompt
* retrieved documents
* tool results

The output is the generated response.

For our application we therefore track:

```text
input_tokens
output_tokens
total_tokens
```

with:

```text
total_tokens =
    input_tokens + output_tokens
```

The exact accounting can be provider-specific, so our abstraction should not assume every provider exposes identical telemetry.

---

# 7. The LLM Gateway

Instead of allowing application code to call Ollama directly everywhere, we created a small adapter:

```text
app/
└── llm/
    ├── types.py
    ├── pricing.py
    └── ollama.py
```

The important separation is:

```text
CRM/application code
        │
        ▼
    LLM interface
        │
        ▼
   Ollama adapter
        │
        ▼
      Ollama
```

The application therefore doesn't need to know:

* Ollama's URL
* Ollama's HTTP payload
* Ollama's response structure
* Ollama's duration units
* Ollama-specific telemetry fields

That knowledge belongs in the adapter.

This is an example of **provider isolation**.

---

# 8. Why Pydantic?

We also introduced a typed representation for an LLM response.

Conceptually:

```python
class LLMResponse:
    request_id
    provider
    model
    content
    usage
```

and:

```python
class LLMUsage:
    input_tokens
    cached_input_tokens
    output_tokens
    total_tokens

    latency_ms

    model_load_ms
    prompt_eval_ms
    generation_ms

    time_to_first_token_ms

    end_to_end_tokens_per_second
    generation_tokens_per_second

    estimated_api_cost_usd
```

This creates a stable internal contract even when the provider's raw response is different.

This pattern will become increasingly important when we eventually add multiple providers.

---

# 9. Latency Is Not One Thing

One of the most useful discoveries in this experiment was that:

```text
LLM latency
```

is not a single homogeneous operation.

Ollama exposes several durations.

Conceptually:

```text
Request
│
├── model loading
│
├── prompt evaluation
│
└── generation
```

We therefore measured:

```text
model_load_ms
prompt_eval_ms
generation_ms
latency_ms
```

This lets us distinguish different performance characteristics.

For example, a request can be slow because:

```text
model loading is expensive
```

rather than because:

```text
token generation is slow
```

This distinction becomes important when optimizing production systems.

---

# 10. Cold vs Warm Generation

Our experiments demonstrated an important difference between cold and warm execution.

In one experiment, model loading took several seconds.

In another:

```text
model_load_ms ≈ 8 ms
```

The model was already resident, so the expensive loading phase largely disappeared.

This produces two very different user experiences:

```text
Cold request

request
  │
  ├── load model ────────────────┐
  │                              │
  └── generate ──────────────────┘
```

versus:

```text
Warm request

request
  │
  └── generate ────────────────
```

This is one reason why benchmarking an LLM application with a single request can be misleading.

A production system may experience:

* cold starts
* warm requests
* model eviction
* concurrent requests
* different prompt sizes
* different output sizes

Performance testing therefore needs representative workloads.

---

# 11. Output Length Matters

We ran two contrasting experiments.

### Experiment A

Prompt:

```text
Explain what a CRM is in one sentence.
```

The model generated approximately:

```text
318 output tokens
```

The generation took several seconds.

### Experiment B

Prompt:

```text
Reply with exactly: CRM.
```

The result was approximately:

```text
3 output tokens
```

with generation time around:

```text
51 ms
```

The generation throughput in both cases was roughly in the same range:

```text
~55–58 tokens/sec
```

The important observation is not the exact benchmark number.

The important relationship is:

```text
more output tokens
        ↓
more generation work
        ↓
more generation latency
```

This becomes extremely important later when designing agents.

An agent that unnecessarily generates large responses can consume significantly more compute and time than an agent that produces concise intermediate results.

---

# 12. Token Economics

Ollama itself is running locally, so our direct API cost is:

```text
$0
```

However, we introduced a simulated hosted-API pricing model so that we can reason about cost as we build the system.

Our benchmark assumptions are:

```text
Input:  $0.50 / 1M tokens
Output: $1.50 / 1M tokens
```

The estimated cost is:

```python
input_cost = (
    input_tokens / 1_000_000
) * input_price

output_cost = (
    output_tokens / 1_000_000
) * output_price
```

Therefore:

```text
estimated_cost =
    input_cost + output_cost
```

This is deliberately **not actual Ollama pricing**.

It is an engineering simulation.

The purpose is to make cost awareness part of the architecture from the beginning.

Later, when we build agents, this becomes particularly important because one user request may cause:

```text
User request
    │
    ├── LLM call
    ├── tool call
    ├── LLM call
    ├── retrieval
    ├── LLM call
    └── final response
```

The cost of the user request is therefore not necessarily the cost of one LLM call.

---

# 13. Streaming

We also experimented with Ollama's streaming API.

Instead of:

```text
request
   │
   ▼
wait
   │
   ▼
complete response
```

streaming produces incremental chunks:

```text
request
   │
   ├── chunk
   ├── chunk
   ├── chunk
   ├── chunk
   └── done
```

This enables applications to display generated content progressively.

However, we discovered an important provider/model-specific behavior.

Gemma's response stream can contain:

```json
{
  "message": {
    "content": "",
    "thinking": "Here"
  }
}
```

followed by additional thinking chunks.

The visible answer is therefore not necessarily the first thing emitted by the model.

This led to an important distinction:

```text
stream started
        ≠
user-visible answer started
```

We do not need to optimize this behavior yet.

The purpose of the experiment was to understand that streaming is a protocol and that its semantics are provider/model dependent.

---

# 14. A Stream Chunk Is Not Necessarily a Token

Another useful discovery came from inspecting the raw streaming response.

We saw chunks such as:

```text
"Here"
"'"
"s"
" a"
" thinking"
" process"
```

It would be tempting to call each chunk a token.

That would be incorrect.

A streaming chunk is a unit emitted by the provider's streaming protocol.

The relationship between:

```text
HTTP chunk
```

and:

```text
model token
```

should not be assumed without provider-specific evidence.

This is a good example of why abstraction layers should preserve semantics rather than invent them.

---

# 15. Hidden Assumptions Are Dangerous

The first streaming experiment also demonstrated a broader engineering lesson.

It is easy to write:

```python
token_count += 1
```

inside a streaming loop.

But that variable might actually be counting:

```text
HTTP chunks
```

rather than:

```text
tokens
```

The number can still be useful operationally, but it should be named correctly.

Good observability starts with accurate semantics.

For example:

```text
chunks_received
```

is better than:

```text
token_count
```

unless we have evidence that the provider's chunks correspond to tokens.

---

# 16. Why We Did Not Use LangChain

It would have been easy to begin with:

```text
LangChain
    ↓
Ollama
```

But that would hide many of the mechanisms we are trying to learn.

Instead, we built:

```text
Python
  ↓
httpx
  ↓
Ollama HTTP API
```

This forces us to understand:

* HTTP requests
* request payloads
* response parsing
* provider metadata
* token accounting
* streaming
* latency
* error handling
* provider abstraction

Frameworks will become useful later.

But a framework should simplify mechanisms we already understand, rather than become a substitute for understanding them.

---

# 17. What We Have Built

At the end of this chapter, our application has a primitive LLM gateway:

```text
app/
└── llm/
    ├── __init__.py
    ├── types.py
    ├── pricing.py
    └── ollama.py
```

The application can:

* send chat messages
* select a model
* configure temperature
* receive generated text
* collect usage metadata
* measure latency
* estimate benchmark cost
* stream generated content

This is the first reusable infrastructure component in our Agentic AI platform.

---

# 18. What We Have Not Built

We intentionally have not implemented:

```text
❌ Structured outputs
❌ JSON schema enforcement
❌ Tool calling
❌ Function calling
❌ RAG
❌ Embeddings
❌ Vector search
❌ Memory
❌ Agents
❌ Planning
❌ Multi-agent systems
❌ MCP
```

Those are the subjects of later chapters.

This distinction is important.

We should understand the primitive before composing primitives into increasingly complex systems.

---

# 19. Engineering Lessons

## Lesson 1 — An LLM is an infrastructure dependency

Treating an LLM as:

```python
response = llm(prompt)
```

hides important operational concerns.

A real LLM integration needs to account for:

* latency
* token usage
* errors
* retries
* provider behavior
* model selection
* cost
* observability
* streaming

---

## Lesson 2 — Provider isolation matters

Application code should not be tightly coupled to a specific provider.

Instead:

```text
Application
    ↓
LLM abstraction
    ↓
Provider adapter
```

This gives us the ability to change providers later without rewriting the application.

---

## Lesson 3 — Output length is an engineering parameter

Generation length affects:

* latency
* compute
* cost
* user experience

Prompt design therefore isn't merely about answer quality.

It is also a performance and economics concern.

---

## Lesson 4 — Local inference is not "free"

Although the Ollama API cost is zero, the machine still consumes:

* CPU/GPU resources
* memory
* electricity
* time

A production system therefore needs to think about resource economics even when using local models.

---

## Lesson 5 — LLM output is probabilistic

An LLM produces generated text.

It does not automatically produce:

```text
validated application state
```

That distinction will become central in the next chapter.

The application must establish boundaries around the model.

---

## Lesson 6 — Observability should reflect actual semantics

A metric is useful only if we understand what it represents.

For example:

```text
stream chunk
```

should not automatically be called:

```text
token
```

Likewise:

```text
request latency
```

should not automatically be interpreted as:

```text
generation latency
```

Good AI systems require precise telemetry semantics.

---

# 20. The Mental Model Going Forward

The simplest useful mental model for the next stages is:

```text
              ┌─────────────────┐
              │      Prompt     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │      Model      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Generated Text  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Application     │
              │ Validation      │
              │ Logic           │
              └─────────────────┘
```

The next question is therefore obvious:

> What happens when generated text needs to become structured application data?

That is where we go next.

---

# 21. Transition to Chapter 02

Our current interaction is:

```text
User
  │
  ▼
Natural language
  │
  ▼
LLM
  │
  ▼
Natural language
```

But an application needs something more like:

```text
User
  │
  ▼
Natural language
  │
  ▼
LLM
  │
  ▼
Structured data
  │
  ▼
Validation
  │
  ▼
Application
```

For our CRM application, we might receive:

```text
I spoke with John from Acme yesterday.
They're interested in our enterprise plan
and want a demo next week.
```

and want:

```json
{
  "person_name": "John",
  "company_name": "Acme",
  "interaction_type": "call",
  "interest": "enterprise plan",
  "next_action": "demo",
  "next_action_time": "next week"
}
```

This introduces our next fundamental concept:

# Structured Outputs

We will learn how to move from:

```text
probabilistic language generation
```

to:

```text
validated application data
```

without yet introducing agents or frameworks.

That is the foundation for everything that follows.
