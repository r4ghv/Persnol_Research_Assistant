import json
import pytest
from research_assistant.workspace import ResearchWorkspace, WORKSPACE_DIRS, _sanitize


class TestWorkspaceStructure:
    def test_all_six_directories_created(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        for name in WORKSPACE_DIRS:
            assert (tmp_path / name).is_dir()

    def test_directory_paths_exposed(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        assert ws.papers_dir.name == "Papers"
        assert ws.chat_dir.name == "Chat History"
        assert ws.citations_dir.name == "Citations"


class TestSanitize:
    def test_replaces_special_chars(self):
        assert _sanitize("a/b:c*d?e") == "a_b_c_d_e"

    def test_collapses_underscores(self):
        assert _sanitize("a___b") == "a_b"

    def test_falls_back_when_empty(self):
        assert _sanitize("///") == "unnamed"

    def test_truncates_long_names(self):
        assert len(_sanitize("x" * 100, max_length=20)) <= 20


class TestPapers:
    def test_save_paper_pdf_skips_empty(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        assert ws.save_paper_pdf("p1", b"") is None
        assert ws.list_papers() == []

    def test_save_paper_pdf_writes_bytes(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        path = ws.save_paper_pdf("paper one", b"%PDF-1.4 fake")
        assert path is not None
        assert path.startswith(str(tmp_path / "Papers"))
        with open(path, "rb") as f:
            assert f.read() == b"%PDF-1.4 fake"


class TestChatPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        messages = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        ws.save_chat("my-session", messages)
        assert ws.load_chat("my-session") == messages

    def test_load_missing_session_returns_empty(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        assert ws.load_chat("nope") == []

    def test_load_corrupt_file_returns_empty(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        (ws.chat_dir / "broken.json").write_text("{not json", encoding="utf-8")
        assert ws.load_chat("broken") == []

    def test_load_wrong_shape_returns_empty(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        (ws.chat_dir / "obj.json").write_text('{"a": 1}', encoding="utf-8")
        assert ws.load_chat("obj") == []

    def test_list_chats_returns_stems(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        ws.save_chat("alpha", [])
        ws.save_chat("beta", [])
        assert ws.list_chats() == ["alpha", "beta"]


class TestNotesHighlightsReportsCitations:
    def test_save_note(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        path = ws.save_note("my idea", "# Note\ncontent")
        assert path.endswith(".md")
        with open(path, encoding="utf-8") as f:
            assert "content" in f.read()

    def test_save_highlight(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        path = ws.save_highlight("p1", "key quote", note="context")
        assert path.endswith(".md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "key quote" in content
        assert "context" in content
    def test_save_report_writes_json(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        data = {"topic": "t", "papers": [{"title": "A"}]}
        path = ws.save_report("my topic", data)
        assert path.endswith(".json")
        loaded = json.loads(ws.reports_dir.joinpath(path.split("/")[-1]).read_text())
        assert loaded == data

    def test_save_citation_writes_json(self, tmp_path):
        ws = ResearchWorkspace(str(tmp_path))
        citation = {"session_id": "s", "question": "q", "answer": "a", "sources": []}
        path = ws.save_citation(citation)
        assert path.endswith(".json")
        assert len(ws.list_citations()) == 1
        loaded = json.loads(ws.citations_dir.joinpath(path.split("/")[-1]).read_text())
        assert loaded["question"] == "q"
