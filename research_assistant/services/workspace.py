"""Workspace service: expose vector store and workspace state to the API."""

from typing import Any


class WorkspaceService:
    """Read-only accessors over the vector store and research workspace."""

    def __init__(self, workspace, vector_store):
        self.workspace = workspace
        self.vector_store = vector_store

    def list_papers(self) -> list[dict[str, str]]:
        """Distinct papers in the vector store with metadata (for pickers)."""
        return self.vector_store.list_papers()

    def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Vector search across stored paper chunks."""
        if not query or not query.strip():
            return []
        return self.vector_store.search(query, k=int(k))

    def paper_chunks(self, paper_id: str) -> list[dict[str, Any]]:
        return self.vector_store.get_paper_chunks(paper_id)

    def delete_paper(self, paper_id: str) -> dict[str, Any]:
        self.vector_store.delete_paper(paper_id)
        return {"ok": True, "paper_id": paper_id}

    def counts(self) -> dict[str, int]:
        """Counts per workspace directory."""
        return {
            "papers": len(self.workspace.list_papers()),
            "notes": len(self.workspace.list_notes()),
            "chats": len(self.workspace.list_chats()),
            "highlights": len(self.workspace.list_highlights()),
            "reports": len(self.workspace.list_reports()),
            "citations": len(self.workspace.list_citations()),
            "chunks": self.vector_store.count(),
        }

    def summary(self) -> dict[str, Any]:
        """Markdown snapshot of the workspace plus per-dir file names."""
        lines = [
            f"**Workspace:** `{self.workspace.base_dir}`",
            "",
            f"- 📄 **Papers** ({len(self.workspace.list_papers())})",
            f"- 📝 **Notes** ({len(self.workspace.list_notes())})",
            f"- 💬 **Chat History** ({len(self.workspace.list_chats())})",
            f"- 🖍️ **Highlights** ({len(self.workspace.list_highlights())})",
            f"- 📊 **Reports** ({len(self.workspace.list_reports())})",
            f"- 🔖 **Citations** ({len(self.workspace.list_citations())})",
        ]
        for label, names in [
            ("Papers", self.workspace.list_papers()),
            ("Notes", self.workspace.list_notes()),
            ("Chat History", self.workspace.list_chats()),
            ("Reports", self.workspace.list_reports()),
        ]:
            if names:
                lines.append("")
                lines.append(f"**{label}:**")
                lines.extend(f"- `{n}`" for n in names[-10:])
        return {"markdown": "\n".join(lines), "counts": self.counts()}
