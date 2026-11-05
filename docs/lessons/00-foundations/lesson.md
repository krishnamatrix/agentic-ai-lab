# Lesson 0 — Step-by-Step Laboratory Setup

> **Agentic AI Engineering Lab**
>
> This document is the hands-on setup guide for Lesson 0.
>
> Follow the steps in order.

---

# 1. Prerequisites

Before starting, verify that the following are available:

* Git
* Docker
* Terminal
* VS Code or another IDE
* Internet access

We will install Python through `uv`, so a separate Python installation is not strictly required.

---

# 2. Verify Git

Run:

```bash
git --version
```

Expected output:

```text
git version ...
```

If Git is not installed, install it for your operating system before continuing.

---

# 3. Install `uv`

We use `uv` as the Python project and dependency manager.

### macOS / Linux

Run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal if necessary.

Verify:

```bash
uv --version
```

Expected:

```text
uv ...
```

---

# 4. Create the Project

Create the root directory:

```bash
mkdir agentic-ai-lab
cd agentic-ai-lab
```

Initialize Git:

```bash
git init
```

---

# 5. Create the Directory Structure

Run:

```bash
mkdir -p apps/api
mkdir -p data/seed
mkdir -p data/generated
mkdir -p docs/lessons
mkdir -p docs/architecture
mkdir -p docs/experiments
mkdir -p docs/failures
mkdir -p experiments
mkdir -p evaluations
mkdir -p scripts
```

Create the root README:

```bash
touch README.md
```

The initial structure should look like:

```text
agentic-ai-lab/
├── apps/
│   └── api/
├── data/
│   ├── seed/
│   └── generated/
├── docs/
│   ├── lessons/
│   ├── architecture/
│   ├── experiments/
│   └── failures/
├── experiments/
├── evaluations/
├── scripts/
└── README.md
```

---

# 6. Initialize the Python Project

Move into the API directory:

```bash
cd apps/api
```

Initialize the Python project:

```bash
uv init
```

Verify:

```bash
ls
```

You should see a `pyproject.toml`.

---

# 7. Select Python

Pin the project to Python 3.13:

```bash
uv python pin 3.13
```

Create/synchronize the environment:

```bash
uv sync
```

Verify:

```bash
uv run python --version
```

Expected:

```text
Python 3.13.x
```

---

# 8. Install Runtime Dependencies

Install FastAPI:

```bash
uv add fastapi
```

Install Uvicorn:

```bash
uv add "uvicorn[standard]"
```

Install Pydantic:

```bash
uv add pydantic
```

Install Pydantic Settings:

```bash
uv add pydantic-settings
```

---

# 9. Install Development Dependencies

Install pytest:

```bash
uv add --dev pytest
```

Install HTTPX:

```bash
uv add --dev httpx
```

Install Ruff:

```bash
uv add --dev ruff
```

Synchronize:

```bash
uv sync
```

Add to `apps/api/pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = "."
```

---

# 10. Create the Application Structure

From:

```text
apps/api
```

create:

```bash
mkdir -p app/models
mkdir -p tests

touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/models/__init__.py
touch app/models/crm.py
touch tests/test_health.py
```

The structure should now be:

```text
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── models/
│       ├── __init__.py
│       └── crm.py
│
├── tests/
│   └── test_health.py
│
├── pyproject.toml
└── .python-version
```

---

# 11. Create the FastAPI Application

Open:

```text
app/main.py
```

Add:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Agentic AI Lab",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "agentic-ai-lab",
    }
```

---

# 12. Start the API

From:

```text
apps/api
```

run:

```bash
uv run uvicorn app.main:app --reload
```

Expected output will contain something similar to:

```text
Uvicorn running on http://127.0.0.1:8000
```

---

# 13. Test the Health Endpoint

Open:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "agentic-ai-lab"
}
```

---

# 14. Open FastAPI Swagger Documentation

Open:

```text
http://localhost:8000/docs
```

You should see the automatically generated FastAPI API documentation.

This confirms that FastAPI is correctly running.

---

# 15. Verify the API from the Terminal

Open another terminal.

From:

```text
apps/api
```

run:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","service":"agentic-ai-lab"}
```

---

# 16. Start PostgreSQL

We will use Docker for the initial PostgreSQL environment.

From any directory:

```bash
docker run \
  --name agentic-ai-postgres \
  -e POSTGRES_USER=agentic \
  -e POSTGRES_PASSWORD=agentic \
  -e POSTGRES_DB=crm \
  -p 5432:5432 \
  -d postgres:17
```

Verify:

```bash
docker ps
```

You should see:

```text
agentic-ai-postgres
```

---

# 17. Verify PostgreSQL

Run:

```bash
docker exec -it agentic-ai-postgres \
  psql -U agentic -d crm
```

You should enter the PostgreSQL shell.

Run:

```sql
SELECT version();
```

Then:

```sql
\q
```

to exit.

---

# 18. Create the CRM Database Schema

Create a SQL file:

```text
data/seed/001_initial_schema.sql
```

From the repository root:

```bash
touch data/seed/001_initial_schema.sql
```

Add:

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    employee_count INTEGER,
    annual_revenue NUMERIC,
    headquarters TEXT,
    website TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE people (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT,
    email TEXT,
    phone TEXT,
    location TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    interaction_type TEXT NOT NULL,
    subject TEXT,
    content TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE opportunities (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    name TEXT NOT NULL,
    stage TEXT NOT NULL,
    value NUMERIC,
    probability NUMERIC,
    expected_close_date DATE,
    owner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE notes (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    content TEXT NOT NULL,
    author TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 19. Apply the Schema

From the repository root:

```bash
docker exec -i agentic-ai-postgres \
  psql -U agentic -d crm \
  < data/seed/001_initial_schema.sql
```

---

# 20. Verify the Tables

Run:

```bash
docker exec -it agentic-ai-postgres \
  psql -U agentic -d crm
```

Then:

```sql
\dt
```

You should see:

```text
companies
people
interactions
opportunities
notes
```

Exit:

```sql
\q
```

---

# 21. Create Environment Configuration

Go to:

```text
apps/api
```

Create:

```bash
touch .env
```

Add:

```env
APP_ENV=development
DATABASE_URL=postgresql://agentic:agentic@localhost:5432/crm
```

Do not commit this file.

---

# 22. Create Configuration Management

Open:

```text
apps/api/app/config.py
```

Add:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
```

---

# 23. Create the CRM Pydantic Model

Open:

```text
apps/api/app/models/crm.py
```

Add:

```python
from pydantic import BaseModel


class Company(BaseModel):
    id: str
    name: str
    industry: str | None = None
    employee_count: int | None = None
    annual_revenue: float | None = None
    headquarters: str | None = None
    website: str | None = None
```

At this stage we only create the Company model.

Additional models will be added as the application requires them.

---

# 24. Create the First Test

Open:

```text
apps/api/tests/test_health.py
```

Add:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

# 25. Run Tests

From:

```text
apps/api
```

run:

```bash
uv run pytest
```

Expected result:

```text
1 passed
```

The exact formatting may differ depending on the pytest version.

---

# 26. Run Ruff

Run:

```bash
uv run ruff check .
```

Then:

```bash
uv run ruff format .
```

Run the check again:

```bash
uv run ruff check .
```

The goal is a clean result.

---

# 27. Create the Git Ignore File

Return to the repository root:

```bash
cd ../..
```

Create:

```bash
touch .gitignore
```

Add:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.env
*.pyc
.DS_Store
```

---

# 28. Verify Git Status

Run:

```bash
git status
```

Make sure `.env` is not listed as an untracked file.

If `.env` appears, stop and fix `.gitignore` before committing.

---

# 29. Inspect the Repository

Run:

```bash
find . -maxdepth 4 -type f \
  | grep -v ".git/" \
  | sort
```

You should have a structure broadly similar to:

```text
./.gitignore
./README.md
./apps/api/.python-version
./apps/api/app/__init__.py
./apps/api/app/config.py
./apps/api/app/main.py
./apps/api/app/models/__init__.py
./apps/api/app/models/crm.py
./apps/api/pyproject.toml
./apps/api/tests/test_health.py
./data/seed/001_initial_schema.sql
```

---

# 30. Run the Complete Verification

Perform these checks:

### Python

```bash
cd apps/api
uv run python --version
```

### Tests

```bash
uv run pytest
```

### Ruff

```bash
uv run ruff check .
```

### API

```bash
uv run uvicorn app.main:app --reload
```

### Database

From another terminal:

```bash
docker exec -it agentic-ai-postgres \
  psql -U agentic -d crm
```

Then:

```sql
\dt
```

---

# 31. Create the Lesson Documentation

From the repository root:

```bash
mkdir -p docs/lessons/00-foundations
```

Place the two lesson files here:

```text
docs/lessons/00-foundations/
├── README.md
└── lesson.md
```

The files have different purposes.

### README.md

The file you are reading now.

It answers:

> What commands do I run?

### lesson.md

The conceptual lesson.

It answers:

> Why are we doing this and what did we learn?

---

# 32. Create the First Git Checkpoint

From the repository root:

```bash
git add .
```

Review:

```bash
git status
```

Commit:

```bash
git commit -m "chore: initialize agentic AI laboratory"
```

Verify:

```bash
git log --oneline -1
```

You should see your new commit.

---

# 33. Checkpoint

At this point we have:

```text
┌─────────────────────────────────────┐
│       Agentic AI Engineering Lab    │
├─────────────────────────────────────┤
│                                     │
│ Python 3.13                         │
│ uv                                  │
│ FastAPI                             │
│ Pydantic                            │
│ PostgreSQL                          │
│ pytest                              │
│ Ruff                                │
│ Git                                 │
│                                     │
│ CRM schema                          │
│                                     │
└─────────────────────────────────────┘
```

No AI has been added yet.

That is intentional.

---

# 34. Troubleshooting

## `uv: command not found`

Restart your terminal after installing `uv`.

Then:

```bash
uv --version
```

If it still isn't found, verify that the `uv` installation directory is in your `PATH`.

---

## Python version is incorrect

Run:

```bash
uv python list
```

Then:

```bash
uv python pin 3.13
```

And:

```bash
uv sync
```

Verify:

```bash
uv run python --version
```

---

## PostgreSQL container already exists

If Docker reports:

```text
Conflict. The container name is already in use
```

Check:

```bash
docker ps -a
```

If it is the container created for this project:

```bash
docker start agentic-ai-postgres
```

Then verify:

```bash
docker ps
```

---

## PostgreSQL port 5432 is already in use

Check:

```bash
lsof -i :5432
```

If another PostgreSQL instance is already running, you can either use it or change the Docker mapping.

For example:

```bash
docker run \
  --name agentic-ai-postgres \
  -e POSTGRES_USER=agentic \
  -e POSTGRES_PASSWORD=agentic \
  -e POSTGRES_DB=crm \
  -p 5433:5432 \
  -d postgres:17
```

If you do this, update:

```env
DATABASE_URL=postgresql://agentic:agentic@localhost:5433/crm
```

---

## FastAPI import error

Make sure you are running the command from:

```text
apps/api
```

and use:

```bash
uv run uvicorn app.main:app --reload
```

---

## pytest cannot import `app`

Make sure you are running:

```bash
uv run pytest
```

from:

```text
apps/api
```

---

# 35. Do Not Install These Yet

Do not add these dependencies during Lesson 0:

```text
LangChain
LangGraph
LlamaIndex
pgvector
Chroma
Pinecone
Redis
Ollama
MCP SDKs
Agent frameworks
```

They will be introduced deliberately in later lessons.

---

# 36. Lesson Completion Checklist

Mark each item when completed:

* [ ] Git repository created
* [ ] `uv` installed
* [ ] Python 3.13 configured
* [ ] FastAPI installed
* [ ] Pydantic installed
* [ ] pytest installed
* [ ] Ruff installed
* [ ] FastAPI `/health` endpoint works
* [ ] Swagger documentation works
* [ ] PostgreSQL container running
* [ ] CRM database created
* [ ] Five CRM tables created
* [ ] Environment configuration created
* [ ] Pydantic Company model created
* [ ] Health test created
* [ ] pytest passes
* [ ] Ruff passes
* [ ] `.env` excluded from Git
* [ ] Initial Git commit created
* [ ] `docs/lessons/00-foundations/README.md` created
* [ ] `docs/lessons/00-foundations/lesson.md` created

---

# 37. Next Step

Once every item above is complete, move to:

**Lesson 1 — LLM Fundamentals and the First Model Call**

The first AI capability we introduce will be intentionally simple:

```text
Python
   ↓
LLM API
   ↓
Response
```

We will instrument that first call from the beginning.

We will capture:

```text
model
input tokens
output tokens
total tokens
latency
cost
request ID
errors
```

This establishes the first version of our **LLM Gateway** and begins the Token Economics and Observability tracks.

---

**Current checkpoint:** `Lesson 0`

**Next checkpoint:** `Lesson 1`

**Repository state:** Deterministic foundation complete
