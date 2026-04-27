from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.middleware import AuditMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.core.limiter import limiter
from app.core.config import settings

app = FastAPI(
    title="TIP API",
    description="Threat Intelligence Platform (TIP) - MVP",
    version="0.1.0",
)

# ── Middleware (order matters: Starlette applies in REVERSE registration order) ─
# AuditMiddleware must be added AFTER CORSMiddleware so Starlette runs
# CORSMiddleware first (it was second to be added = first to execute).
# This ensures CORS preflight and response headers are always present.
app.add_middleware(AuditMiddleware)   # runs second (inner)
app.add_middleware(                   # runs first (outer) ← correct for CORS
    CORSMiddleware,
    allow_origins=settings.FRONTEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Threat Intelligence Platform API v1"}
