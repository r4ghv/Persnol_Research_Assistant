import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

WORKSPACE_DIRS = [
    "Papers",
    "Notes",
    "Chat History",
    "Highlights",
    "Reports",
    "Citations",
]


def _sanitize(name: str, max_length: int = 60) -> str:
    """Sanitize a string for use as a filename component."""
    safe = re.sub(r"[^\w\-]", "_", name[:max_length])
    return re.sub(r"_+", "_", safe).strip("_") or "unnamed"


class ResearchWorkspace:
    """Manage the research workspace directory structure:

    Workspace/
    ├── Papers/        - downloaded PDFs
    ├── Notes/         - user notes
    ├── Chat History/  - conversational RAG sessions (JSON)
    ├── Highlights/    - saved excerpts from papers
    ├── Reports/       - pipeline research reports (markdown + JSON)
    └── Citations/     - structured citation records (JSON)
    """

    def __init__(self, base_dir: str = "workspace"):
        self.base_dir = Path(base_dir)
        for name in WORKSPACE_DIRS:
            (self.base_dir / name).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ paths
    @property
    def papers_dir(self) -> Path:
        return self.base_dir / "Papers"

    @property
    def notes_dir(self) -> Path:
        return self.base_dir / "Notes"

    @property
    def chat_dir(self) -> Path:
        return self.base_dir / "Chat History"

    @property
    def highlights_dir(self) -> Path:
        return self.base_dir / "Highlights"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "Reports"

    @property
    def citations_dir(self) -> Path:
        return self.base_dir / "Citations"

    # ------------------------------------------------------------------ papers
    def save_paper_pdf(self, paper_id: str, pdf_data: bytes) -> Optional[str]:
        """Save a paper's PDF into Papers/; returns the path or None."""
        if not pdf_data:
            return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.papers_dir / f"{_sanitize(paper_id)}_{ts}.pdf"
        path.write_bytes(pdf_data)
        return str(path)

    def list_papers(self) -> List[str]:
        return sorted(p.name for p in self.papers_dir.glob("*.pdf"))

    # ------------------------------------------------------------------- notes
    def save_note(self, title: str, content: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.notes_dir / f"{_sanitize(title)}_{ts}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def list_notes(self) -> List[str]:
        return sorted(p.name for p in self.notes_dir.glob("*.md"))

    # -------------------------------------------------------------------- chat
    def save_chat(self, session_id: str, messages: List[Dict[str, str]]) -> str:
        """Persist a chat session's messages as JSON in Chat History/."""
        path = self.chat_dir / f"{_sanitize(session_id)}.json"
        path.write_text(json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def load_chat(self, session_id: str) -> List[Dict[str, str]]:
        """Load a chat session's messages; returns [] if missing or corrupt."""
        path = self.chat_dir / f"{_sanitize(session_id)}.json"
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to load chat session %s", session_id)
            return []

    def list_chats(self) -> List[str]:
        return sorted(p.stem for p in self.chat_dir.glob("*.json"))

    # ---------------------------------------------------------------- highlights
    def save_highlight(self, paper_id: str, text: str, note: str = "") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = f"# Highlight — {paper_id}\n\n> {text}\n"
        if note:
            content += f"\n**Note:** {note}\n"
        path = self.highlights_dir / f"{_sanitize(paper_id)}_{ts}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def list_highlights(self) -> List[str]:
        return sorted(p.name for p in self.highlights_dir.glob("*.md"))

    # ------------------------------------------------------------------ reports
    def save_report(self, topic: str, report_data: Dict[str, Any]) -> str:
        """Save a structured report JSON into Reports/."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.reports_dir / f"{_sanitize(topic)}_{ts}.json"
        path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def list_reports(self) -> List[str]:
        return sorted(p.name for p in self.reports_dir.glob("*.json"))

    # ---------------------------------------------------------------- citations
    def save_citation(self, citation: Dict[str, Any]) -> str:
        """Save a structured citation record (question, answer, sources)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.citations_dir / f"citation_{ts}.json"
        path.write_text(json.dumps(citation, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def list_citations(self) -> List[str]:
        return sorted(p.name for p in self.citations_dir.glob("*.json"))
