import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import datasets, analytics, catalog, chat

from app.core.config import CORS_ORIGIN

app = FastAPI(title="DataMind OS Backend")

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
# Also include insights router for executive summary etc.
from app.routers import insights
app.include_router(insights.router, prefix="/api/v1/insights", tags=["insights"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
