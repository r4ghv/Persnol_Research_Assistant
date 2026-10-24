import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a research assistant that answers questions using ONLY the retrieved paper excerpts provided in the context. Follow these rules strictly:

1. Base your answer exclusively on the context; do not use outside knowledge.
2. Cite sources inline with numbered brackets like [1], [2] matching the source list at the end of the context.
3. If the context does not contain the answer, say "The retrieved papers do not contain information about this." Do not fabricate.
4. Keep the answer concise and well-structured (short paragraphs or bullets)."""

STRUCTURED_SYSTEM_PROMPT = """You are a research assistant that answers questions using ONLY the retrieved paper excerpts provided in the context. Follow these rules strictly:

1. Base your answer exclusively on the context; do not use outside knowledge.
2. Cite sources inline with numbered brackets like [1], [2] matching the source list at the end of the context.
3. If the context does not contain the answer, say "The retrieved papers do not contain information about this." Do not fabricate.
4. Keep the answer concise and well-structured (short paragraphs or bullets).
5. Respond ONLY with a valid JSON object having exactly two keys: "answer" (string) and "citations" (array of objects with "title", "source", "url" keys, one per distinct source cited)."""


class RAGAssistant:
    """Retrieve relevant paper chunks from the vector store and answer via the LLM."""

    def __init__(
        self,
        api_key: str,
        vector_store,
        model: str = "gpt-4o-mini",
        max_context_chars: int = 8000,
        top_k: int = 5,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.vector_store = vector_store
        self.max_context_chars = max_context_chars
        self.top_k = top_k

    def answer(
        self,
        question: str,
        k: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
        structured: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve relevant chunks for `question` and generate a grounded answer.

        Args:
            question: the user's question.
            k: number of chunks to retrieve (defaults to self.top_k).
            history: prior turns as [{"role": "user"|"assistant", "content": str}]
                     for conversational context (defaults to None).
            structured: if True, request JSON output with an "answer" and
                        "citations" field and parse it.

        Returns {"answer": str, "sources": [{"title","source","url"}], "chunks": int,
                 "citations": [{"title","source","url"}] (only when structured)}.
        """
        if not question or not question.strip():
            return {
                "answer": "Please enter a question.",
                "sources": [],
                "chunks": 0,
                **({"citations": []} if structured else {}),
            }
        question = question.strip()

        k = k or self.top_k
        results = self.vector_store.search(question, k=k)
        if not results:
            return {
                "answer": (
                    "No relevant paper content found in the vector store. "
                    "Run a research query first so papers are embedded and stored."
                ),
                "sources": [],
                "chunks": 0,
                **({"citations": []} if structured else {}),
            }

        context = self._build_context(results)
        sources = self._build_sources(results)
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        kwargs = {"model": self.model, "messages": messages, "temperature": 0.2}
        if structured:
            messages[0] = {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT}
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            raw = response.choices[0].message.content
        except Exception as e:
            logger.error("RAG generation failed: %s", e)
            return {
                "answer": f"Error generating answer: {e}",
                "sources": sources,
                "chunks": len(results),
                **({"citations": []} if structured else {}),
            }

        if not structured:
            return {"answer": raw, "sources": sources, "chunks": len(results)}

        parsed = self._parse_json(raw)
        if parsed is None or not isinstance(parsed, dict):
            return {"answer": raw, "sources": sources, "chunks": len(results), "citations": sources}
        answer = parsed.get("answer") or raw
        citations = parsed.get("citations") or sources
        return {"answer": answer, "sources": sources, "chunks": len(results), "citations": citations}

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse a JSON object from model output, tolerating code fences and prose."""
        import json
        import re

        if not text:
            return None
        # Strip markdown code fences if present
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        # Fall back to extracting the first {...} block
        m = re.search(r"\{.*\}", stripped, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a numbered context block within budget."""
        parts: List[str] = []
        used = 0
        for i, r in enumerate(results, 1):
            doc = r.get("document", "").strip()
            if not doc:
                continue
            meta = r.get("metadata", {})
            header = f"[{i}] ({meta.get('title', 'Unknown')} — {meta.get('source', 'unknown')})"
            part = f"{header}\n{doc}"
            sep = "\n\n" if parts else ""

            if used + len(sep) + len(part) > self.max_context_chars:
                # Try to fit a truncated version of the doc under the remaining budget.
                budget = self.max_context_chars - used - len(sep) - len(header) - 1 - 3
                if budget > 0:
                    parts.append(f"{header}\n{doc[:budget]}...")
                break

            parts.append(part)
            used += len(sep) + len(part)
        return "\n\n".join(parts)

    @staticmethod
    def _build_sources(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Deduplicate paper sources by title, preserving retrieval order."""
        seen = set()
        sources: List[Dict[str, str]] = []
        for r in results:
            meta = r.get("metadata", {})
            title = meta.get("title", "Unknown")
            if title in seen:
                continue
            seen.add(title)
            sources.append(
                {
                    "title": title,
                    "source": meta.get("source", "unknown"),
                    "url": meta.get("url", ""),
                }
            )
        return sources
