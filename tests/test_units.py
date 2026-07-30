import pytest
from research_assistant.utils.file_utils import save_json, load_json, save_text, load_text
from research_assistant.agents.organizer import Organizer
from research_assistant.agents.sources import _clean_query
from research_assistant.agents.ranker import score_paper, _keyword_overlap, _recency_score
from research_assistant.agents.preprocessor import (
    clean_pdf_text,
    detect_sections,
    chunk_sections,
    preprocess_and_chunk,
)


class TestSources:
    def test_clean_query_removes_special_chars(self):
        assert _clean_query("test!@# query") == "test query"

    def test_clean_query_collapses_whitespace(self):
        assert _clean_query("  lots   of  space ") == "lots of space"

    def test_clean_query_truncates_long_queries(self):
        query = "a b c d e f g h i j"
        result = _clean_query(query)
        assert len(result.split()) <= 4


class TestRanker:
    def test_keyword_overlap(self):
        score = _keyword_overlap("machine learning", "Machine Learning for Beginners", "A paper about machine learning")
        assert 0 < score <= 40

    def test_keyword_overlap_empty_query(self):
        assert _keyword_overlap("", "Some title", "Some abstract") == 0

    def test_recency_score_recent(self):
        import datetime
        current_year = datetime.datetime.now().year
        score = _recency_score(f"{current_year}-01-01")
        assert score == 30

    def test_recency_score_old(self):
        score = _recency_score("2000-01-01")
        assert score == 0

    def test_recency_score_none(self):
        assert _recency_score(None) == 0

    def test_score_paper_arxiv(self):
        paper = {"title": "deep learning", "abstract": "about deep learning", "published": "2025-01-01", "source": "arXiv", "citation_count": None}
        score = score_paper(paper, "deep learning")
        assert 10 <= score <= 100


class TestPreprocessor:
    def test_clean_removes_page_numbers(self):
        result = clean_pdf_text("Some text\n\n42\n\nMore text")
        assert "42" not in result

    def test_clean_removes_arxiv_id(self):
        result = clean_pdf_text("Some text arXiv:2508.12345 and more")
        assert "arXiv:2508.12345" not in result

    def test_clean_removes_latex_cites(self):
        result = clean_pdf_text("Prior work \\cite{smith2023} shows")
        assert "\\cite" not in result

    def test_clean_trims_references(self):
        text = "Main content.\n\nReferences\n[1] Some citation\n[2] Another"
        result = clean_pdf_text(text)
        assert "References" not in result

    def test_detect_sections(self):
        text = "Abstract\nWe present a study.\n\nIntroduction\nThis is the intro."
        sections = detect_sections(text)
        labels = [s[0] for s in sections]
        assert "abstract" in labels
        assert "introduction" in labels

    def test_chunk_sections_short_stays_whole(self):
        chunks = chunk_sections([("abstract", "Short text.")])
        assert len(chunks) == 1
        assert "abstract" in chunks[0].lower()

    def test_preprocess_and_chunk_pipeline(self):
        text = "Abstract\nThis is a test paper.\n\nConclusion\nDone."
        chunks = preprocess_and_chunk(text)
        assert len(chunks) >= 1

    def test_build_chunked_prompt_includes_title(self):
        from research_assistant.agents.preprocessor import build_chunked_prompt
        chunks = ["chunk one", "chunk two"]
        prompt = build_chunked_prompt("Test Title", "Test Abstract", chunks)
        assert "Test Title" in prompt
        assert "Test Abstract" in prompt


class TestOrganizer:
    def test_sanitize_filename_removes_illegal_chars(self):
        result = Organizer._sanitize_filename("test/file:name?with*illegal<chars>")
        assert "/" not in result
        assert ":" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_filename_collapses_underscores(self):
        result = Organizer._sanitize_filename("test___file__name")
        assert "__" not in result

    def test_sanitize_filename_truncates(self):
        long_name = "a" * 100
        result = Organizer._sanitize_filename(long_name, max_length=20)
        assert len(result) <= 20


class TestFileUtils:
    def test_save_and_load_json(self, tmp_path):
        data = {"key": "value", "nested": {"a": 1}}
        path = str(tmp_path / "test.json")

        assert save_json(data, path) is True
        loaded = load_json(path)
        assert loaded == data

    def test_load_json_nonexistent(self):
        assert load_json("/nonexistent/path.json") is None

    def test_save_and_load_text(self, tmp_path):
        content = "Hello, World!"
        path = str(tmp_path / "test.txt")

        assert save_text(content, path) is True
        loaded = load_text(path)
        assert loaded == content
