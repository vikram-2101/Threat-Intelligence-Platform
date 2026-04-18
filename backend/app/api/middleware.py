import time
import uuid
from fastapi import Request
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.models.audit_log import AuditLog
from sqlalchemy import select
from app.models.user import User

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Execute the request first
        response = await call_next(request)
        
        # 2. Skip logging for noise endpoints (health, docs, etc.)
        if request.url.path in ["/health", "/", "/docs", "/openapi.json", "/favicon.ico"]:
            return response
            
        # 3. Attempt to log the activity
        try:
            await self.log_request(request, response)
        except Exception as e:
            # We fail silently to ensure the primary request is never blocked by audit issues
            # In production, we would log this error to a monitoring service (e.g., Sentry)
            pass
            
        return response

    async def log_request(self, request: Request, response):
        user_id = None
        auth_header = request.headers.get("Authorization")
        
        # Try to extract user_id from the JWT token if present
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
                )
                username = payload.get("sub")
                if username:
                    # We open a dedicated session for the audit log to avoid interfering 
                    # with the main request session
                    async with AsyncSessionLocal() as db:
                        res = await db.execute(select(User.id).where(User.username == username))
                        user_id = res.scalar_one_or_none()
            except:
                # Token might be invalid or expired, but we still log the attempt without user_id
                pass

        # Persist the audit log entry
        async with AsyncSessionLocal() as db:
            audit_log = AuditLog(
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                details={
                    "status_code": response.status_code,
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            )
            db.add(audit_log)
            await db.commit()
