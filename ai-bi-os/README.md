# AI BI OS: Enterprise AI Decision Intelligence Platform

Welcome to the AI BI OS. This is a Next-Generation AI Business Intelligence platform designed to autonomously analyze, visualize, and reason over your enterprise data using large language models.

## Architecture

The AI BI OS is built on a modern, decoupled architecture:
1. **Frontend**: Next.js + React + Recharts (Port 3000)
2. **Backend**: FastAPI + Python (Port 8000)
3. **Data Engine**: DuckDB (In-memory analytical SQL engine)
4. **AI Core**: LiteLLM Multi-Agent Orchestrator (ReAct Loop)
5. **Knowledge Base**: Semantic Vector Store (RAG)

## Key Features
- **Instant Data Ingestion**: Upload a CSV and DuckDB automatically infers schema and calculates KPI aggregations.
- **Text-to-SQL ReAct Loop**: Talk to your data. The AI acts as an autonomous agent that writes SQL, executes it against DuckDB, and interprets the results.
- **Data Lineage & Transparency**: The exact SQL queries executed by the AI are surfaced in the Chat UI so your analysts can verify the math.
- **Semantic RAG**: The system understands both quantitative metrics (via DuckDB) and qualitative business policies (via the RAG engine), automatically choosing the right tool for your question.

## Quickstart

We've provided a simple batch script to spin up the entire ecosystem on Windows.

1. Ensure you have `python` and `npm` installed.
2. In the `backend` folder, create a `.env` file with your `OPENAI_API_KEY`.
3. Double-click the `start_servers.bat` file in the root directory.

The frontend dashboard will be available at `http://localhost:3000`.

## Testing

To run the backend unit tests:
```bash
cd backend
python -m pytest tests/
```
