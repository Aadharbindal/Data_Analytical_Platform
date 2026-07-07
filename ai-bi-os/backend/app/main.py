from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router
from app.auth import rate_limiter

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="AI Business Intelligence Operating System (AI BI OS)",
    description="""Enterprise API Gateway for AI Decision Intelligence.
    
    This API provides the core functionality for the AI BI OS, including:
    - Complete dataset lifecycle management
    - Advanced statistical and Machine Learning analytics
    - Forecast validation and governance
    - Observability and pipeline tracking
    """,
    version="1.0.0",
    openapi_tags=[
        {"name": "analytics", "description": "Core analytics pipelines"},
        {"name": "forecast-governance", "description": "Model governance and monitoring endpoints"}
    ]
)

Instrumentator().instrument(app).expose(app)

from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        rate_limiter(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.dataset_router import router as dataset_router
from app.api.schema_router import router as schema_router
from app.api.profile_router import router as profile_router
from app.api.quality_router import router as quality_router
from app.api.cleaning_router import router as cleaning_router
from app.api.privacy_router import router as privacy_router, version_router as privacy_version_router
from app.api.semantic_router import router as semantic_router
from app.api.catalog_router import router as catalog_router
from app.api.query_router import router as query_router
from app.api.analytics_router import router as analytics_router
from app.api.insight_router import router as insight_router
from app.api.rule_router import router as rule_router
from app.api.recommendation_router import router as recommendation_router
from app.api.context_router import router as context_router
from app.api.prompt_router import router as prompt_router
from app.api.kpi_router import router as kpi_router
from app.api.ai_gateway_router import router as ai_gateway_router
from app.api.eda_router import router as eda_router
from app.api.correlation_router import router as correlation_router
from app.api.statistics_router import router as statistics_router
from app.api.regression_router import router as regression_router
from app.api.validation_router import router as validation_router
from app.api.distribution_router import router as distribution_router
from app.api.outlier_router import router as outlier_router
from app.api.timeseries_router import router as timeseries_router
from app.api.trend_router import router as trend_router
from app.api.forecast_router import router as forecast_router
from app.api.forecast_governance_router import router as forecast_governance_router
from app.api.business_metrics_router import router as business_metrics_router

app.include_router(router)
app.include_router(dataset_router)
app.include_router(schema_router)
app.include_router(profile_router)
app.include_router(quality_router)
app.include_router(cleaning_router)
app.include_router(privacy_router)
app.include_router(privacy_version_router)
app.include_router(semantic_router)
app.include_router(catalog_router)
app.include_router(query_router)
app.include_router(analytics_router)
app.include_router(insight_router)
app.include_router(rule_router)
app.include_router(recommendation_router)
app.include_router(context_router)
app.include_router(prompt_router)
app.include_router(kpi_router)
app.include_router(ai_gateway_router)
app.include_router(business_metrics_router)
app.include_router(eda_router)
app.include_router(correlation_router)
app.include_router(statistics_router)
app.include_router(regression_router)
app.include_router(validation_router)
app.include_router(distribution_router)
app.include_router(outlier_router)
app.include_router(timeseries_router)
app.include_router(trend_router)
app.include_router(forecast_router)
app.include_router(forecast_governance_router)
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "api-gateway"}
