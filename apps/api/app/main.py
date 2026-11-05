from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agents.simple_agent import SimpleAgent
from app.llm.ollama import OllamaClient
from app.llm.structured import StructuredLLM

STATIC_DIR = Path(__file__).parent / "static"

# Lazy-loaded agent instance
agent: SimpleAgent | None = None


def get_agent() -> SimpleAgent:
    global agent
    if agent is None:
        llm = OllamaClient()
        structured_llm = StructuredLLM(llm)
        agent = SimpleAgent(llm=llm, structured_llm=structured_llm)
    return agent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Warm up agent on startup
    get_agent()
    yield


app = FastAPI(
    title="Agentic AI Lab",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to the agent")
    conversation_id: str = Field(default="demo-001", description="Unique conversation session ID")
    user_id: str = Field(default="default-user", description="Stable user identifier for durable memory")


class MemoryItemResponse(BaseModel):
    id: str
    type: str
    key: str
    value: str
    source: str
    confidence: float


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    user_memories: list[dict[str, Any]]
    conversation_memories: list[dict[str, Any]]
    summary: str | None = None
    messages_count: int
    memory_histories: list[dict[str, Any]]


@app.get("/health")
async def healthy():
    return {"status": "ok", "service": "agentic-ai-lab"}


@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Agentic AI Lab API is running. UI not found at static/index.html"}


@app.get("/api/sample-queries")
async def get_sample_queries():
    return [
        {
            "category": "Memory & Preferences",
            "icon": "brain",
            "queries": [
                "Remember that I prefer Acme over Globex.",
                "My executive summaries should be under 100 words.",
                'For this discussion, call this strategy "Project Phoenix".',
                "I prefer technical recommendations to explicitly include tradeoffs.",
            ],
        },
        {
            "category": "Memory Recall",
            "icon": "sparkles",
            "queries": [
                "Which company should we prioritize?",
                "What is my executive summary constraint?",
                "What is the name of my strategy?",
                "Give me all the preferences, decisions, and terminology you remember from the beginning.",
            ],
        },
        {
            "category": "CRM & Knowledge Tools",
            "icon": "database",
            "queries": [
                "Who is the CEO of Acme Corporation?",
                "What security concerns has Acme raised?",
                "Who raised them?",
                "What integration requirements does Acme have?",
            ],
        },
    ]


@app.get("/api/conversations")
async def list_conversations():
    ag = get_agent()
    conversations = []
    for conv_id, msgs in ag.conversations.items():
        memories = ag.memory_store.get_memories(conv_id)
        summary = ag.conversation_summaries.get(conv_id)
        user_msgs = [m for m in msgs if m.get("role") == "user"]
        last_msg = user_msgs[-1]["content"] if user_msgs else "New conversation"
        conversations.append(
            {
                "conversation_id": conv_id,
                "message_count": len(msgs),
                "memory_count": len(memories),
                "has_summary": bool(summary),
                "last_message": last_msg[:60] + "..." if len(last_msg) > 60 else last_msg,
            }
        )
    return conversations


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user_id: str = "default-user"):
    ag = get_agent()
    history = ag.get_conversation_history(conversation_id)
    raw_user_mems = ag.memory_store.get_user_memories(user_id)
    raw_conv_mems = ag.memory_store.get_conversation_memories(conversation_id)
    summary = ag.conversation_summaries.get(conversation_id)
    memory_histories = ag.memory_store.get_history(conversation_id)

    return {
        "conversation_id": conversation_id,
        "history": history,
        "user_memories": [m.model_dump() for m in raw_user_mems],
        "conversation_memories": [m.model_dump() for m in raw_conv_mems],
        "summary": summary,
        "messages_count": len(history),
        "memory_histories": memory_histories,
    }


@app.post("/api/conversations/{conversation_id}/reset")
async def reset_conversation(conversation_id: str):
    ag = get_agent()
    ag.reset_conversation(conversation_id)
    return {
        "status": "reset",
        "conversation_id": conversation_id,
        "message": f"Conversation '{conversation_id}' and memory cleared.",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    ag = get_agent()
    try:
        reply = await ag.run(
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        raw_user_mems = ag.memory_store.get_user_memories(request.user_id)
        raw_conv_mems = ag.memory_store.get_conversation_memories(request.conversation_id)
        summary = ag.conversation_summaries.get(request.conversation_id)
        history = ag.get_conversation_history(request.conversation_id)
        memory_histories = ag.memory_store.get_history(request.conversation_id)

        return ChatResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            user_memories=[m.model_dump() for m in raw_user_mems],
            conversation_memories=[m.model_dump() for m in raw_conv_mems],
            summary=summary,
            messages_count=len(history),
            memory_histories=memory_histories,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
