# AI BI OS: Enterprise AI Decision Intelligence Platform
# DataMind OS

Welcome to the AI BI OS. This is a Next-Generation AI Business Intelligence platform designed to autonomously analyze, visualize, and reason over your enterprise data using large language models.
**An AI business intelligence platform that never lets an AI make up a number.**

## Architecture
Upload a CSV. Get real KPIs, real forecasts, real correlations — computed the boring, reliable way, with pandas and statsmodels. Then let an LLM explain what it all means, in plain English, with every claim it makes checked against the actual data before it ever reaches your screen.

---

## Why this exists

Most "AI analytics" tools have the same failure mode: ask them a hard question, and they'll give you a confident, well-formatted, completely wrong answer. The number sounds right. The sentence is fluent. It's just not true.

This project was built around a different rule, applied without exception:

> **The LLM is never allowed to compute a number. It is only allowed to describe a number that deterministic code already computed and verified.**

That single constraint shapes almost everything below — from how the Dashboard works, to why the Copilot writes SQL instead of guessing answers, to why every AI-generated insight carries a visible `Verified` / `Unverified` badge instead of a blanket assurance that it's correct.

---

## What it actually does

The AI BI OS is built on a modern, decoupled architecture:
1. **Frontend**: Next.js + React + Recharts (Port 3000)
2. **Backend**: FastAPI + Python (Port 8000)
3. **Data Engine**: DuckDB (In-memory analytical SQL engine)
4. **AI Core**: LiteLLM Multi-Agent Orchestrator (ReAct Loop)
5. **Knowledge Base**: Semantic Vector Store (RAG)
### Upload → Understand
Drop in a CSV (sales data, bank statements, SaaS subscriptions, whatever). The platform auto-detects which column is revenue, which is a customer/user count, which represents deal size, and which tracks pipeline status — using a widened, battle-tested pattern match that understands `Revenue`, `MRR`, `ARR`, `GMV`, `Turnover`, `Amount`, `Net Sales`, and variants of each, while correctly *ignoring* things like a `Narration` column that happens to contain the letters "arr" in the middle of a word. (That specific bug — and the fix — is documented further down, because it's a good example of how this project actually got tested.)

## Key Features
- **Instant Data Ingestion**: Upload a CSV and DuckDB automatically infers schema and calculates KPI aggregations.
- **Text-to-SQL ReAct Loop**: Talk to your data. The AI acts as an autonomous agent that writes SQL, executes it against DuckDB, and interprets the results.
- **Data Lineage & Transparency**: The exact SQL queries executed by the AI are surfaced in the Chat UI so your analysts can verify the math.
- **Semantic RAG**: The system understands both quantitative metrics (via DuckDB) and qualitative business policies (via the RAG engine), automatically choosing the right tool for your question.
### The Analytics Studio
A full suite of exploration tools, all backed by real pandas/numpy/scipy computation:

## Quickstart
| Tool | What it computes |
|---|---|
| EDA | Per-column profiling — types, nulls, distinct values, top categories |
| Statistics | Mean, median, std dev, skewness, kurtosis |
| Correlation | Pearson correlation matrix across numeric columns |
| Distribution | Histograms per column |
| Outliers | Z-score *and* IQR-based anomaly detection |
| Trend Analysis | Linear regression slope, direction, and strength (r²) |
| Time Series | Real monthly aggregation of any metric |
| Regression | scikit-learn linear regression — train on any target/feature combination, real R² |
| Forecast | Linear trend or Holt-Winters seasonal projection, with confidence bounds |

We've provided a simple batch script to spin up the entire ecosystem on Windows.
None of this touches an LLM. It doesn't need to — this is arithmetic, and arithmetic doesn't hallucinate.

1. Ensure you have `python` and `npm` installed.
2. In the `backend` folder, create a `.env` file with your `OPENAI_API_KEY`.
3. Double-click the `start_servers.bat` file in the root directory.
### The Copilot
Ask it a question in plain language. It doesn't guess an answer — it writes a real SQL query, runs it against your actual data through DuckDB, and only then answers, with the executed query visible for you to audit. Ask it something the data genuinely can't answer (profit margin, when there's no cost column) and it says so, instead of inventing a number to sound helpful.

The frontend dashboard will be available at `http://localhost:3000`.
### The Deep Insights Engine
The most ambitious piece. Instead of waiting for you to ask a question, this engine autonomously generates six analytical questions about your dataset, writes SQL to answer each one (through a SELECT-only safety gate that rejects anything resembling `DROP`, `DELETE`, `INSERT`, or a dozen other dangerous keywords), and turns the results into insights — each one re-verified against its own underlying query before it's shown to you.

## Testing
### Confidence Center
A dedicated transparency dashboard. It shows what percentage of AI-generated insights and recommendations actually passed verification, with a full audit trail linking every claim back to the SQL that produced it. Nothing here is aspirational marketing copy — if the AI got something wrong, this page shows it got something wrong.

---

## How we actually know it works

This is the part most project READMEs skip, and it's the part that matters most.

During development, the platform was tested against more than a dozen independently generated datasets — a retail electronics chain, a SaaS subscription business, a gym membership system, several bank statement formats, a corporate payments ledger, a digital wallet transaction log. For each one, every number the app displayed was cross-checked against a completely separate calculation, written fresh in a plain Python script that never touched the app's own code. If the numbers didn't match exactly, it was treated as a bug — not a rounding quirk to wave away.

That process caught real problems, including:

- **A column-detection collision.** The revenue-detection logic matched on the substring `arr` to catch `ARR` (Annual Recurring Revenue). It also matched the middle of the word `Narration` — so a dataset with a `Narration` text column had its entire Dashboard silently break, with the app trying to sum a column full of sentences. Fixed by filtering to numeric-dtype columns *before* applying any name pattern, not after.
- **A fabricated statistic.** One "insight" confidently stated that a customer had a "1 out of 1000" likelihood of making a large payment "within the next week." There is no forecasting model anywhere in that pipeline capable of computing a future probability from a flat SQL query — the number came from nowhere. Fixed with an explicit system-prompt restriction against predictive claims, plus a language filter that catches this pattern even if it slips past the first line of defense.
- **Silent overfitting.** A "Trend" insight was built from calendar-day averages based on a sample size of one or two transactions per day — technically accurate arithmetic, dressed up as a meaningful pattern it wasn't. Fixed by requiring every grouped query to report its own sample size, and rejecting anything built on too few rows.
- **Route shadowing.** A generic `/{dataset_id}` route was registered before a specific `/compare` route, so every request to `/datasets/compare` was silently intercepted and treated as a lookup for a dataset literally named "compare" — a 404 with a confusing cause. Fixed by registering specific routes before catch-all ones (and now this pattern is checked for elsewhere in the codebase too).

None of these were found by guessing. They were found by refusing to accept "it looks right" as good enough, and checking the arithmetic every time.

---

## Architecture

```
Next.js Frontend
      │
      ▼
FastAPI Backend
 ├── Auth            bcrypt + JWT (httpOnly cookies) + rate limiting
 ├── Analytics Engine pandas / numpy / scipy / statsmodels
 ├── Regression       scikit-learn
 ├── Chat Agent   →   DuckDB (real SQL execution)
 ├── Insights Engine  LLM + SQL sandbox + independent re-verification
 └── PDF Generator    reportlab + matplotlib
      │
      ▼
SQLite (users, datasets, insights, rules, regression models)
      │
      ▼
Groq API (gpt-oss-120b) — used only for Chat, Summaries, and Insights narration
```

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js, React, Tailwind |
| Backend | FastAPI (Python) |
| Database | SQLite |
| Query engine (Chat) | DuckDB |
| Statistics | pandas, numpy, scipy, statsmodels |
| Machine learning | scikit-learn |
| LLM inference | Groq (`openai/gpt-oss-120b`) |
| PDF generation | reportlab, matplotlib |
| Auth | bcrypt, PyJWT |

---

## Getting Started

To run the backend unit tests:
```bash
cd backend
python -m pytest tests/
# Backend
cd ai-bi-os/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add GROQ_API_KEY and SECRET_KEY
uvicorn app.main:app --reload

# Frontend
cd ai-bi-os/frontend
npm install
npm run dev
```

Groq's free tier is enough to run every AI feature in this project at zero cost. Without a key, the platform still works fully — the analytics engine doesn't need one, and the AI features degrade to clear "not configured" states instead of failing silently.

---

## What's not here yet

In the interest of not overselling this: it currently runs on SQLite (fine for individual or small-team use, not yet built for large multi-tenant scale), regression is linear-only (no classification or clustering yet), and there's no mobile-responsive layout — it's built for a desktop browser. These are documented, not hidden.

---

## A closing thought

The interesting engineering problem here was never "can an LLM write a paragraph about a spreadsheet." It's "how do you let an LLM be genuinely useful for analysis without ever trusting it to do the arithmetic." Everything in this repository is downstream of that question.
