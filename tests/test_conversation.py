import json

import pytest
from unittest.mock import patch, MagicMock

from research_assistant.agents.conversation import ChatSession, COMPARE_SYSTEM
from research_assistant.workspace import ResearchWorkspace


def _result(paper_id, title, document, i=0):
    """Build a vector-store search result dict shaped like rag's outputs."""
    return {
        "id": f"{paper_id}_chunk_{i}",
        "document": document,
        "metadata": {
            "paper_id": paper_id,
            "title": title,
            "source": "arXiv",
            "url": f"https://arxiv.org/abs/{paper_id}",
            "chunk_index": i,
        },
        "distance": 0.1 + i,
    }


@pytest.fixture
def canned_answer():
    return {
        "answer": "The answer.",
        "sources": [{"title": "Paper A", "source": "arXiv", "url": "u"}],
        "chunks": 1,
        "citations": [{"title": "Paper A", "source": "arXiv", "url": "u"}],
    }


@pytest.fixture
def mock_openai():
    with patch("research_assistant.agents.conversation.OpenAI") as mo:
        client = MagicMock()
        mo.return_value = client
        yield mo, client


class TestAsk:
    def test_ask_persists_history_and_citation(self, tmp_path, canned_answer):
        rag = MagicMock()
        rag.answer.return_value = canned_answer
        ws = ResearchWorkspace(base_dir=str(tmp_path))
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        session.ask("first question")
        session.ask("second question")

        assert len(session.get_history()) == 4
        assert len(ws.load_chat("s1")) == 4
        assert ws.list_citations()  # at least one citation file recorded

    def test_ask_blank_question(self, tmp_path):
        rag = MagicMock()
        ws = ResearchWorkspace(base_dir=str(tmp_path))
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        result = session.ask("   ")

        assert "Please enter a question" in result["answer"]
        assert result["chunks"] == 0
        rag.answer.assert_not_called()

    def test_ask_passes_history_to_rag(self, tmp_path, canned_answer):
        rag = MagicMock()
        rag.answer.return_value = canned_answer
        ws = ResearchWorkspace(base_dir=str(tmp_path))
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        session.ask("first question")
        session.ask("second question")

        call = rag.answer.call_args
        assert call.kwargs["history"] == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "The answer."},
        ]

    def test_clear_resets_history(self, tmp_path, canned_answer):
        rag = MagicMock()
        rag.answer.return_value = canned_answer
        ws = ResearchWorkspace(base_dir=str(tmp_path))
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        session.ask("hello")
        session.clear()

        assert session.get_history() == []
        assert ws.load_chat("s1") == []

    def test_history_loaded_from_workspace_on_init(self, tmp_path):
        ws = ResearchWorkspace(base_dir=str(tmp_path))
        ws.save_chat(
            "s1",
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )
        rag = MagicMock()
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        assert len(session.get_history()) == 2


class TestComparePapers:
    def test_compare_papers_returns_structured_answer(self, mock_openai):
        mo, client = mock_openai
        rag = MagicMock()
        rag.vector_store.search.return_value = [
            _result("p1", "Paper A", "Paper 1 uses X.", 0),
            _result("p2", "Paper B", "Paper 2 uses Y.", 0),
        ]
        ws = MagicMock()
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=json.dumps(
                            {
                                "answer": "Paper 1 uses X, Paper 2 uses Y",
                                "citations": [{"title": "A", "source": "arxiv", "url": "u"}],
                            }
                        )
                    )
                )
            ]
        )

        result = session.compare_papers(["p1", "p2"], "Compare these papers")

        assert result["answer"] == "Paper 1 uses X, Paper 2 uses Y"
        assert len(result["sources"]) == 2
        assert result["citations"] == [{"title": "A", "source": "arxiv", "url": "u"}]
        assert result["chunks"] == 2
        rag.vector_store.search.assert_called_once_with(query="Compare these papers", k=20)

    def test_compare_papers_filters_to_requested_ids(self, mock_openai):
        mo, client = mock_openai
        rag = MagicMock()
        rag.vector_store.search.return_value = [
            _result("p1", "Paper 1", "p1 content here", 0),
            _result("p2", "Paper 2", "p2 content here", 0),
            _result("p3", "Paper 3", "p3 secret content", 0),
        ]
        ws = MagicMock()
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"answer": "ok", "citations": []}'))]
        )

        session.compare_papers(["p1", "p2"], "Compare")

        user_msg = client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "p1 content here" in user_msg
        assert "p2 content here" in user_msg
        assert "p3 secret content" not in user_msg

    def test_compare_papers_too_few_papers(self, mock_openai):
        mo, client = mock_openai
        rag = MagicMock()
        rag.vector_store.search.return_value = [_result("p1", "Paper 1", "content", 0)]
        ws = MagicMock()
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        result = session.compare_papers(["p1"], "Compare")

        assert "at least two papers" in result["answer"]
        assert result["chunks"] == 0
        mo.assert_not_called()  # OpenAI client never constructed
        client.chat.completions.create.assert_not_called()

    def test_compare_papers_error_fallback(self, mock_openai):
        mo, client = mock_openai
        rag = MagicMock()
        rag.vector_store.search.return_value = [
            _result("p1", "Paper A", "a", 0),
            _result("p2", "Paper B", "b", 0),
        ]
        ws = MagicMock()
        session = ChatSession(api_key="sk-test-fake", rag=rag, workspace=ws, session_id="s1")

        client.chat.completions.create.side_effect = Exception("api down")

        result = session.compare_papers(["p1", "p2"], "Compare")

        assert result["answer"].startswith("Error comparing papers")
        assert len(result["sources"]) == 2
        assert result["citations"] == []
