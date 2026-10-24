"""Chat service: sessioned conversational RAG + multi-paper comparison."""

import logging
from typing import Any

from ..agents.conversation import ChatSession

logger = logging.getLogger(__name__)


class ChatService:
    """Manage persistent ChatSession instances keyed by session_id.

    History is persisted to the workspace's Chat History dir by ChatSession.
    """
    def __init__(
        self,
        api_key: str,
        rag,
        workspace,
        model: str = "gpt-4o-mini",
        top_k: int = 5,
    ):
        self.api_key = api_key
        self.rag = rag
        self.workspace = workspace
        self.model = model
        self.top_k = top_k
        self._sessions: dict[str, ChatSession] = {}

    def _session(self, session_id: str = "default") -> ChatSession:
        session_id = session_id or "default"
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(
                api_key=self.api_key,
                rag=self.rag,
                workspace=self.workspace,
                session_id=session_id,
                model=self.model,
                top_k=self.top_k,
            )
        return self._sessions[session_id]

    def send(self, session_id: str, question: str, k: int | None = None) -> dict[str, Any]:
        """Ask a question in a session; returns the structured RAG result."""
        session = self._session(session_id)
        result = session.ask(question, k=k)
        result["session_id"] = session_id
        result["history"] = session.get_history()
        return result

    def clear(self, session_id: str = "default") -> dict[str, Any]:
        """Reset a session's conversation history."""
        session = self._session(session_id)
        session.clear()
        return {"ok": True, "session_id": session_id}

    def history(self, session_id: str = "default") -> dict[str, Any]:
        """Return a session's persisted conversation history."""
        session = self._session(session_id)
        return {"session_id": session_id, "history": session.get_history()}

    def compare(
        self,
        paper_ids: list[str],
        question: str,
        k_per_paper: int = 3,
    ) -> dict[str, Any]:
        """Compare multiple stored papers with a structured, sourced answer."""
        session = self._session("compare")
        if not paper_ids or len(paper_ids) < 2:
            return {
                "answer": "Please select at least two papers to compare.",
                "sources": [],
                "chunks": 0,
                "citations": [],
            }
        return session.compare_papers(paper_ids, question, k_per_paper=k_per_paper)

    def list_sessions(self) -> list[str]:
        return self.workspace.list_chats()
