import logging
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from openai import OpenAI

from .ranker import _deduplicate, rank_papers
from .sources import ArxivSource, PubMedSource, SemanticScholarSource

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "arXiv": ArxivSource,
    "PubMed": PubMedSource,
    "Semantic Scholar": SemanticScholarSource,
}

MAX_WORKERS = 5

CRITIC_SYSTEM = (
    "You are a rigorous academic critic. You review an AI-generated paper summary "
    "against the paper's actual content. Be specific and honest about: "
    "(1) factual errors or unsupported claims, (2) important content the summary missed, "
    "(3) misrepresentation of methods or results. Then produce an improved summary that "
    "fixes the issues. Respond with exactly three labeled sections."
)

COMPARE_SYSTEM = (
    "You are a research analyst. Compare the papers synthetically: shared themes, "
    "key differences in approach, conflicting findings, and relative strengths and "
    "weaknesses. Reference papers by their bracketed number [n]. Be specific and concise."
)


class SearchAgent:
    """Query all enabled sources in parallel, then deduplicate and rank."""

    def __init__(self, timeout: int = 30, max_workers: int = MAX_WORKERS):
        self.timeout = timeout
        self.max_workers = max_workers

    def search(
        self,
        query: str,
        max_results: int = 5,
        sources: list[str] | None = None,
    ) -> list[dict]:
        sources = sources or list(SOURCE_MAP)
        per_source = max(1, max_results // max(len(sources), 1))

        papers: list[dict] = []
        workers = min(self.max_workers, len(sources))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._search_one, name, query, per_source): name for name in sources
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    papers.extend(future.result())
                except Exception as e:
                    logger.error("%s search failed: %s", name, e)

        deduped = _deduplicate(papers)
        ranked = rank_papers(deduped, query)
        return ranked[:max_results]

    def _search_one(self, name: str, query: str, per_source: int) -> list[dict]:
        cls = SOURCE_MAP.get(name)
        if cls is None:
            logger.warning("Unknown source '%s' skipped", name)
            return []
        instance = cls(timeout=self.timeout) if name != "arXiv" else cls()
        return instance.search(query, per_source)


class ReaderAgent:
    """Download PDFs and extract text from all papers simultaneously."""

    def __init__(self, scraper, max_workers: int = MAX_WORKERS):
        self.scraper = scraper
        self.max_workers = max_workers

    def read(self, papers: list[dict]) -> list[dict]:
        """Returns [{paper, content, pdf_data}] in input order, failures isolated."""
        results: list[dict | None] = [None] * len(papers)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.scraper.extract_content, p): i for i, p in enumerate(papers)
            }
            for future in as_completed(futures):
                i = futures[future]
                try:
                    content, pdf_data = future.result()
                except Exception as e:
                    logger.error("Read failed for paper %d: %s", i, e)
                    content, pdf_data = papers[i].get("abstract", ""), None
                results[i] = {"paper": papers[i], "content": content, "pdf_data": pdf_data}
        return results


class RetrieverAgent:
    """Chunk paper text, embed it, and store the vectors for semantic search."""

    def __init__(self, vector_store):
        self.store = vector_store

    def store_papers(self, paper_contents: list[dict]) -> int:
        """Store all papers' chunks; returns total chunks added."""
        total = 0
        for pc in paper_contents:
            paper = pc["paper"]
            total += self.store.add_paper_chunks(
                paper_id=paper.get("entry_id") or paper.get("doi") or paper.get("source_id", ""),
                title=paper["title"],
                content=pc["content"],
                metadata={
                    "source": paper.get("source", "unknown"),
                    "authors": ", ".join(paper.get("authors", [])),
                    "url": paper.get("pdf_url") or paper.get("url", ""),
                },
            )
        return total

    def search(self, query: str, k: int = 5) -> list[dict]:
        return self.store.search(query, k=k)


class SummarizerAgent:
    """Summarize all papers in parallel."""

    def __init__(self, summarizer, max_workers: int = MAX_WORKERS):
        self.summarizer = summarizer
        self.max_workers = max_workers

    def summarize(self, paper_contents: list[dict], style: str = "bullet_points") -> list[dict]:
        """Returns [{paper, content, pdf_data, summary}] in input order."""
        results: list[dict | None] = [None] * len(paper_contents)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for i, pc in enumerate(paper_contents):
                futures[
                    executor.submit(
                        self.summarizer.summarize,
                        pc["paper"]["title"],
                        pc["paper"]["abstract"],
                        pc["content"],
                        style,
                    )
                ] = i
            for future in as_completed(futures):
                i = futures[future]
                pc = paper_contents[i]
                results[i] = {**pc, "summary": future.result()}
        return results


class CriticAgent:
    """Review each summary against the paper content and produce an improved version."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_workers: int = MAX_WORKERS,
        max_content_chars: int = 6000,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_workers = max_workers
        self.max_content_chars = max_content_chars

    def critique_all(self, summaries: list[dict]) -> list[dict]:
        """Returns [{paper, summary, critique, revised_summary, rating, ...}] in order."""
        results: list[dict | None] = [None] * len(summaries)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for i, s in enumerate(summaries):
                futures[
                    executor.submit(
                        self._critique_one,
                        s["paper"]["title"],
                        s["paper"]["abstract"],
                        s["content"],
                        s["summary"],
                    )
                ] = i
            for future in as_completed(futures):
                i = futures[future]
                results[i] = {**summaries[i], **future.result()}
        return results

    def _critique_one(self, title: str, abstract: str, content: str, summary: str) -> dict:
        truncated = content[: self.max_content_chars]
        prompt = (
            f"Title: {title}\nAbstract: {abstract}\n\n"
            f"Paper content:\n{truncated}\n\n"
            f"Summary under review:\n{summary}\n\n"
            "Respond with exactly three sections:\n"
            "CRITIQUE: <factual issues, coverage gaps, misrepresentations>\n"
            "REVISED SUMMARY: <improved summary fixing the issues>\n"
            "RATING: <integer 1-10>"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CRITIC_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            text = response.choices[0].message.content
        except Exception as e:
            logger.error("Critique failed for '%s': %s", title[:50], e)
            return {
                "critique": f"Critique failed: {e}",
                "revised_summary": summary,
                "rating": None,
            }
        return self._parse(text, summary)

    @staticmethod
    def _parse(text: str, fallback_summary: str) -> dict:
        critique = re.search(r"CRITIQUE:\s*(.*?)(?:REVISED SUMMARY:|RATING:)", text, re.S | re.I)
        revised = re.search(r"REVISED SUMMARY:\s*(.*?)(?:RATING:)", text, re.S | re.I)
        rating = re.search(r"RATING:\s*(\d+)", text, re.I)
        return {
            "critique": critique.group(1).strip() if critique else text.strip()[:2000],
            "revised_summary": revised.group(1).strip() if revised else fallback_summary,
            "rating": int(rating.group(1)) if rating else None,
        }


class ReportAgent:
    """Produce a structured markdown report with per-paper and comparative sections."""

    def __init__(
        self,
        api_key: str,
        organizer,
        model: str = "gpt-4o-mini",
    ):
        self.client = OpenAI(api_key=api_key)
        self.organizer = organizer
        self.model = model

    def compare_papers(self, critiqued: list[dict]) -> str:
        """Cross-paper comparison via one LLM call; local fallback on failure."""
        if len(critiqued) < 2:
            return "Only one paper analyzed — no cross-paper comparison available."

        entries = []
        for i, s in enumerate(critiqued, 1):
            text = s.get("revised_summary") or s["summary"]
            entries.append(f"[{i}] {s['paper']['title']}\n{text[:1500]}")
        prompt = "Compare the following papers:\n\n" + "\n\n".join(entries)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": COMPARE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Comparison failed: %s", e)
            return self._local_comparison(critiqued)

    @staticmethod
    def _local_comparison(critiqued: list[dict]) -> str:
        lines = ["Papers analyzed:"]
        for i, s in enumerate(critiqued, 1):
            lines.append(f"- [{i}] {s['paper']['title']} ({s['paper'].get('source', 'unknown')})")
        return "\n".join(lines)

    def generate(self, topic: str, critiqued: list[dict], comparison: str) -> dict:
        """Render and save the report. Returns {'path', 'json_path', 'markdown'}."""
        markdown = self._render_markdown(topic, critiqued, comparison)
        md_path = self._save_markdown(topic, markdown)

        report_data = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "papers_analyzed": len(critiqued),
            "comparison": comparison,
            "papers": [
                {
                    "title": s["paper"]["title"],
                    "source": s["paper"].get("source"),
                    "url": s["paper"].get("pdf_url") or s["paper"].get("url"),
                    "rating": s.get("rating"),
                    "summary": s["summary"],
                    "revised_summary": s.get("revised_summary"),
                    "critique": s.get("critique"),
                }
                for s in critiqued
            ],
        }
        json_path = self.organizer.save_report(report_data)
        return {"path": md_path, "json_path": json_path, "markdown": markdown}

    def _save_markdown(self, topic: str, markdown: str) -> str:
        slug = self.organizer._sanitize_filename(topic)
        filename = f"{slug}_report.md"
        import os

        path = os.path.join(self.organizer.output_dir, "reports", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown)
        return path

    def _render_markdown(self, topic: str, critiqued: list[dict], comparison: str) -> str:
        lines = [
            f"# Research Report: {topic}",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Papers analyzed:** {len(critiqued)}",
            "",
        ]
        for i, s in enumerate(critiqued, 1):
            paper = s["paper"]
            rating = s.get("rating")
            rating_str = f"{rating}/10" if rating is not None else "n/a"
            summary = s.get("revised_summary") or s["summary"]
            lines += [
                f"## Paper {i}: {paper['title']}",
                f"- **Source:** {paper.get('source', 'unknown')}",
                f"- **Critic rating:** {rating_str}",
                "",
                "### Summary",
                summary,
                "",
                "### Critique",
                s.get("critique", ""),
                "",
            ]
        lines += [
            "## Comparative Analysis",
            comparison,
            "",
            "## Sources",
        ]
        seen = set()
        for s in critiqued:
            paper = s["paper"]
            title = paper["title"]
            if title in seen:
                continue
            seen.add(title)
            url = paper.get("pdf_url") or paper.get("url") or ""
            source = paper.get("source", "unknown")
            if url:
                lines.append(f"- [{title}]({url}) — *{source}*")
            else:
                lines.append(f"- {title} — *{source}*")
        return "\n".join(lines)


class ResearchPipeline:
    """Search → Read → Retrieve → Summarize → Critique → Report."""

    def __init__(
        self,
        api_key: str,
        model: str,
        scraper,
        summarizer,
        vector_store,
        organizer,
        timeout: int = 30,
        max_workers: int = MAX_WORKERS,
        log: Callable[[str], None] | None = None,
    ):
        self.log = log or logger.info
        self.search_agent = SearchAgent(timeout=timeout, max_workers=max_workers)
        self.reader_agent = ReaderAgent(scraper, max_workers=max_workers)
        self.retriever_agent = RetrieverAgent(vector_store)
        self.summarizer_agent = SummarizerAgent(summarizer, max_workers=max_workers)
        self.critic_agent = CriticAgent(api_key, model, max_workers=max_workers)
        self.report_agent = ReportAgent(api_key, organizer, model)

    def run(
        self,
        topic: str,
        max_papers: int = 5,
        summary_style: str = "bullet_points",
        sources: list[str] | None = None,
    ) -> dict:
        # 1. Search (parallel across sources)
        self.log("Search agent: querying sources...")
        papers = self.search_agent.search(topic, max_papers, sources)
        if not papers:
            return {"error": f"No papers found for topic: '{topic}'"}

        # 2. Read (parallel downloads)
        self.log(f"Reader agent: downloading {len(papers)} PDFs simultaneously...")
        paper_contents = self.reader_agent.read(papers)

        # 3. Retrieve (chunk + embed + store)
        self.log("Retriever agent: embedding chunks into vector store...")
        chunks_stored = self.retriever_agent.store_papers(paper_contents)
        self.log(f"Retriever agent: stored {chunks_stored} chunks")

        # 4. Summarize (parallel)
        self.log("Summarizer agent: generating summaries...")
        summaries = self.summarizer_agent.summarize(paper_contents, summary_style)

        # 5. Critique (parallel)
        self.log("Critic agent: reviewing summaries against paper content...")
        critiqued = self.critic_agent.critique_all(summaries)

        # 6. Report
        self.log("Report agent: comparing papers and writing report...")
        comparison = self.report_agent.compare_papers(critiqued)
        report = self.report_agent.generate(topic, critiqued, comparison)

        return {
            "topic": topic,
            "papers": papers,
            "summaries": critiqued,
            "chunks_stored": chunks_stored,
            "report": report,
        }
