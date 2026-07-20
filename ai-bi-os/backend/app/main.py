import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routers import datasets, analytics, catalog, chat, regression

from app.core.config import CORS_ORIGIN

app = FastAPI(title="DataMind OS Backend", redirect_slashes=False)

# Allow requests from frontend
origins = [
    CORS_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://datamind-frontend-kmsr.onrender.com",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

# Comma-separated list of additional allowed origins (e.g. Vercel prod + preview URLs)
extra_origins = os.getenv("ALLOWED_ORIGINS", "")
origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])



app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(regression.router, prefix="/api/v1/analytics/regression", tags=["regression"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
# Also include insights router for executive summary etc.
from app.routers import insights, auth, recommendations, rules, rag, ai_gateway, agents, decision_rules
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Rate limiter setup
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: Response("Rate limit exceeded", status_code=429))
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(origins)),
    allow_origin_regex=r"https://.*\.(onrender\.com|vercel\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["insights"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(ai_gateway.router, prefix="/api/v1/ai-gateway", tags=["ai-gateway"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(decision_rules.router, prefix="/api/v1/decision-rules", tags=["decision-rules"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
