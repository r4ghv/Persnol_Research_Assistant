import pytest
from unittest.mock import MagicMock, patch

from research_assistant.agents.pipeline import (
    SearchAgent,
    ReaderAgent,
    SummarizerAgent,
    CriticAgent,
    ReportAgent,
    ResearchPipeline,
)


def _paper(title="Test Paper", source="arXiv", i=0):
    return {
        "title": title,
        "authors": [f"Author {i}"],
        "abstract": f"Abstract about {title}.",
        "published": "2025-01-01",
        "pdf_url": f"https://example.com/{i}.pdf",
        "doi": f"10.0/{i}",
        "source": source,
        "source_id": f"id{i}",
        "url": f"https://example.com/{i}",
        "entry_id": f"https://arxiv.org/abs/2501.0000{i}",
        "citation_count": None,
    }


def _content(i=0):
    return f"Section one of paper {i}. Attention mechanisms are discussed here. Methods follow."


def _summaries(n=2):
    return [
        {
            "paper": _paper(title=f"Paper {i}", i=i),
            "content": _content(i),
            "pdf_data": b"%PDF-fake",
            "summary": f"Summary of paper {i}.",
        }
        for i in range(n)
    ]


class TestCriticAgent:
    def test_parse_full(self):
        text = (
            "CRITIQUE: The summary omits the dataset size.\n"
            "REVISED SUMMARY: A better summary including dataset details.\n"
            "RATING: 7"
        )
        out = CriticAgent._parse(text, "fallback")
        assert out["critique"] == "The summary omits the dataset size."
        assert out["revised_summary"] == "A better summary including dataset details."
        assert out["rating"] == 7

    def test_parse_missing_sections(self):
        out = CriticAgent._parse("some raw text without labels", "fallback")
        assert out["revised_summary"] == "fallback"
        assert out["rating"] is None
        assert "some raw text" in out["critique"]

    def test_parse_rating_with_slash(self):
        out = CriticAgent._parse("CRITIQUE: x\nREVISED SUMMARY: y\nRATING: 9/10", "f")
        assert out["rating"] == 9

    def test_critique_openai_error_keeps_summary(self):
        with patch("research_assistant.agents.pipeline.OpenAI") as mo:
            client = MagicMock()
            mo.return_value = client
            client.chat.completions.create.side_effect = Exception("down")
            agent = CriticAgent(api_key="sk-fake", model="m")
            out = agent._critique_one("T", "A", "C", "S")
            assert out["revised_summary"] == "S"
            assert out["rating"] is None
            assert "Critique failed" in out["critique"]


class TestReportAgent:
    def test_local_comparison_single_paper(self, tmp_path):
        from research_assistant.agents.organizer import Organizer

        agent = ReportAgent(api_key="sk-fake", organizer=Organizer(str(tmp_path)), model="m")
        out = agent.compare_papers([_summaries(1)[0]])
        assert "no cross-paper comparison" in out

    def test_compare_papers_openai_fallback(self, tmp_path):
        from research_assistant.agents.organizer import Organizer

        with patch("research_assistant.agents.pipeline.OpenAI") as mo:
            client = MagicMock()
            mo.return_value = client
            client.chat.completions.create.side_effect = Exception("down")
            agent = ReportAgent(api_key="sk-fake", organizer=Organizer(str(tmp_path)), model="m")
            out = agent.compare_papers(_summaries(2))
            assert "Paper 0" in out
            assert "Paper 1" in out

    def test_render_markdown_content(self, tmp_path):
        from research_assistant.agents.organizer import Organizer

        agent = ReportAgent(api_key="sk-fake", organizer=Organizer(str(tmp_path)), model="m")
        critiqued = _summaries(2)
        critiqued[0]["critique"] = "Missing dataset info."
        critiqued[0]["revised_summary"] = "Improved summary 0."
        critiqued[0]["rating"] = 8
        md = agent._render_markdown("My Topic", critiqued, "Both papers use attention.")
        assert "# Research Report: My Topic" in md
        assert "## Paper 1: Paper 0" in md
        assert "Improved summary 0." in md
        assert "Missing dataset info." in md
        assert "8/10" in md
        assert "## Comparative Analysis" in md
        assert "Both papers use attention." in md
        assert "## Sources" in md
        assert "https://example.com/0.pdf" in md

    def test_generate_saves_markdown_and_json(self, tmp_path):
        from research_assistant.agents.organizer import Organizer

        organizer = Organizer(str(tmp_path))
        agent = ReportAgent(api_key="sk-fake", organizer=organizer, model="m")
        out = agent.generate("My Topic", _summaries(1), "comparison text")
        assert out["path"].endswith(".md")
        assert out["json_path"].endswith(".json")
        import os

        assert os.path.exists(out["path"])
        assert os.path.exists(out["json_path"])


class TestReaderAgent:
    def test_preserves_order(self):
        scraper = MagicMock()
        papers = [_paper(title="A", i=0), _paper(title="B", i=1), _paper(title="C", i=2)]

        def fake_extract(paper):
            return f"content-{paper['title']}", f"pdf-{paper['title']}"

        scraper.extract_content.side_effect = fake_extract
        agent = ReaderAgent(scraper, max_workers=3)
        results = agent.read(papers)
        assert [r["paper"]["title"] for r in results] == ["A", "B", "C"]
        assert results[1]["content"] == "content-B"

    def test_failure_isolation(self):
        scraper = MagicMock()
        papers = [_paper(title="A", i=0), _paper(title="B", i=1)]

        def fake_extract(paper):
            if paper["title"] == "B":
                raise RuntimeError("boom")
            return "ok-A", b"pdf-A"

        scraper.extract_content.side_effect = fake_extract
        agent = ReaderAgent(scraper, max_workers=2)
        results = agent.read(papers)
        assert results[0]["content"] == "ok-A"
        assert results[1]["content"] == papers[1]["abstract"]  # falls back to abstract
        assert results[1]["pdf_data"] is None


class TestSummarizerAgent:
    def test_preserves_order(self):
        summarizer = MagicMock()

        def fake_summarize(title, abstract, content, style):
            return f"sum-{title}"

        summarizer.summarize.side_effect = fake_summarize
        agent = SummarizerAgent(summarizer, max_workers=2)
        out = agent.summarize(
            [
                {"paper": _paper(title="A", i=0), "content": "c0", "pdf_data": None},
                {"paper": _paper(title="B", i=1), "content": "c1", "pdf_data": None},
            ],
            style="paragraph",
        )
        assert [s["summary"] for s in out] == ["sum-A", "sum-B"]
        summarizer.summarize.assert_any_call("A", "Abstract about A.", "c0", "paragraph")


class TestSearchAgent:
    def test_searches_all_sources_parallel(self):
        class FakeSourceA:
            def __init__(self, timeout=30):
                pass

            def search(self, query, n):
                return [_paper(title=f"A-{query}", source="FakeA", i=0)]

        class FakeSourceB:
            def __init__(self, timeout=30):
                pass

            def search(self, query, n):
                return [_paper(title=f"B-{query}", source="FakeB", i=1)]

        with patch.dict(
            "research_assistant.agents.pipeline.SOURCE_MAP",
            {"FakeA": FakeSourceA, "FakeB": FakeSourceB},
        ):
            agent = SearchAgent(max_workers=2)
            results = agent.search("testing", max_results=10, sources=["FakeA", "FakeB"])
        titles = {p["title"] for p in results}
        assert "A-testing" in titles
        assert "B-testing" in titles

    def test_unknown_source_skipped(self):
        agent = SearchAgent(max_workers=2)
        results = agent.search("x", max_results=5, sources=["NotARealSource"])
        assert results == []


class TestResearchPipeline:
    def test_run_executes_stages_in_order(self):
        order = []

        def log(msg):
            order.append(("log", msg))

        pipeline = ResearchPipeline(
            api_key="sk-fake",
            model="m",
            scraper=MagicMock(),
            summarizer=MagicMock(),
            vector_store=MagicMock(),
            organizer=MagicMock(),
            log=log,
        )
        papers = [_paper(title="P1", i=0), _paper(title="P2", i=1)]
        contents = [
            {"paper": papers[0], "content": "c0", "pdf_data": None},
            {"paper": papers[1], "content": "c1", "pdf_data": None},
        ]
        summaries = [{**contents[0], "summary": "s0"}, {**contents[1], "summary": "s1"}]
        critiqued = [
            {**summaries[0], "revised_summary": "r0", "critique": "k0", "rating": 8},
            {**summaries[1], "revised_summary": "r1", "critique": "k1", "rating": 7},
        ]

        pipeline.search_agent.search = MagicMock(return_value=papers)
        pipeline.reader_agent.read = MagicMock(return_value=contents)
        pipeline.retriever_agent.store_papers = MagicMock(return_value=42)
        pipeline.summarizer_agent.summarize = MagicMock(return_value=summaries)
        pipeline.critic_agent.critique_all = MagicMock(return_value=critiqued)
        pipeline.report_agent.compare_papers = MagicMock(return_value="cmp")
        pipeline.report_agent.generate = MagicMock(
            return_value={"path": "r.md", "json_path": "r.json", "markdown": "md"}
        )

        result = pipeline.run(
            "topic", max_papers=2, summary_style="bullet_points", sources=["arXiv"]
        )

        pipeline.search_agent.search.assert_called_once_with("topic", 2, ["arXiv"])
        pipeline.reader_agent.read.assert_called_once_with(papers)
        pipeline.retriever_agent.store_papers.assert_called_once_with(contents)
        pipeline.summarizer_agent.summarize.assert_called_once_with(contents, "bullet_points")
        pipeline.critic_agent.critique_all.assert_called_once_with(summaries)
        pipeline.report_agent.compare_papers.assert_called_once_with(critiqued)
        pipeline.report_agent.generate.assert_called_once_with("topic", critiqued, "cmp")

        assert result["summaries"] == critiqued
        assert result["chunks_stored"] == 42
        assert result["report"]["path"] == "r.md"

        log_messages = [m for kind, m in order if kind == "log"]
        joined = " | ".join(log_messages)
        assert "Search agent" in joined
        assert "Reader agent" in joined
        assert "Retriever agent" in joined
        assert "Summarizer agent" in joined
        assert "Critic agent" in joined
        assert "Report agent" in joined
        # stage order in logs
        assert (
            joined.index("Search")
            < joined.index("Reader")
            < joined.index("Retriever")
            < joined.index("Summarizer")
            < joined.index("Critic")
            < joined.index("Report")
        )

    def test_run_no_papers_returns_error(self):
        pipeline = ResearchPipeline(
            api_key="sk-fake",
            model="m",
            scraper=MagicMock(),
            summarizer=MagicMock(),
            vector_store=MagicMock(),
            organizer=MagicMock(),
        )
        pipeline.search_agent.search = MagicMock(return_value=[])
        pipeline.reader_agent.read = MagicMock()
        result = pipeline.run("nope")
        assert "error" in result
        pipeline.reader_agent.read.assert_not_called()
