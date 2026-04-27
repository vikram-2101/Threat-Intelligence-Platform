from typing import AsyncGenerator, Annotated, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.schemas.user import TokenPayload
from app.models.user import User, Role, UserRole, RoleName

# auto_error=False → returns None instead of 401 when Authorization header is missing.
# This enables DEMO MODE: unauthenticated requests are served as the admin user.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(reusable_oauth2)]
) -> User:
    # ── DEMO MODE ────────────────────────────────────────────────────────────
    # When no Bearer token is present, return the seeded admin user so all
    # endpoints work without authentication for the presentation.
    # To restore: remove this block and change auto_error=False → True above.
    if not token:
        result = await db.execute(select(User).where(User.username == "admin"))
        demo_user = result.scalar_one_or_none()
        if demo_user:
            return demo_user
    # ─────────────────────────────────────────────────────────────────────────

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.username == token_data.sub))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[RoleName]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        result = await db.execute(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == current_user.id)
        )
        user_roles = result.scalars().all()

        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user


def require_roles(*roles: RoleName):
    allowed = list(roles)

    async def _inner(
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        result = await db.execute(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == current_user.id)
        )
        user_roles = result.scalars().all()

        if not any(role in allowed for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user

    return _inner
