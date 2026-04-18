from fastapi import FastAPI
from app.api.v1.api import api_router
from app.api.middleware import AuditMiddleware

app = FastAPI(
    title="TIP API",
    description="Threat Intelligence Platform (TIP) - MVP",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
app.add_middleware(AuditMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Threat Intelligence Platform API v1"}
