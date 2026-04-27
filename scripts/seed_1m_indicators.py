import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add the backend app to path if script is run contextually
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.indicator import Indicator, IndicatorType, IndicatorStatus
from app.models.source import Source

# Construct DB URL using psycopg adapter natively preventing asyncpg loops
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_size=10, max_overflow=20)
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def pre_seed_source():
    async with AsyncSessionFactory() as session:
        mock_source = Source(id=uuid.uuid4(), name="Load_Test_Source", type="OSINT", reliability=80, url="http://locust.example.com", description="Mocker")
        session.add(mock_source)
        await session.commit()
        return mock_source.id

async def seed_indicators(total: int = 1_000_000, chunk_size: int = 50_000):
    source_id = await pre_seed_source()
    print(f"Starting seeding of {total} indicators in chunks of {chunk_size}...")
    start_time = datetime.now()
    
    for i in range(0, total, chunk_size):
        chunk = []
        for j in range(chunk_size):
            chunk.append(
                Indicator(
                    id=uuid.uuid4(),
                    type=IndicatorType.IPV4,
                    value=f"10.{i//256}.{(i+j)%256}.{j%256}",
                    status=IndicatorStatus.ACTIVE,
                    current_confidence=85.00,
                    ttl=datetime.max.replace(tzinfo=timezone.utc)
                )
            )
        
        async with AsyncSessionFactory() as session:
            session.add_all(chunk)
            await session.commit()
            print(f"Committed {i + chunk_size}/{total} rows...")

    end_time = datetime.now()
    print(f"Success! Time taken: {end_time - start_time}")

if __name__ == "__main__":
    asyncio.run(seed_indicators())
