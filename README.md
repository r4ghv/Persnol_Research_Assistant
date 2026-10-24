# 🔬 Personal Research Assistant

An AI-powered research assistant that discovers academic papers across **arXiv, PubMed and Semantic Scholar**, extracts and summarizes them with an LLM, and lets you chat with your papers using **RAG** (Retrieval-Augmented Generation) — with a **FastAPI** backend and a **React + TypeScript** frontend.

```
React UI (Vite)  →  FastAPI REST API  →  Service layer  →  ChromaDB vector store / OpenAI LLM
```

## Features

- **Multi-source search** — arXiv, PubMed and Semantic Scholar behind a common `PaperSource` interface, with relevance ranking
- **Multi-agent pipeline** — search → read → retrieve → summarize → critique → report
- **PDF processing** — text extraction (PyMuPDF), section detection and chunking
- **RAG chat** — multi-turn Q&A over your papers using a ChromaDB vector store, with cited sources
- **Paper comparison** — compare multiple papers side by side
- **Research workspace** — papers, notes, chat history, reports and citations organized automatically
- **Resilience** — caching, timeouts, retry/backoff for rate-limited APIs, structured logging
- **Tested** — 107 pytest tests across the API, pipeline, RAG, vector store, conversation and workspace

## Tech Stack

| Layer    | Technology                                   |
|----------|----------------------------------------------|
| Backend  | Python, FastAPI, Pydantic, Uvicorn           |
| AI / RAG | OpenAI SDK, ChromaDB, PyMuPDF                |
| Frontend | React, TypeScript, Vite, Tailwind CSS        |
| Testing  | pytest                                       |

## Setup

### 1. Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your OPENAI_API_KEY
```

### 2. Frontend

```bash
cd frontend
bun install                 # or: npm install
```

## Running

```bash
# Terminal 1 — API at http://127.0.0.1:8000  (docs at /docs)
uvicorn research_assistant.api:app --reload

# Terminal 2 — UI at http://localhost:5173
cd frontend && bun run dev  # or: npm run dev
```

The legacy Gradio interface is still available with `python main.py` (http://localhost:7860).

## API Endpoints

| Method | Endpoint                          | Description                        |
|--------|-----------------------------------|------------------------------------|
| GET    | `/api/health`                     | Health check                       |
| POST   | `/api/research`                   | Run the research pipeline on a topic |
| POST   | `/api/search`                     | Semantic search over stored papers |
| POST   | `/api/compare`                    | Compare multiple papers            |
| POST   | `/api/chat/send`                  | Ask a question (RAG chat)          |
| POST   | `/api/chat/clear`                 | Clear a chat session               |
| GET    | `/api/chat/{session_id}/history`  | Get chat history                   |
| GET    | `/api/papers`                     | List papers                        |
| DELETE | `/api/papers/{paper_id}`          | Delete a paper                     |
| GET    | `/api/workspace`                  | Workspace overview                 |

## Tests

```bash
pip install pytest
pytest
```

## Project Structure

```
├── research_assistant/
│   ├── api.py               # FastAPI app and routes
│   ├── services/            # Service layer (research, chat, workspace, container)
│   ├── agents/              # sources, scraper, ranker, preprocessor, summarizer,
│   │                        # pipeline, rag, vector_store, conversation, organizer
│   ├── utils/               # config, logging, file helpers
│   └── workspace.py         # Research workspace management
├── frontend/                # React + TypeScript (Vite) UI
├── tests/                   # pytest suite
├── main.py                  # Legacy Gradio UI
└── research_output/         # Generated papers, summaries and reports
```

## Configuration

All settings are read from `.env` — see [`.env.example`](.env.example) for the full list (model, token limits, paper limits, timeouts, ChromaDB location, RAG top-k, workspace directory).

## License

MIT
