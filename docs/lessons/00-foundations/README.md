# Lesson 0 — Building the Agentic AI Engineering Laboratory

> **Learning Path:** Agentic AI Engineering Lab
> **Stage:** 0 — Foundations
> **Project:** CRM Intelligence Platform
> **Status:** Foundation

---

## 1. Objective

Before building an AI system, we need a reliable engineering foundation on which the AI capabilities can evolve.

In this lesson, we establish the initial application architecture, development environment, database, testing infrastructure, configuration management, and documentation structure for the **Agentic AI Engineering Lab**.

The goal is deliberately modest:

> Build a deterministic software system first. Introduce probabilistic AI only after the foundation is in place.

This approach allows us to understand exactly what changes when an LLM, retrieval system, tool-calling system, and eventually an autonomous agent are introduced.

---

## 2. What We Are Building

The long-term objective is to build a CRM Intelligence Platform that progressively evolves from a simple conversational interface into an agentic AI system.

The system will eventually be able to:

* understand natural-language CRM queries
* retrieve CRM information
* search unstructured CRM content
* reason over multiple sources
* invoke tools
* execute workflows
* maintain appropriate forms of memory
* plan multi-step tasks
* collaborate across specialized agents
* interact with external systems through MCP
* operate with production-grade observability, security, reliability, and cost controls

However, none of those capabilities are implemented yet.

We intentionally start with the deterministic foundation.

---

## 3. Initial Architecture

Our initial architecture is:

```text
                         ┌──────────────┐
                         │   Browser    │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Next.js    │
                         │      UI      │
                         └──────┬───────┘
                                │ HTTP
                                ▼
                         ┌──────────────┐
                         │   FastAPI    │
                         │    Python    │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
             ┌──────────────┐        ┌──────────────┐
             │ PostgreSQL   │        │     LLM      │
             │     CRM      │        │   Provider   │
             └──────────────┘        └──────────────┘
```

The LLM provider appears in the target architecture only to illustrate where it will eventually connect.

At the end of Lesson 0, the LLM integration does not exist yet.

---

## 4. Technology Stack

The initial stack is intentionally small.

### Application

* Python
* FastAPI
* Pydantic
* Pydantic Settings

### Database

* PostgreSQL

### Development

* `uv`
* pytest
* Ruff
* Git

### Frontend

* Next.js
* TypeScript

The frontend is not the focus of the initial lessons. The primary learning environment is the Python AI backend.

---

## 5. Why Python?

Python is used for the AI backend because it provides a broad ecosystem for:

* LLM integration
* machine learning
* embeddings
* RAG
* evaluation
* experimentation
* agent frameworks
* MCP
* data processing
* model inference
* AI observability

Using Python also makes the learning material accessible to a broad audience of AI engineers and developers.

However, the architectural principles we learn are not Python-specific.

The important distinction is:

```text
Python
   ↓
Implementation language

LLM / RAG / Agent architecture
   ↓
Engineering concepts
```

The concepts should remain applicable regardless of implementation language.

---

## 6. Why FastAPI?

FastAPI provides a lightweight HTTP layer around our AI backend.

It gives us:

* type-aware request handling
* Pydantic integration
* automatic OpenAPI documentation
* asynchronous request handling
* a simple foundation for AI APIs

We deliberately avoid introducing an AI-specific framework at this stage.

FastAPI is an application framework.

It does not attempt to hide the mechanics of LLMs or agents from us.

---

## 7. Why PostgreSQL?

PostgreSQL will initially act as the system of record for our CRM.

We will eventually use it for both structured CRM information and, when the curriculum reaches retrieval, potentially vector search through `pgvector`.

Starting with PostgreSQL provides an important architectural advantage:

> We can understand the difference between structured data storage and semantic retrieval before introducing specialized vector infrastructure.

---

## 8. Why CRM?

CRM is an excellent domain for learning agentic AI because it combines several different types of information.

### Structured data

Examples:

```text
Company
Person
Opportunity
Pipeline stage
Revenue
Employee count
```

### Semi-structured data

Examples:

```text
Interaction metadata
Meeting records
Call information
Email metadata
```

### Unstructured data

Examples:

```text
Meeting notes
Call summaries
Research notes
Email content
```

This gives us a natural progression:

```text
SQL
  ↓
Context Engineering
  ↓
Semantic Search
  ↓
RAG
  ↓
Tool Calling
  ↓
Agents
  ↓
Agentic Workflows
```

The same underlying dataset remains useful throughout the entire learning journey.

---

# 9. Initial CRM Data Model

The initial CRM consists of five primary entities.

```text
                     ┌──────────────┐
                     │   Company    │
                     └──────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
         People       Opportunities    Interactions
             │
             ▼
           Notes
```

## Companies

Represents organizations in the CRM.

Example attributes:

```text
id
name
industry
employee_count
annual_revenue
headquarters
website
created_at
```

## People

Represents individuals associated with companies.

Example attributes:

```text
id
company_id
first_name
last_name
title
email
phone
location
linkedin_url
created_at
```

## Interactions

Represents events occurring between people, companies, and the organization using the CRM.

Examples include:

```text
meeting
email
call
conference
introduction
```

Attributes include:

```text
id
company_id
person_id
interaction_type
subject
content
occurred_at
created_at
```

## Opportunities

Represents business opportunities associated with companies.

Attributes include:

```text
id
company_id
name
stage
value
probability
expected_close_date
owner
created_at
```

## Notes

Represents free-form CRM observations.

Attributes include:

```text
id
company_id
person_id
content
author
created_at
```

---

# 10. Why We Are Not Adding a Vector Database Yet

A common mistake when learning RAG is to immediately install a vector database.

We deliberately do not do that.

At this stage, we do not yet need:

```text
embeddings
vectors
vector indexes
semantic retrieval
reranking
```

Those concepts will be introduced when we reach the RAG portion of the curriculum.

This gives us an opportunity to understand **why** a vector database is needed rather than simply following a framework tutorial.

---

# 11. Why We Are Not Using an Agent Framework Yet

We are deliberately not starting with:

```text
LangChain
LangGraph
LlamaIndex
```

or another agent framework.

The reason is fundamental.

Before using an abstraction such as an agent framework, we should understand the primitives underneath it:

```text
LLM call
    ↓
structured output
    ↓
tool definition
    ↓
tool invocation
    ↓
observation
    ↓
state
    ↓
iteration
```

Later, we will implement these mechanisms ourselves.

Only after understanding them will we introduce frameworks and compare what abstractions they provide.

This avoids learning a framework without understanding the underlying architecture.

---

# 12. Deterministic vs Probabilistic Systems

One of the central themes of this curriculum is the distinction between deterministic and probabilistic components.

Traditional application components are generally deterministic:

```text
HTTP request
    ↓
Python function
    ↓
Database query
    ↓
Result
```

Given the same inputs and environment, we generally expect the same behavior.

LLMs introduce probabilistic behavior:

```text
Prompt
    ↓
LLM
    ↓
Generated output
```

The output is generated probabilistically rather than through a conventional deterministic function.

As the system evolves, our job as engineers is to surround these probabilistic components with deterministic controls.

For example:

```text
              Probabilistic
                  LLM
                   │
       ┌───────────┼────────────┐
       ▼           ▼            ▼
   Validation   Authorization  Budgets
       │           │            │
       ▼           ▼            ▼
    Pydantic     Policies     Limits
```

This principle will become increasingly important as we build autonomous agents.

---

# 13. Initial Python Project Structure

The initial repository structure is:

```text
agentic-ai-lab/
│
├── apps/
│   └── api/
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── config.py
│       │   └── models/
│       │       ├── __init__.py
│       │       └── crm.py
│       │
│       ├── tests/
│       │   └── test_health.py
│       │
│       ├── pyproject.toml
│       └── .env
│
├── data/
│   ├── seed/
│   └── generated/
│
├── experiments/
│
├── evaluations/
│
├── docs/
│   ├── lessons/
│   ├── architecture/
│   ├── experiments/
│   └── failures/
│
├── scripts/
│
├── .gitignore
└── README.md
```

This structure will evolve throughout the curriculum.

---

# 14. Initial API

Our first endpoint is intentionally simple:

```http
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "agentic-ai-lab"
}
```

The purpose of this endpoint is not functionality.

It establishes the first observable boundary of our backend service.

---

# 15. Configuration

Configuration is externalized from application code.

Example:

```env
APP_ENV=development
DATABASE_URL=postgresql://agentic:agentic@localhost:5432/crm
```

Secrets and environment-specific values should never be committed to source control.

The `.env` file is therefore excluded through `.gitignore`.

LLM credentials will be introduced in a later lesson.

---

# 16. Testing

Even before AI is introduced, we establish automated testing.

Our initial test verifies:

```text
GET /health
        ↓
HTTP 200
        ↓
status == "ok"
```

This may seem trivial, but it establishes an important habit:

> Every capability added to the system should eventually have a way to verify its behavior.

As the project evolves, testing will become significantly more sophisticated.

Eventually we will test:

* LLM outputs
* structured output validation
* tool selection
* tool arguments
* retrieval quality
* agent trajectories
* task completion
* security controls
* cost limits
* failure recovery

---

# 17. Code Quality

Ruff is introduced from the beginning.

The purpose is to avoid accumulating technical debt while the project is still small.

Our development loop becomes:

```text
Write
  ↓
Run tests
  ↓
Run Ruff
  ↓
Commit
```

Later, this becomes part of CI/CD.

---

# 18. Engineering Principles

The project follows several principles.

## 18.1 Understand before abstracting

We implement important mechanisms ourselves before introducing frameworks that abstract them.

## 18.2 Measure before optimizing

We don't assume that a technique improves the system.

We measure:

```text
quality
latency
tokens
cost
memory
throughput
```

before and after changes.

## 18.3 Treat failures as learning material

Failures are not removed from the curriculum.

They become documented experiments.

Examples will eventually include:

```text
Infinite agent loop
Incorrect tool selection
Malformed structured output
Poor retrieval
Token explosion
Stale cache
Duplicate tool execution
Prompt injection
Agent timeout
```

## 18.4 Separate deterministic and probabilistic logic

Business rules, authorization, validation, persistence, and safety controls should not depend unnecessarily on LLM behavior.

## 18.5 One evolving project

We don't build a new toy application for every concept.

The same CRM system evolves through every lesson.

---

# 19. The Long-Term Learning Progression

The system will evolve approximately as follows:

```text
LLM Fundamentals
       │
       ▼
Basic Chat
       │
       ▼
Context Engineering
       │
       ▼
Structured Output
       │
       ▼
Tool Calling
       │
       ▼
Custom Agent Loop
       │
       ▼
Embeddings
       │
       ▼
RAG
       │
       ▼
RAG Evaluation
       │
       ▼
Deterministic Workflows
       │
       ▼
Agentic Workflows
       │
       ▼
Memory
       │
       ▼
Planning
       │
       ▼
Multi-Agent Systems
       │
       ▼
MCP
       │
       ▼
Production Agent Platform
```

Across every stage we will progressively add:

```text
Token Economics
Observability
Caching
Memory Optimization
Error Handling
Security
Evaluation
Performance
Reliability
Cost Governance
```

---

# 20. What We Deliberately Do Not Optimize Yet

At this stage, we do not optimize:

* LLM cost
* inference latency
* vector search
* prompt caching
* semantic caching
* agent memory
* concurrency
* model routing
* token budgets

The reason is simple:

> Optimization without a baseline is speculation.

We first establish the baseline.

Then we measure.

Then we optimize.

---

# 21. Lesson 0 Completion Criteria

Lesson 0 is complete when:

* [ ] Git repository exists
* [ ] Python environment is working
* [ ] `uv` manages dependencies
* [ ] FastAPI starts successfully
* [ ] `/health` responds successfully
* [ ] PostgreSQL is running
* [ ] CRM schema exists
* [ ] Pydantic models exist
* [ ] Configuration is externalized
* [ ] `.env` is excluded from Git
* [ ] pytest passes
* [ ] Ruff passes
* [ ] Initial Git checkpoint exists

---

# 22. Key Takeaways

The most important lessons from this stage are not the commands.

They are architectural.

### First

An AI application is still a software system.

We therefore begin with:

```text
application
database
configuration
testing
observability foundations
```

### Second

LLMs are probabilistic components.

We will need deterministic controls around them.

### Third

The CRM is our persistent learning environment.

The dataset will remain with us as the system evolves.

### Fourth

Frameworks are abstractions, not fundamentals.

We will understand the primitives before adopting higher-level frameworks.

### Fifth

Every optimization must have a measurable baseline.

This principle will guide our work on:

```text
tokens
cost
latency
memory
retrieval
agent performance
```

---

# 23. Next Lesson

## Lesson 1 — What Actually Happens When an LLM Generates Text?

We will make our first real LLM call.

We will investigate:

```text
Application
    ↓
Messages
    ↓
Tokenization
    ↓
Input tokens
    ↓
Model inference
    ↓
Output tokens
    ↓
Sampling / decoding
    ↓
Response
```

We will implement the call in Python without an agent framework.

We will also capture our first:

```text
input token count
output token count
total token count
latency
estimated cost
```

This begins the **Token Economics + Observability** track from the very first LLM interaction.

---

**Checkpoint:** `Lesson 0 — Laboratory Foundation`

**Next checkpoint:** `Lesson 1 — First LLM Interaction`
