from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Agentic CRM Assistant" in response.text


def test_sample_queries_endpoint():
    response = client.get("/api/sample-queries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert any(cat["category"] == "Memory & Preferences" for cat in data)


def test_conversations_endpoint():
    response = client.get("/api/conversations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_conversation_reset():
    response = client.post("/api/conversations/test-session/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "reset"
