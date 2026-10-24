import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

from .preprocessor import preprocess_and_chunk

logger = logging.getLogger(__name__)


class VectorStore:
    """Embed paper chunks and store them in ChromaDB for semantic search."""

    def __init__(
        self,
        api_key: str,
        collection_name: str = "research_papers",
        persist_dir: str = ".vector_store",
        embedding_model: str = "text-embedding-3-small",
    ):
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=embedding_model,
        )
        self.collection = self._get_or_create_collection(collection_name)

    def _get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name, embedding_function=self.embedding_fn)
        except (ValueError, chromadb.errors.NotFoundError):
            return self.client.create_collection(name, embedding_function=self.embedding_fn)

    def add_paper_chunks(
        self,
        paper_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Chunk paper text, embed, and store in ChromaDB.

        Returns the number of chunks stored.
        """
        chunks = preprocess_and_chunk(content)
        if not chunks:
            logger.warning("No chunks generated for '%s'", title)
            return 0

        base_meta = {
            "paper_id": paper_id,
            "title": title[:200],
            "source": (metadata or {}).get("source", "unknown"),
            "authors": (metadata or {}).get("authors", "")[:500],
            "url": (metadata or {}).get("url", "")[:500],
            "added_at": datetime.now().isoformat(),
        }

        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        safe_prefix = self._sanitize_id(paper_id)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{safe_prefix}_chunk_{i:04d}"
            ids.append(chunk_id)
            meta = dict(base_meta)
            meta["chunk_index"] = i
            meta["total_chunks"] = len(chunks)
            metadatas.append(meta)

        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info("Stored %d chunks for '%s'", len(chunks), title)
        return len(chunks)

    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search chunks by semantic similarity to a text query."""
        if not query.strip():
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
        )
        return self._format_results(results)

    def search_by_embedding(self, embedding: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search chunks by a raw embedding vector."""
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )
        return self._format_results(results)

    def get_paper_chunks(self, paper_id: str) -> List[Dict[str, Any]]:
        """Retrieve all stored chunks for a paper."""
        results = self.collection.get(
            where={"paper_id": paper_id},
            include=["documents", "metadatas"],
        )
        if not results["ids"]:
            return []
        return [
            {
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
            for i in range(len(results["ids"]))
        ]

    def delete_paper(self, paper_id: str) -> None:
        """Remove all chunks for a paper."""
        self.collection.delete(where={"paper_id": paper_id})

    def count(self) -> int:
        """Total number of stored chunks."""
        return self.collection.count()

    def list_papers(self) -> List[Dict[str, str]]:
        """Distinct papers in the collection with their metadata (for UI pickers)."""
        res = self.collection.get(include=["metadatas"])
        if not res["ids"]:
            return []
        seen: Dict[str, Dict[str, str]] = {}
        for m in res["metadatas"]:
            pid = m.get("paper_id", "")
            if pid and pid not in seen:
                seen[pid] = {
                    "paper_id": pid,
                    "title": m.get("title") or pid,
                    "source": m.get("source", "unknown"),
                    "url": m.get("url", ""),
                }
        return list(seen.values())

    # ------------------------------------------------------------------
    @staticmethod
    def _sanitize_id(paper_id: str) -> str:
        safe = re.sub(r"[^\w\-]", "_", paper_id)
        return re.sub(r"_+", "_", safe).strip("_")

    @staticmethod
    def _format_results(results) -> List[Dict[str, Any]]:
        if not results["ids"] or not results["ids"][0]:
            return []
        out = []
        for i in range(len(results["ids"][0])):
            out.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
            )
        return out
