import logging
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routers import datasets, analytics, catalog, chat, regression, classification, clustering, share

from app.core.config import CORS_ORIGIN

# Analytics responses are assembled from pandas/numpy results, and a single
# un-cast numpy scalar anywhere in a payload makes the JSON encoder raise —
# turning an otherwise successful request into a 500 (a numpy.bool_ from a
# collinearity check did exactly that). Teaching the encoder these types once
# removes the whole failure class rather than relying on every call site to
# remember an int()/float()/bool() cast.
import numpy as _np
from fastapi.encoders import ENCODERS_BY_TYPE as _ENCODERS_BY_TYPE

for _np_type, _py_type in (
    (_np.bool_, bool),
    (_np.int8, int), (_np.int16, int), (_np.int32, int), (_np.int64, int),
    (_np.uint8, int), (_np.uint16, int), (_np.uint32, int), (_np.uint64, int),
    (_np.float16, float), (_np.float32, float), (_np.float64, float),
):
    _ENCODERS_BY_TYPE.setdefault(_np_type, _py_type)
_ENCODERS_BY_TYPE.setdefault(_np.ndarray, lambda a: a.tolist())

import math as _math
from fastapi.responses import JSONResponse as _JSONResponse


def _json_safe(value):
    """Replace NaN/Infinity with null so a payload stays valid JSON.

    Statistical results legitimately reach these values — a VIF of infinity for
    perfectly collinear features, a correlation over a zero-variance column —
    but JSON has no way to express them, so json.dumps raises and the whole
    request fails with a 500 instead of returning the analysis. null is the
    honest representation: the quantity exists but has no finite value.
    """
    if isinstance(value, float):
        return value if _math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


class SafeJSONResponse(_JSONResponse):
    def render(self, content) -> bytes:
        return super().render(_json_safe(content))


# Before the app, so anything that fails during startup is reported too - the
# failures hardest to find are the ones that happen before there is a server to
# ask. No-op unless SENTRY_DSN is set.
from app.core.error_tracking import init_error_tracking, capture

init_error_tracking()

app = FastAPI(
    title="Numerate OS Backend",
    redirect_slashes=False,
    default_response_class=SafeJSONResponse,
)

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
app.include_router(classification.router, prefix="/api/v1/analytics/classification", tags=["classification"])
app.include_router(clustering.router, prefix="/api/v1/analytics/clustering", tags=["clustering"])
app.include_router(share.router, prefix="/api/v1/share", tags=["share"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
# Also include insights router for executive summary etc.
from app.routers import insights, auth, recommendations, rules, ai_gateway, dashboard, notifications, telemetry
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
app.include_router(ai_gateway.router, prefix="/api/v1/ai-gateway", tags=["ai-gateway"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])

@app.on_event("startup")
async def check_storage_on_startup():
    """Say at boot whether uploaded files will survive.

    This is the check that would have caught the problem it was written for:
    object storage had been unreachable for months, uploads were silently
    falling back to local disk, and the host wipes that disk on every deploy.
    Nobody found out until a shared dashboard could not find its dataset.
    Asking the question while someone is watching a deploy is much cheaper.
    """
    try:
        from app.services.storage import report_storage_status

        report_storage_status()
    except Exception:
        logging.getLogger("app").exception("Storage status check failed to run")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    """Report anything that got all the way out, then answer plainly.

    Sentry's integration already catches most of this; the handler exists so
    the reply is deliberate rather than a stack trace, and so the report
    carries the path that produced it. It is registered for Exception only, so
    HTTPException and the rate-limit response still travel their own routes -
    a 404 is an answer, not a fault.
    """
    capture(exc, path=str(request.url.path), method=request.method)
    logging.getLogger("app").exception("Unhandled error on %s %s", request.method, request.url.path)
    return _JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. The error has been recorded."},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
