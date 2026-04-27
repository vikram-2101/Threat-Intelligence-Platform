from fastapi import APIRouter
from app.api.v1.endpoints import sources, indicators, auth, analyst_actions

api_router = APIRouter()

api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(
    analyst_actions.router,
    prefix="/indicators",
    tags=["analyst-actions"],
)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
