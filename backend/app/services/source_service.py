import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate

class SourceService:
    @staticmethod
    async def create_source(db: AsyncSession, source_in: SourceCreate) -> Source:
        source = Source(**source_in.model_dump())
        db.add(source)
        try:
            await db.commit()
            await db.refresh(source)
            return source
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Source with name '{source.name}' already exists"
            )

    @staticmethod
    async def get_source(db: AsyncSession, source_id: uuid.UUID) -> Optional[Source]:
        result = await db.execute(select(Source).where(Source.id == source_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_sources(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Source]:
        result = await db.execute(select(Source).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_source(db: AsyncSession, source_id: uuid.UUID, source_in: SourceUpdate) -> Optional[Source]:
        source = await SourceService.get_source(db, source_id)
        if not source:
            return None
        
        update_data = source_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)
            
        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def delete_source(db: AsyncSession, source_id: uuid.UUID) -> bool:
        source = await SourceService.get_source(db, source_id)
        if not source:
            return False
        
        await db.delete(source)
        await db.commit()
        return True
