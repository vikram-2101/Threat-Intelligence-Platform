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
