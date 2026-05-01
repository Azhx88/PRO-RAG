# RAG BASED CONVERSATIONAL DATA ANALYTICS SYSTEM

## Project Overview

Full-stack RAG application that routes queries to either a **SQL pipeline** (Excel/CSV files) or a **vector search pipeline** (PDF/text files) based on the uploaded file type. Users upload files into workspaces, ask questions in a chat interface, and get AI-generated insights, charts, and Excel exports.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.111.0, Python 3.11, Uvicorn |
| ORM | SQLAlchemy 2.0.30 |
| Database | PostgreSQL 16 + pgvector extension |
| Auth | python-jose (JWT), passlib/bcrypt |
| LLM — chat/SQL | Groq `llama-3.3-70b-versatile` |
| LLM — embeddings | Google Gemini `text-embedding-004` (768-dim) |
| Document parsing | pdfplumber, PyMuPDF, pandas/openpyxl |
| Frontend | React 18.3, Vite 5.2, React Router 6 |
| HTTP client | Axios 1.7 |
| Infrastructure | Docker Compose (3 services: postgres, backend, frontend) |

## Key Directories

```
hybrid-rag/
├── backend/
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # FastAPI route handlers (thin — delegate to services)
│   ├── services/       # Business logic: LLM calls, file processing, charting
│   ├── utils/          # JWT helpers (auth_utils.py), file helpers
│   ├── config.py       # Pydantic BaseSettings — reads from .env
│   ├── database.py     # SQLAlchemy engine, get_db() dependency, init_db()
│   └── main.py         # App factory: CORS, router registration, static files
├── frontend/
│   ├── src/api/        # Axios client with auth interceptors + API namespaces
│   ├── src/components/ # Presentational components by feature (auth/chat/workspace)
│   ├── src/context/    # AuthContext — global JWT + user state
│   ├── src/hooks/      # useAuth, useChat
│   └── src/pages/      # LoginPage, RegisterPage, DashboardPage
├── uploads/            # Persisted file storage + generated chart PNGs
├── .env                # Secrets (DATABASE_URL, GEMINI_API_KEY, GROQ_API_KEY, etc.)
└── docker-compose.yml
```

## Essential Commands

```bash
# Start all services (first run or after code changes)
docker-compose up --build

# Start without rebuilding
docker-compose up

# View live logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down

# Wipe DB volume (full reset)
docker-compose down -v
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`
Frontend: http://localhost:5173

## Environment Variables

All read from `.env` via `backend/config.py:1`. Required:
- `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `GEMINI_API_KEY`, `GROQ_API_KEY`
- `UPLOAD_DIR` (Docker default: `/app/uploads`)

## Known Issues / Constraints

- `passlib` is incompatible with `bcrypt >= 4.0`. Pin: `bcrypt==3.2.2` or `bcrypt==4.0.1` in `backend/requirements.txt:9`
- `metadata` is a reserved SQLAlchemy attribute. Both `ChatMessage` and `DocumentChunk` use `meta` as the Python attribute with `Column("metadata", ...)` to preserve the DB column name — see `backend/models/chat.py:18` and `backend/models/vector_store.py:12`
- Chart static files served at `/charts/` via FastAPI `StaticFiles` mount — see `backend/main.py`

## Additional Documentation

| Topic | File |
|---|---|
| Architectural patterns & design decisions | `.claude/docs/architectural_patterns.md` |
