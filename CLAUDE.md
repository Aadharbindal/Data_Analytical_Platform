# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

The repository root contains two unrelated things:
- **`ai-bi-os/`** — the actual application (FastAPI backend + Next.js frontend). All code work happens here.
- Root-level `.docx`/`.txt` files (`Volume1/2/3_*`, `AI_Business_Analyst_PRD_*`, `parsed_texts/`) — design/spec documents for the product, parsed via `parse_docx.py`. These are reference material, not source code; don't treat them as authoritative for current implementation state.

Everything below refers to paths inside `ai-bi-os/`.

## Commands

### Backend (FastAPI, Python, from `ai-bi-os/backend/`)
```bash
# Activate the existing venv (Windows)
.\venv\Scripts\activate

# Run the dev server
python -m uvicorn app.main:app --reload --port 8000

# Run all tests
python -m pytest tests/

# Run a single test file / test
python -m pytest tests/test_forecast.py
python -m pytest tests/test_forecast.py::test_specific_case -v

# Root-level integration tests (not in tests/) also exist and run the same way:
python -m pytest test_analytics_integration.py test_privacy_integration.py
```

### Frontend (Next.js, from `ai-bi-os/frontend/`)
```bash
npm run dev      # dev server on :3000
npm run build
npm run start
npm run lint
```

### Full stack
- `ai-bi-os/start_servers.bat` — Windows convenience script; kills ports 3000/8000, then launches backend (`uvicorn --reload`) and frontend (`npm run dev`) in separate terminals.
- `docker-compose.yml` (in `ai-bi-os/`) — full stack incl. Redis, Celery worker, Prometheus, Grafana. `docker-compose.redis.yml` is a lighter Redis-only compose file.

### Environment
Backend reads its LLM provider key from `ai-bi-os/backend/.env` (copy from `.env.example`). Supports `GEMINI_API_KEY` (default provider), `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`, routed through LiteLLM.

## Architecture

### Big picture
Decoupled two-service architecture:
1. **Frontend** — Next.js 16 (App Router) + React 19 + Recharts, port 3000, in `ai-bi-os/frontend/`.
2. **Backend** — FastAPI + Python, port 8000, in `ai-bi-os/backend/`.
3. **Analytical data engine** — DuckDB, used as an in-memory SQL engine over uploaded datasets (not the system-of-record DB).
4. **System-of-record DB** — SQLite (`ai_bi_os.db`) via SQLAlchemy ORM, for app metadata/entities (see `app/core/database.py`). Tables are created at startup via `Base.metadata.create_all`.
5. **AI Core** — LiteLLM-based multi-agent orchestrator running a ReAct tool-calling loop (`app/ai/agents.py`, `app/ai/registry.py`).
6. **Async jobs** — Celery + Redis for long-running AI queries (`app/worker.py`, `/api/v1/chat/async`).
7. **Observability** — `prometheus-fastapi-instrumentator` auto-exposes metrics; Prometheus + Grafana wired in docker-compose.

### Backend module structure
The backend follows a consistent layered pattern **per feature domain** (e.g. `forecast`, `correlation`, `privacy`, `rag`, `business_metrics`, `ai_gateway`, `decision_intelligence`, ...). For a given domain, expect up to four parallel files/dirs:
- `app/api/<domain>_router.py` — FastAPI route definitions.
- `app/schemas/<domain>.py` — Pydantic request/response models.
- `app/models/<domain>.py` — SQLAlchemy ORM models.
- `app/repositories/<domain>_repository.py` — DB access layer.
- `app/services/<domain>/` — business logic, often further split into per-concern engines (e.g. `services/analytics/{correlation_engine,trend_engine,variance_engine,segmentation_engine,metric_engine,insight_builder}.py`).

When adding or modifying a feature, expect to touch several of these files in parallel rather than one monolithic file — grep across `api/`, `schemas/`, `models/`, `repositories/`, and `services/<domain>/` for the domain name to find everything.

**Router wiring is two-tiered**: most domain routers are included in `app/api/routers.py` (which is then included as the single generic `router` in `main.py`), but several analytics-adjacent routers (`dataset_router`, `analytics_router`, `forecast_router`, `kpi_router`, etc.) are imported and `include_router`'d directly in `app/main.py`. Check both files when tracing how an endpoint is mounted, or when adding a new router.

### AI orchestration
- `app/ai/agents.py` defines `AgentOrchestrator.run_query()` — the main ReAct loop: sends messages + tool schema to the model via `ModelRegistry.route_request()`, executes any tool calls against an `MCPToolAbstraction` (DuckDB query tools + RAG tools, see `app/ai/mcp_tools.py`), feeds results back, and loops (max 3 iterations) until a final text/JSON response.
- `app/ai/registry.py` (`ModelRegistry`) is the thin LiteLLM wrapper actually used by `AgentOrchestrator`. There is a **separate, more elaborate** AI Gateway subsystem at `app/services/ai_gateway/` (model routing, cost engine, circuit breaker, fallback manager, health monitor, retry manager, stream manager, token manager) exposed via `ai_gateway_router.py` — this is a distinct, more "enterprise" routing layer, not currently the one wired into `AgentOrchestrator`. Don't assume the two are the same code path.
- When the AI response is meant to render a chart, the system prompt instructs the model to return a JSON object with `text_response` and `chart_config` keys instead of plain text — the frontend chat UI expects this shape when a chart was requested.
- The DuckDB engine (`app/services/duckdb_engine.py`) currently loads uploaded CSVs into a single fixed table named `current_dataset` (see `POST /api/v1/upload` in `app/api/routers.py`) — there's no multi-dataset table namespace yet at that entry point.

### Frontend structure
Next.js App Router under `frontend/src/app/`, organized by top-level feature: `analytics/` (with nested routes per analysis type: `correlation`, `forecast`, `regression`, `timeseries`, `trend`, `outliers`, `distribution`, `eda`, `kpi`, `governance`, `metrics`, `confidence`), plus `admin/` (mirrors many backend "intelligence engine" domains: `ai-evaluation`, `ai-validation`, `business-rules`, `decisions`, `multi-agent`, `vector-store`, etc.), `chat/`, `datasets/`, `data-catalog/`, `insights/`, `knowledge-console/`, `privacy/`, `python-console/`, `recommendations/`, `rules/`.
- `src/lib/api.ts`, `src/api/*.ts` — API client functions calling the FastAPI backend.
- `src/components/ui/` — shadcn-style primitives (button, card, table, etc.).
- `src/components/dashboard/`, `src/components/admin/*` — feature-specific composed components.
- State/data fetching: TanStack Query (`@tanstack/react-query`) + Zustand.
- **Note**: `frontend/AGENTS.md` and `frontend/CLAUDE.md` both point to Next.js–specific agent rules embedded in `node_modules/next/dist/docs/` — this project pins a Next.js version with breaking API/convention changes from typical training data. Read the relevant doc there before writing Next.js code (routing, data fetching, config) in `frontend/`.

### Known rough edges (don't "fix" silently — these reflect early-stage/demo code)
- `app/auth.py` hardcodes `SECRET_KEY = "enterprise_super_secret_key"` and uses an in-memory rate-limit store — not production auth.
- `app/core/database.py` is explicitly labeled a "Temporary SQLite DB for Module 1".
- CORS in `main.py` allows `["http://localhost:3000", "*"]` together (the wildcard makes the explicit origin redundant).
