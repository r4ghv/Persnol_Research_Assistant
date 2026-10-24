import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .rag import RAGAssistant

logger = logging.getLogger(__name__)

COMPARE_SYSTEM = """You are a research assistant comparing multiple academic papers. Use ONLY the paper excerpts provided. Follow these rules strictly:

1. Compare the papers on methodology, findings, and limitations; highlight agreements and disagreements.
2. Cite each paper inline with its numbered bracket, e.g. [1], [2], matching the paper order in the context.
3. If the excerpts do not contain enough information for a claim, say so instead of fabricating.
4. Respond ONLY with a valid JSON object with exactly two keys: "answer" (string) and "citations" (array of objects with "title", "source", "url" keys)."""


class ChatSession:
    """Conversational RAG with persistent history and multi-paper comparison."""

    def __init__(
        self,
        api_key: str,
        rag,
        workspace,
        session_id: str = "default",
        model: str = "gpt-4o-mini",
        top_k: int = 5,
        max_context_chars: int = 8000,
        history_limit: int = 6,
    ):
        self.api_key = api_key
        self.rag = rag
        self.workspace = workspace
        self.session_id = session_id
        self.model = model
        self.top_k = top_k
        self.max_context_chars = max_context_chars
        self.history_limit = history_limit
        self.history = workspace.load_chat(session_id)
        self.client: Optional[OpenAI] = None

    def _ensure_client(self) -> OpenAI:
        """Lazily construct the OpenAI client on first use."""
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key)
        return self.client

    def ask(self, question: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Answer a question with conversational RAG and persist the exchange.

        Retrieval happens inside `rag.answer` (structured output), so no
        separate retrieval is performed here. The question/answer pair is
        appended to `self.history`, persisted, and recorded as a citation.
        """
        if not question or not question.strip():
            return {
                "answer": "Please enter a question.",
                "sources": [],
                "chunks": 0,
                "citations": [],
            }
        question = question.strip()

        r = self.rag.answer(
            question,
            k=k or self.top_k,
            history=self.history[-self.history_limit :],
            structured=True,
        )

        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": r["answer"]})
        self.workspace.save_chat(self.session_id, self.history)
        self.workspace.save_citation(
            {
                "session_id": self.session_id,
                "question": question,
                "answer": r["answer"],
                "sources": r.get("sources", []),
                "timestamp": datetime.now().isoformat(),
            }
        )
        return r

    def compare_papers(
        self,
        paper_ids: List[str],
        question: str,
        k_per_paper: int = 3,
    ) -> Dict[str, Any]:
        """Compare stored papers against each other, grounded in their chunks.

        Retrieves chunks once from the vector store, groups them by paper_id
        (keeping only the requested papers, top `k_per_paper` each in search
        order), and asks the LLM for a structured JSON comparison.
        """
        k = max(20, k_per_paper * len(paper_ids))
        results = self.rag.vector_store.search(query=question, k=k)

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            meta = r.get("metadata", {})
            pid = meta.get("paper_id")
            if pid in paper_ids and len(grouped.get(pid, [])) < k_per_paper:
                grouped.setdefault(pid, []).append(r)
        for pid in paper_ids:
            grouped.setdefault(pid, [])

        papers_with_chunks = sum(1 for pid in paper_ids if grouped[pid])
        if papers_with_chunks < 2:
            return {
                "answer": (
                    "Not enough papers with content to compare. "
                    "Store at least two papers first."
                ),
                "sources": [],
                "chunks": 0,
                "citations": [],
            }

        parts: List[str] = []
        used_chunks: List[Dict[str, Any]] = []
        used = 0
        for i, pid in enumerate(paper_ids, 1):
            pid_results = grouped[pid]
            meta = pid_results[0].get("metadata", {}) if pid_results else {}
            header = f"[{i}] ({meta.get('title', pid)} — {meta.get('source', 'unknown')})"
            if not pid_results:
                parts.append(f"{header}\nno matching chunks")
                continue
            docs = "\n".join(
                r.get("document", "").strip()
                for r in pid_results
                if r.get("document", "").strip()
            )
            part = f"{header}\n{docs}"
            sep = "\n\n" if parts else ""
            if used + len(sep) + len(part) > self.max_context_chars:
                # Try to fit a truncated version of the docs under the remaining budget.
                budget = self.max_context_chars - used - len(sep) - len(header) - 1 - 3
                if budget > 0:
                    parts.append(f"{header}\n{docs[:budget]}...")
                    used_chunks.extend(pid_results)
                break
            parts.append(part)
            used += len(sep) + len(part)
            used_chunks.extend(pid_results)
        context = "\n\n".join(parts)
        sources = RAGAssistant._build_sources(used_chunks)

        try:
            response = self._ensure_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": COMPARE_SYSTEM},
                    {"role": "user", "content": f"Papers:\n{context}\n\nQuestion: {question}"},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
        except Exception as e:
            logger.error("Paper comparison failed: %s", e)
            return {
                "answer": f"Error comparing papers: {e}",
                "sources": sources,
                "chunks": len(used_chunks),
                "citations": [],
            }

        parsed = RAGAssistant._parse_json(raw)
        if parsed is None or not isinstance(parsed, dict):
            return {
                "answer": raw,
                "sources": sources,
                "chunks": len(used_chunks),
                "citations": sources,
            }
        answer = parsed.get("answer") or raw
        citations = parsed.get("citations") or sources
        return {
            "answer": answer,
            "sources": sources,
            "chunks": len(used_chunks),
            "citations": citations,
        }

    def get_history(self) -> List[Dict[str, str]]:
        """Return the in-memory conversation history."""
        return self.history

    def clear(self) -> None:
        """Reset the session history and persist the empty state."""
        self.history = []
        self.workspace.save_chat(self.session_id, self.history)
