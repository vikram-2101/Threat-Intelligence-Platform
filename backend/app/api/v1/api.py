from fastapi import APIRouter
from app.api.v1.endpoints import sources, indicators, auth, analyst_actions, export, audit_logs

api_router = APIRouter()

api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(
    analyst_actions.router,
    prefix="/indicators",
    tags=["analyst-actions"],
)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
