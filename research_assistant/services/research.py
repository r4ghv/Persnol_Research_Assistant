"""Research service: run the agentic pipeline and archive artifacts."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ResearchService:
    """Wrap the ResearchPipeline plus file/workspace archiving for API use.

    The pipeline is Search → Read → Retrieve → Summarize → Critique → Report.
    This service adds the side effects (organizer saves, workspace archives)
    and returns a JSON-serializable summary of the run.
    """

    def __init__(self, pipeline, organizer, workspace):
        self.pipeline = pipeline
        self.organizer = organizer
        self.workspace = workspace

    def run(
        self,
        topic: str,
        max_papers: int = 5,
        summary_style: str = "bullet_points",
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run the pipeline and archive outputs. Returns a JSON-serializable dict.

        On pipeline failure, returns {"error": str}. On success returns
        {"topic", "papers", "summaries", "chunks_stored", "report",
         "average_rating", "sources_used", "workspace_report"}.
        """
        if not topic or not topic.strip():
            return {"error": "Please provide a research topic."}

        result = self.pipeline.run(
            topic=topic,
            max_papers=max_papers,
            summary_style=summary_style,
            sources=sources or ["arXiv"],
        )
        if result.get("error"):
            return {"error": result["error"]}

        papers = result.get("papers", [])
        summaries = result.get("summaries", [])
        report = result.get("report", {})

        # Archive papers + PDFs + report into the research workspace
        workspace_report = None
        try:
            for s in summaries:
                self.organizer.save_paper(
                    s["paper"],
                    s["content"],
                    s.get("revised_summary") or s["summary"],
                    pdf_data=s.get("pdf_data"),
                )
                if s.get("pdf_data"):
                    paper_id = (
                        s["paper"].get("entry_id")
                        or s["paper"].get("id")
                        or s["paper"].get("title", "paper")
                    )
                    self.workspace.save_paper_pdf(paper_id, s["pdf_data"])
            if report.get("json_path"):
                with open(report["json_path"], encoding="utf-8") as f:
                    report_data = json.load(f)
                workspace_report = self.workspace.save_report(topic, report_data)
        except (OSError, ValueError) as e:
            logger.warning("Archiving to workspace failed: %s", e)

        # pdf_data is raw bytes (already archived server-side); drop it from
        # the JSON-serializable payload returned to the API/frontend.
        summaries = [
            {k: v for k, v in dict(s).items() if k != "pdf_data"} for s in summaries
        ]


        ratings = [s.get("rating") for s in summaries if s.get("rating") is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        return {
            "topic": topic,
            "papers": papers,
            "summaries": summaries,
            "chunks_stored": result.get("chunks_stored", 0),
            "report": report,
            "average_rating": avg_rating,
            "sources_used": sorted({p.get("source", "?") for p in papers}),
            "workspace_report": workspace_report,
        }
