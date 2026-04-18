import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.api.deps import get_db
from app.db.base import Base
from app.core.config import settings
from unittest.mock import patch
import fakeredis.aioredis

# Test Database Configuration
# We use the same DB but with a schema/transaction isolated per test
TEST_DATABASE_URL = settings.DATABASE_URL # Normally we'd use a different name, but for this dev env we use transactions

test_engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Setup: Create all tables for tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Teardown: Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        # Start a transaction
        await session.begin()
        yield session
        # Rollback everything after the test to keep isolation
        await session.rollback()

@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def mock_redis():
    """
    Mocks the Redis client using fakeredis for PUBSUB verification.
    """
    from app.core.redis import redis_manager
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch.object(redis_manager, "client", fake):
        yield fake

@pytest_asyncio.fixture
async def admin_token_headers() -> dict:
    """
    Provides valid JWT headers for an admin user.
    Since we are testing the API layer, we can either mock the auth 
    dependency or provide a real token for a test admin.
    For integration tests, providing a real token is more comprehensive.
    """
    from app.core.security import create_access_token
    # We'll use a hardcoded admin username for tests
    access_token = create_access_token(data={"sub": "admin"})
    return {"Authorization": f"Bearer {access_token}"}
