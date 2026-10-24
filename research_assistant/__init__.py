# Research Assistant Package
"""Personal Research Assistant using OpenAI and Gradio"""

__version__ = "1.0.0"
__author__ = "Research Assistant Team"

# Import main components
from .agents import (
    ChatSession,
    Organizer,
    RAGAssistant,
    ResearchPipeline,
    Scraper,
    Summarizer,
    VectorStore,
)
from .services import ChatService, ResearchService, ServiceContainer, WorkspaceService
from .utils import Config, Logger
from .workspace import ResearchWorkspace

__all__ = [
    'VectorStore',
    'RAGAssistant',
    'ResearchPipeline',
    'ChatSession',
    'ResearchWorkspace',
    'ServiceContainer',
    'ResearchService',
    'ChatService',
    'WorkspaceService',
    'Summarizer',
    'Organizer',
    'Scraper',
    'Logger',
    'Config'
]
