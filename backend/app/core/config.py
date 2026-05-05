from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Threat Intelligence Platform (TIP)"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    @field_validator("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="after")
    @classmethod
    def sanitize_redis_url(cls, v: str) -> str:
        """
        Fix for 'ValueError: A rediss:// URL must have parameter ssl_cert_reqs'
        Commonly encountered on managed Redis providers like Render.
        """
        if v and v.startswith("rediss://") and "ssl_cert_reqs" not in v:
            sep = "&" if "?" in v else "?"
            return f"{v}{sep}ssl_cert_reqs=none"
        return v

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # TIP Specifics
    DECAY_LAMBDA: float = 0.05
    AUTO_EXPIRE_THRESHOLD: float = 10.0

settings = Settings()
