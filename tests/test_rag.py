import pytest
from unittest.mock import patch, MagicMock
from research_assistant.agents.rag import RAGAssistant, SYSTEM_PROMPT


def _sample_results(n=2):
    return [
        {
            "id": f"paper_a_chunk_000{i}",
            "document": f"Attention mechanisms enable models to focus on relevant tokens. Chunk {i} content here.",
            "metadata": {
                "paper_id": "paper_a",
                "title": "Attention Is All You Need",
                "source": "arXiv",
                "url": "https://arxiv.org/abs/1234.5678",
                "chunk_index": i,
            },
            "distance": 0.1 + i,
        }
        for i in range(n)
    ]


class TestRAGContext:
    def test_build_context_numbered_headers(self):
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=None)
        context = rag._build_context(_sample_results(2))
        assert "[1] (Attention Is All You Need — arXiv)" in context
        assert "[2] (Attention Is All You Need — arXiv)" in context
        assert "Chunk 0 content" in context
        assert "Chunk 1 content" in context

    def test_build_context_truncates_to_budget(self):
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=None, max_context_chars=200)
        context = rag._build_context(_sample_results(2))
        assert len(context) <= 200 + 20  # allow slack for the truncation marker logic

    def test_build_sources_dedupes_by_title(self):
        results = _sample_results(3) + [
            {
                "id": "paper_b_chunk_0000",
                "document": "other",
                "metadata": {"title": "Attention Is All You Need", "source": "arXiv", "url": ""},
                "distance": 0.5,
            }
        ]
        sources = RAGAssistant._build_sources(results)
        assert len(sources) == 1
        assert sources[0]["title"] == "Attention Is All You Need"
        assert sources[0]["url"] == "https://arxiv.org/abs/1234.5678"

    def test_build_sources_preserves_order(self):
        results = [
            {**r, "metadata": {**r["metadata"], "title": f"Paper {i}"}}
            for i, r in enumerate(_sample_results(3))
        ]
        sources = RAGAssistant._build_sources(results)
        assert [s["title"] for s in sources] == ["Paper 0", "Paper 1", "Paper 2"]


class TestRAGAnswer:
    @pytest.fixture
    def mock_store(self):
        store = MagicMock()
        return store

    @pytest.fixture
    def mock_openai(self):
        with patch("research_assistant.agents.rag.OpenAI") as mo:
            client = MagicMock()
            mo.return_value = client
            yield client

    def test_answer_empty_question(self, mock_openai):
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=MagicMock())
        result = rag.answer("   ")
        assert "Please enter a question" in result["answer"]
        assert result["chunks"] == 0
        mock_openai.chat.completions.create.assert_not_called()

    def test_answer_no_results(self, mock_openai, mock_store):
        mock_store.search.return_value = []
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        result = rag.answer("anything")
        assert "No relevant paper content" in result["answer"]
        assert result["sources"] == []
        assert result["chunks"] == 0
        mock_openai.chat.completions.create.assert_not_called()

    def test_answer_calls_openai_with_context_and_citations(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(2)
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="The answer is [1]."))]
        )
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        result = rag.answer("How do attention mechanisms work?")

        assert result["answer"] == "The answer is [1]."
        assert result["chunks"] == 2
        assert len(result["sources"]) == 1

        mock_store.search.assert_called_once_with("How do attention mechanisms work?", k=5)
        call = mock_openai.chat.completions.create.call_args
        kwargs = call.kwargs
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["temperature"] == 0.2
        system_msg = kwargs["messages"][0]["content"]
        user_msg = kwargs["messages"][1]["content"]
        assert system_msg == SYSTEM_PROMPT
        assert "Question: How do attention mechanisms work?" in user_msg
        assert "Attention Is All You Need" in user_msg

    def test_answer_custom_k(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(1)
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="ok"))]
        )
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store, top_k=3)
        rag.answer("question", k=7)
        mock_store.search.assert_called_once_with("question", k=7)

    def test_answer_openai_error_returns_sources(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(1)
        mock_openai.chat.completions.create.side_effect = Exception("api down")
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        result = rag.answer("question")
        assert "Error generating answer" in result["answer"]
        assert result["chunks"] == 1
        assert result["sources"]  # sources still surfaced

    def test_answer_injects_history_messages(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(1)
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="follow-up answer"))]
        )
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        history = [
            {"role": "user", "content": "What is attention?"},
            {"role": "assistant", "content": "Attention is [1]."},
        ]
        rag.answer("And how does it scale?", history=history)
        call = mock_openai.chat.completions.create.call_args
        messages = call.kwargs["messages"]
        assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
        assert messages[1]["content"] == "What is attention?"
        assert messages[2]["content"] == "Attention is [1]."

    def test_answer_structured_requests_json_and_parses(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(1)
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=(
                            '{"answer": "Structured answer [1].", '
                            '"citations": [{"title": "Attention Is All You Need", '
                            '"source": "arXiv", "url": "https://arxiv.org/abs/1706.03762"}]}'
                        )
                    )
                )
            ]
        )
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        result = rag.answer("question", structured=True)
        call = mock_openai.chat.completions.create.call_args
        assert call.kwargs["response_format"] == {"type": "json_object"}
        assert result["answer"] == "Structured answer [1]."
        assert result["citations"][0]["title"] == "Attention Is All You Need"

    def test_answer_structured_parse_failure_falls_back(self, mock_openai, mock_store):
        mock_store.search.return_value = _sample_results(1)
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="```json\nnot json here\n```"))]
        )
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=mock_store)
        result = rag.answer("question", structured=True)
        assert result["answer"] == "```json\nnot json here\n```"
        assert result["citations"] == result["sources"]  # retrieval-based fallback

    def test_parse_json_tolerates_fences_and_prose(self):
        rag = RAGAssistant(api_key="sk-test-fake", vector_store=None)
        assert rag._parse_json('{"a": 1}') == {"a": 1}
        assert rag._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
        assert rag._parse_json('Here: {"a": 1} trailing') == {"a": 1}
        assert rag._parse_json("no json here") is None
        assert rag._parse_json("") is None
