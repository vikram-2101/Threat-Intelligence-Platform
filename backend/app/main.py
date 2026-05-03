from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.middleware import AuditMiddleware

app = FastAPI(
    title="TIP API",
    description="Threat Intelligence Platform (TIP) - MVP",
    version="0.1.0",
)

# ── Middleware (order matters: Starlette applies in REVERSE registration order) ─
# AuditMiddleware must be added AFTER CORSMiddleware so Starlette runs
# CORSMiddleware first (it was second to be added = first to execute).
# This ensures CORS preflight and response headers are always present.
import os

# CORS origins are driven by environment variables for production safety.
# In dev, these default to localhost. In production, set ALLOWED_ORIGINS
# in your Render environment to your Vercel URL.
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost,http://localhost:80"
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(AuditMiddleware)   # runs second (inner)
app.add_middleware(                   # runs first (outer) ← correct for CORS
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Threat Intelligence Platform API v1"}
