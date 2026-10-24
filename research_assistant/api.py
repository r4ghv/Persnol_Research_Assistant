"""FastAPI backend for the Personal Research Assistant.

Frontend (Gradio) → FastAPI → Research Services → Vector DB → LLM

Run with:  uvicorn research_assistant.api:app --reload
"""

import logging
from functools import wraps

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .services import ServiceContainer

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Personal Research Assistant API",
    description=(
        "REST backend for research pipeline, conversational RAG, "
        "comparison, and workspace."
    ),
    version="1.0.0",
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1)
    max_papers: int = Field(default=5, ge=1, le=20)
    summary_style: str = Field(default="bullet_points")
    sources: list[str] | None = None


class ChatSendRequest(BaseModel):
    session_id: str = Field(default="default")
    question: str = Field(min_length=1)
    k: int | None = Field(default=None, ge=1, le=20)


class ChatClearRequest(BaseModel):
    session_id: str = Field(default="default")


class CompareRequest(BaseModel):
    paper_ids: list[str] = Field(min_length=2)
    question: str = Field(min_length=1)
    k_per_paper: int = Field(default=3, ge=1, le=10)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=10, ge=1, le=50)


# ---------------------------------------------------------------------------
# Container lifecycle
# ---------------------------------------------------------------------------

_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Lazily build the service container (shared across requests)."""
    global _container
    if _container is None:
        logger.info("Building ServiceContainer...")
        _container = ServiceContainer()
    return _container


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _guard(fn):
    """Translate service exceptions into HTTP errors with a clean detail."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("API error in %s", getattr(fn, "__name__", "handler"))
            raise HTTPException(status_code=500, detail=str(e)) from e

    return wrapper




@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "personal-research-assistant"}


@app.post("/api/research")
@_guard
def run_research(req: ResearchRequest) -> dict:
    """Run the six-agent pipeline: Search → Read → Retrieve → Summarize → Critique → Report."""
    container = get_container()
    result = container.research.run(
        topic=req.topic,
        max_papers=req.max_papers,
        summary_style=req.summary_style,
        sources=req.sources,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result




@app.post("/api/chat/send")
@_guard
def chat_send(req: ChatSendRequest) -> dict:
    """Conversational RAG: answer grounded in stored chunks, with history."""
    container = get_container()
    return container.chat.send(req.session_id, req.question, k=req.k)


@app.post("/api/chat/clear")
@_guard
def chat_clear(req: ChatClearRequest) -> dict:
    container = get_container()
    return container.chat.clear(req.session_id)


@app.get("/api/chat/{session_id}/history")
@_guard
def chat_history(session_id: str) -> dict:
    container = get_container()
    return container.chat.history(session_id)


@app.post("/api/compare")
@_guard
def compare_papers(req: CompareRequest) -> dict:
    """Compare multiple stored papers with a structured, sourced answer."""
    container = get_container()
    return container.chat.compare(req.paper_ids, req.question, k_per_paper=req.k_per_paper)


@app.post("/api/search")
@_guard
def search_chunks(req: SearchRequest) -> dict:
    """Semantic search over stored paper chunks."""
    container = get_container()
    return {"results": container.workspace_service.search(req.query, k=req.k)}


@app.get("/api/papers")
def list_papers() -> dict:
    """Distinct papers stored in the vector database."""
    container = get_container()
    return {"papers": container.workspace_service.list_papers()}




@app.get("/api/workspace")
def workspace_summary() -> dict:
    """Workspace directory snapshot + counts."""
    container = get_container()
    return container.workspace_service.summary()


@app.delete("/api/papers/{paper_id}")
def delete_paper(paper_id: str) -> dict:
    """Remove a paper's chunks from the vector database."""
    container = get_container()
    return container.workspace_service.delete_paper(paper_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
