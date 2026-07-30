import pytest
import re
from pathlib import Path

from research_assistant.utils.config import Config
from research_assistant.utils.file_utils import save_json, load_json, save_text, load_text
from research_assistant.agents.organizer import Organizer
from research_assistant.agents.scraper import Scraper


class TestScraper:
    def test_clean_query_removes_special_chars(self):
        scraper = Scraper()
        assert scraper._clean_query("test!@# query") == "test query"

    def test_clean_query_collapses_whitespace(self):
        scraper = Scraper()
        assert scraper._clean_query("  lots   of  space ") == "lots of space"

    def test_clean_query_truncates_long_queries(self):
        scraper = Scraper()
        query = "a b c d e f g h i j"
        result = scraper._clean_query(query)
        assert len(result.split()) <= 4


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
