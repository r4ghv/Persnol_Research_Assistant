import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from research_assistant.agents.vector_store import VectorStore


class TestVectorStoreStatic:
    def test_sanitize_id_replaces_special_chars(self):
        result = VectorStore._sanitize_id("http://arxiv.org/abs/2508.06494v1")
        assert "/" not in result
        assert ":" not in result
        assert result == "http_arxiv_org_abs_2508_06494v1"

    def test_sanitize_id_collapses_underscores(self):
        result = VectorStore._sanitize_id("a___b__c")
        assert "__" not in result
        assert result == "a_b_c"

    def test_sanitize_id_strips_edges(self):
        result = VectorStore._sanitize_id("__hello__")
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_sanitize_id_allows_hyphens(self):
        result = VectorStore._sanitize_id("paper-v2_3")
        assert result == "paper-v2_3"

    def test_format_results_empty(self):
        results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        assert VectorStore._format_results(results) == []

    def test_format_results_no_ids(self):
        results = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        assert VectorStore._format_results(results) == []

    def test_format_results_normal(self):
        results = {
            "ids": [["a", "b"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"k": "v1"}, {"k": "v2"}]],
            "distances": [[0.1, 0.2]],
        }
        out = VectorStore._format_results(results)
        assert len(out) == 2
        assert out[0]["id"] == "a"
        assert out[0]["document"] == "doc1"
        assert out[0]["metadata"] == {"k": "v1"}
        assert out[0]["distance"] == 0.1


class TestVectorStoreMocked:
    """Tests using a mocked chromadb PersistentClient."""

    @pytest.fixture
    def mock_client(self):
        with patch("chromadb.PersistentClient") as mc:
            instance = MagicMock()
            mc.return_value = instance
            yield instance

    @pytest.fixture
    def mock_collection(self, mock_client):
        coll = MagicMock()
        mock_client.get_collection.side_effect = ValueError("not found")
        mock_client.create_collection.return_value = coll
        return coll

    @pytest.fixture
    def store(self, mock_client, mock_collection):
        return VectorStore(
            api_key="sk-test-fake",
            collection_name="test_coll",
            persist_dir="/tmp/test_vector_store",
            embedding_model="text-embedding-3-small",
        )

    def test_init_creates_collection(self, store, mock_client, mock_collection):
        """Verify that when get_collection raises ValueError, create_collection is called."""
        mock_client.get_collection.assert_called_once()
        mock_client.create_collection.assert_called_once()
        assert store.collection is mock_collection

    def test_count_delegates(self, store, mock_collection):
        mock_collection.count.return_value = 7
        assert store.count() == 7
        mock_collection.count.assert_called_once()

    def test_delete_paper(self, store, mock_collection):
        store.delete_paper("test123")
        mock_collection.delete.assert_called_once_with(where={"paper_id": "test123"})

    def test_search_empty_query(self, store):
        assert store.search("") == []
        assert store.search("   ") == []

    def test_add_paper_chunks_no_content(self, store, mock_collection):
        """No chunks are stored when content is empty."""
        count = store.add_paper_chunks(
            paper_id="p1",
            title="Empty Paper",
            content="",
            metadata={"source": "arXiv"},
        )
        assert count == 0
        mock_collection.add.assert_not_called()

    def test_get_paper_chunks_empty(self, store, mock_collection):
        mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        result = store.get_paper_chunks("nonexistent")
        assert result == []

    def test_get_paper_chunks_found(self, store, mock_collection):
        mock_collection.get.return_value = {
            "ids": ["p1_chunk_0000"],
            "documents": ["some text"],
            "metadatas": [{"paper_id": "p1"}],
        }
        result = store.get_paper_chunks("p1")
        assert len(result) == 1
        assert result[0]["id"] == "p1_chunk_0000"
        assert result[0]["document"] == "some text"

    def test_init_creates_collection_on_not_found(self, mock_client, mock_collection):
        """chromadb raises NotFoundError (not ValueError) for a missing collection."""
        import chromadb

        mock_client.get_collection.side_effect = chromadb.errors.NotFoundError("missing")
        store = VectorStore(
            api_key="sk-test-fake",
            collection_name="test_coll",
            persist_dir="/tmp/test_vector_store",
            embedding_model="text-embedding-3-small",
        )
        mock_client.create_collection.assert_called_once()
        assert store.collection is mock_collection

    def test_list_papers_empty(self, store, mock_collection):
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        assert store.list_papers() == []

    def test_list_papers_dedupes_and_orders(self, store, mock_collection):
        mock_collection.get.return_value = {
            "ids": ["a", "b", "c", "d"],
            "metadatas": [
                {"paper_id": "p1", "title": "Paper One", "source": "arXiv", "url": "u1"},
                {"paper_id": "p2", "title": "Paper Two", "source": "PubMed", "url": "u2"},
                {"paper_id": "p1", "title": "Paper One", "source": "arXiv", "url": "u1"},
                {"paper_id": "p3", "title": "", "source": "S2", "url": "u3"},
            ],
        }
        papers = store.list_papers()
        assert [p["paper_id"] for p in papers] == ["p1", "p2", "p3"]
        assert papers[0]["title"] == "Paper One"
        assert papers[2]["title"] == "p3"  # falls back to paper_id when title is empty
