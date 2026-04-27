from datetime import timedelta
import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User, RoleName
from app.schemas.user import Token, ApiKeyCreate, ApiKeyResponse
from app.models.api_key import ApiKey
from app.core.limiter import limiter

router = APIRouter()

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login_access_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # 1. Fetch user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # 2. Validate user and password
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # 3. Generate JWT access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.username, expires_delta=access_token_expires
        ),
        token_type="bearer",
    )

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_in: ApiKeyCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([RoleName.ADMIN]))
):
    user_res = await db.execute(select(User).where(User.id == api_key_in.user_id))
    if not user_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target user not found")
        
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
    new_key = ApiKey(
        user_id=api_key_in.user_id,
        key=raw_key,
        name=api_key_in.name,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    return new_key

@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([RoleName.ADMIN]))
):
    res = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = res.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
        
    await db.delete(api_key)
    await db.commit()
