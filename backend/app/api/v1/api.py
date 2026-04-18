from fastapi import APIRouter
from app.api.v1.endpoints import sources, indicators, auth

api_router = APIRouter()

api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
