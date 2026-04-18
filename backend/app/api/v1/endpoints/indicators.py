import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.indicator import IngestionResponse
from app.services.ingestion_service import IngestionService
from app.services.parser import IndicatorParser

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_indicators(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Main ingestion gateway. Supports JSON, CSV, and TXT payloads.
    
    - For JSON: Content-Type: application/json
    - For Files: Content-Type: multipart/form-data (requires 'source_id' and 'file' fields)
    """
    content_type = request.headers.get("Content-Type", "")
    source_id = None
    raw_indicators = []

    try:
        # Handle JSON payload
        if "application/json" in content_type:
            data = await request.json()
            source_id = uuid.UUID(data["source_id"])
            raw_indicators = [(ind["type"], ind["value"]) for ind in data.get("indicators", [])]
        
        # Handle File Upload (CSV/TXT)
        elif "multipart/form-data" in content_type:
            form = await request.form()
            s_id_str = form.get("source_id")
            if not s_id_str:
                raise HTTPException(status_code=400, detail="source_id is required in form data")
            
            source_id = uuid.UUID(str(s_id_str))
            file = form.get("file")
            
            if file and isinstance(file, UploadFile):
                content = (await file.read()).decode("utf-8")
                if file.filename and file.filename.lower().endswith(".csv"):
                    raw_indicators = IndicatorParser.parse_csv(content)
                else:
                    raw_indicators = IndicatorParser.parse_txt(content)
            else:
                raise HTTPException(status_code=400, detail="File is required in multipart request")
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported content type: {content_type}. Use application/json or multipart/form-data."
            )

    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload format: {str(e)}")

    if not source_id:
        raise HTTPException(status_code=400, detail="source_id not found in request")
    
    if not raw_indicators:
        raise HTTPException(status_code=400, detail="No indicators found in request")

    return await IngestionService.ingest_bulk(db, source_id, raw_indicators)
