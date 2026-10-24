"""Services layer: owns agent wiring and business logic for the FastAPI backend.

Frontend → FastAPI → Services → Vector DB → LLM
"""

from .chat import ChatService
from .container import ServiceContainer
from .research import ResearchService
from .workspace import WorkspaceService

__all__ = [
    "ServiceContainer",
    "ResearchService",
    "ChatService",
    "WorkspaceService",
]
