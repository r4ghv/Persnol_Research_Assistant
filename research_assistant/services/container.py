"""ServiceContainer: single wiring point for agents + services.

Frontend → FastAPI → ServiceContainer {research, chat, workspace} → Vector DB → LLM
"""

import logging

from ..agents import (
    Organizer,
    RAGAssistant,
    ResearchPipeline,
    Scraper,
    Summarizer,
    VectorStore,
)
from ..utils.config import Config
from ..utils.logger import Logger
from ..workspace import ResearchWorkspace
from .chat import ChatService
from .research import ResearchService
from .workspace import WorkspaceService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Construct and own every agent and service the backend needs."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.logger = Logger()

        # Research workspace (Papers, Notes, Chat History, Highlights, Reports, Citations)
        self.workspace = ResearchWorkspace(str(self.config.WORKSPACE_DIR))

        # Agents
        self.scraper = Scraper(config=self.config)
        self.summarizer = Summarizer(self.config.OPENAI_API_KEY, self.config.OPENAI_MODEL)
        self.organizer = Organizer(str(self.config.OUTPUT_DIR))
        self.vector_store = VectorStore(
            api_key=self.config.OPENAI_API_KEY,
            collection_name=self.config.CHROMA_COLLECTION,
            persist_dir=str(self.config.BASE_DIR / self.config.CHROMA_PERSIST_DIR),
            embedding_model=self.config.EMBEDDING_MODEL,
        )
        self.rag = RAGAssistant(
            api_key=self.config.OPENAI_API_KEY,
            vector_store=self.vector_store,
            model=self.config.RAG_MODEL,
            top_k=self.config.RAG_TOP_K,
        )
        self.pipeline = ResearchPipeline(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL,
            scraper=self.scraper,
            summarizer=self.summarizer,
            vector_store=self.vector_store,
            organizer=self.organizer,
            timeout=self.config.REQUEST_TIMEOUT,
            log=self.logger.log,
        )

        # Services
        self.research = ResearchService(self.pipeline, self.organizer, self.workspace)
        self.chat = ChatService(
            api_key=self.config.OPENAI_API_KEY,
            rag=self.rag,
            workspace=self.workspace,
            model=self.config.RAG_MODEL,
            top_k=self.config.RAG_TOP_K,
        )
        self.workspace_service = WorkspaceService(self.workspace, self.vector_store)
