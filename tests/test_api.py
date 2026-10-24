"""Integration tests for the FastAPI backend (research_assistant.api).

Hermetic: the service layer is replaced with a MagicMock container, so no
OpenAI calls, network access, or ChromaDB persistence ever happen.
"""

import os

# Config() raises ValueError when OPENAI_API_KEY is missing, so set it BEFORE
# importing research_assistant.api (or anything importing config).
os.environ["OPENAI_API_KEY"] = "sk-test-fake-1234567890"

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import research_assistant.api as api


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def fake_container():
    """Swap the module-global container for a fake; never build the real one."""
    container = MagicMock()
    api._container = container
    yield container
    api._container = None


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_research_success(fake_container, client):
    result = {"topic": "Transformers", "report": "A report", "papers": 3}
    fake_container.research.run.return_value = result

    resp = client.post(
        "/api/research",
        json={
            "topic": "Transformers",
            "max_papers": 3,
            "summary_style": "bullet_points",
            "sources": ["https://example.com"],
        },
    )

    assert resp.status_code == 200
    assert resp.json() == result
    fake_container.research.run.assert_called_once_with(
        topic="Transformers",
        max_papers=3,
        summary_style="bullet_points",
        sources=["https://example.com"],
    )


def test_research_error_400(fake_container, client):
    fake_container.research.run.return_value = {"error": "No sources found for topic"}

    resp = client.post("/api/research", json={"topic": "Nothing"})

    assert resp.status_code == 400
    assert resp.json() == {"detail": "No sources found for topic"}


def test_chat_send(fake_container, client):
    fake_container.chat.send.return_value = {"answer": "42", "session_id": "s1"}

    resp = client.post(
        "/api/chat/send", json={"session_id": "s1", "question": "Meaning of life?", "k": 3}
    )

    assert resp.status_code == 200
    assert resp.json() == {"answer": "42", "session_id": "s1"}
    fake_container.chat.send.assert_called_once_with("s1", "Meaning of life?", k=3)


def test_chat_send_defaults(fake_container, client):
    fake_container.chat.send.return_value = {"answer": "ok"}

    resp = client.post("/api/chat/send", json={"question": "hi"})

    assert resp.status_code == 200
    fake_container.chat.send.assert_called_once_with("default", "hi", k=None)


def test_chat_clear(fake_container, client):
    fake_container.chat.clear.return_value = {"ok": True, "session_id": "s1"}

    resp = client.post("/api/chat/clear", json={"session_id": "s1"})

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    fake_container.chat.clear.assert_called_once_with("s1")


def test_chat_history(fake_container, client):
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    fake_container.chat.history.return_value = {"session_id": "s1", "history": history}

    resp = client.get("/api/chat/s1/history")

    assert resp.status_code == 200
    assert resp.json() == {"session_id": "s1", "history": history}
    fake_container.chat.history.assert_called_once_with("s1")


def test_compare(fake_container, client):
    result = {"comparison": "Paper A is stronger on X.", "sources": []}
    fake_container.chat.compare.return_value = result

    resp = client.post(
        "/api/compare",
        json={"paper_ids": ["p1", "p2"], "question": "Which is better?", "k_per_paper": 5},
    )

    assert resp.status_code == 200
    assert resp.json() == result
    fake_container.chat.compare.assert_called_once_with(
        ["p1", "p2"], "Which is better?", k_per_paper=5
    )


def test_papers(fake_container, client):
    fake_container.workspace_service.list_papers.return_value = [
        {"id": "p1", "title": "Attention Is All You Need"}
    ]

    resp = client.get("/api/papers")

    assert resp.status_code == 200
    assert resp.json() == {"papers": [{"id": "p1", "title": "Attention Is All You Need"}]}


def test_search(fake_container, client):
    fake_container.workspace_service.search.return_value = [
        {"chunk": "self-attention", "score": 0.9}
    ]

    resp = client.post("/api/search", json={"query": "attention", "k": 5})

    assert resp.status_code == 200
    assert resp.json() == {"results": [{"chunk": "self-attention", "score": 0.9}]}
    fake_container.workspace_service.search.assert_called_once_with("attention", k=5)


def test_workspace(fake_container, client):
    summary = {"markdown": "# Workspace", "counts": {"papers": 3, "notes": 1}}
    fake_container.workspace_service.summary.return_value = summary

    resp = client.get("/api/workspace")

    assert resp.status_code == 200
    assert resp.json() == summary
    assert isinstance(resp.json()["markdown"], str)
    assert isinstance(resp.json()["counts"], dict)


def test_delete_paper(fake_container, client):
    fake_container.workspace_service.delete_paper.return_value = {"ok": True, "paper_id": "p1"}

    resp = client.delete("/api/papers/p1")

    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "paper_id": "p1"}
    fake_container.workspace_service.delete_paper.assert_called_once_with("p1")


def test_validation_422(fake_container, client):
    """Bad bodies must be rejected by real pydantic validation (endpoint never runs)."""
    cases = [
        ("post", "/api/research", {"topic": ""}),
        ("post", "/api/research", {"topic": "x", "max_papers": 0}),
        ("post", "/api/research", {"topic": "x", "max_papers": 21}),
        ("post", "/api/chat/send", {"session_id": "s", "question": ""}),
        ("post", "/api/chat/send", {"session_id": "s", "question": "q", "k": 0}),
        ("post", "/api/chat/send", {"session_id": "s", "question": "q", "k": 21}),
        ("post", "/api/compare", {"paper_ids": ["p1"], "question": "q"}),
        ("post", "/api/compare", {"paper_ids": ["p1", "p2"], "question": "q", "k_per_paper": 11}),
        ("post", "/api/search", {"query": ""}),
        ("post", "/api/search", {"query": "q", "k": 51}),
    ]
    for method, path, body in cases:
        resp = getattr(client, method)(path, json=body)
        assert resp.status_code == 422, f"{method.upper()} {path} {body} -> {resp.status_code}"

    # Validation failed before any service call happened.
    fake_container.research.run.assert_not_called()
    fake_container.chat.send.assert_not_called()
    fake_container.chat.compare.assert_not_called()
    fake_container.workspace_service.search.assert_not_called()
