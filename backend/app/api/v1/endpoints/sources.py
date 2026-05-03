import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, RoleChecker, get_current_user
from app.models.user import RoleName
from app.schemas.source import SourceCreate, SourceUpdate, SourceResponse
from app.services.source_service import SourceService

router = APIRouter()

# ADMIN-only dependency for destructive operations (Phase 1.1 Requirement)
admin_deps = [Depends(RoleChecker([RoleName.ADMIN]))]
# Standard active session for read-only operations
auth_deps = [Depends(get_current_user)]

@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, dependencies=admin_deps)
async def create_source(
    *,
    db: AsyncSession = Depends(get_db),
    source_in: SourceCreate
):
    """
    Register a new threat intelligence source. 
    Restricted to ADMIN role.
    """
    return await SourceService.create_source(db, source_in)

@router.get("", response_model=List[SourceResponse], dependencies=auth_deps)
async def list_sources(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all registered intelligence sources. 
    Accessible by ADMIN and ANALYST.
    """
    return await SourceService.get_all_sources(db, skip=skip, limit=limit)

@router.get("/{source_id}", response_model=SourceResponse, dependencies=auth_deps)
async def get_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve details for a specific intelligence source.
    """
    source = await SourceService.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.patch("/{source_id}", response_model=SourceResponse, dependencies=admin_deps)
async def update_source(
    source_id: uuid.UUID,
    source_in: SourceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing intelligence source. 
    Restricted to ADMIN role.
    """
    source = await SourceService.update_source(db, source_id, source_in)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin_deps)
async def delete_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an intelligence source from the system. 
    Restricted to ADMIN role.
    """
    success = await SourceService.delete_source(db, source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    return None


import httpx
from datetime import datetime, timezone
from app.services.ingestion_service import IngestionService
from app.services.parser import IndicatorParser

@router.post("/{source_id}/pull", dependencies=auth_deps)
async def trigger_source_pull(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger an on-demand pull for a specific external feed.
    """
    source = await SourceService.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.pull_url:
        raise HTTPException(status_code=400, detail="This source does not have a pull URL configured")

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            response = await client.get(source.pull_url)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch feed: {response.text[:200]}")
            
            content = response.text
            if source.pull_url.lower().endswith(".csv"):
                indicators = IndicatorParser.parse_csv(content)
            else:
                indicators = IndicatorParser.parse_txt(content)

            ingested = 0
            if indicators:
                res = await IngestionService.ingest_bulk(db, source.id, indicators)
                ingested = res.ingested

            source.last_pull_status = f"success: {ingested} New"
            source.last_pull_at = datetime.now(timezone.utc)
            source.last_pull_error = None
            
            await db.commit()
            return {"message": "Feed successfully pulled and ingested", "ingested": ingested}
            
        except httpx.HTTPError as he:
            source.last_pull_at = datetime.now(timezone.utc)
            source.last_pull_status = "connection_failed"
            source.last_pull_error = str(he)
            await db.commit()
            raise HTTPException(status_code=502, detail=f"HTTP Error pulling feed: {str(he)}")

