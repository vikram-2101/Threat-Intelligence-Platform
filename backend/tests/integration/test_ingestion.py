# import pytest
# import uuid
# import json
# from fastapi.testclient import TestClient
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.main import app
# from app.models.source import Source, SourceCategory, TrustTier
# from app.models.indicator import Indicator
# from app.core.config import settings

# client = TestClient(app)

# @pytest.mark.asyncio
# async def test_ingest_json_success(db_session: AsyncSession, admin_token_headers):
#     # 1. Create a source
#     source = Source(
#         name="Test API Source",
#         category=SourceCategory.community,
#         trust_tier=TrustTier.LOW,
#         default_weight=0.5
#     )
#     db_session.add(source)
#     await db_session.commit()
#     await db_session.refresh(source)

#     # 2. Ingest indicators via JSON
#     payload = {
#         "source_id": str(source.id),
#         "indicators": [
#             {"type": "IPV4", "value": "1.2.3.4"},
#             {"type": "DOMAIN", "value": "malicious[.]com"},
#             {"type": "URL", "value": "hxxp://evil.com/payload"}
#         ]
#     }
    
#     response = client.post(
#         "/api/v1/indicators/",
#         json=payload,
#         headers=admin_token_headers
#     )
    
#     assert response.status_code == 202
#     data = response.json()
#     assert data["ingested"] == 3
#     assert data["duplicates"] == 0
#     assert data["errors"] == 0

# @pytest.mark.asyncio
# async def test_ingest_csv_success(db_session: AsyncSession, admin_token_headers):
#     # 1. Setup Source
#     source = Source(
#         name="Test CSV Source",
#         category=SourceCategory.research,
#         trust_tier=TrustTier.HIGH,
#         default_weight=1.0
#     )
#     db_session.add(source)
#     await db_session.commit()
#     await db_session.refresh(source)

#     # 2. Upload CSV
#     csv_content = "IPV4,8.8.8.8\nDOMAIN,google.com\n"
#     files = {
#         "file": ("test.csv", csv_content, "text/csv")
#     }
#     data = {"source_id": str(source.id)}
    
#     response = client.post(
#         "/api/v1/indicators/",
#         data=data,
#         files=files,
#         headers=admin_token_headers
#     )
    
#     assert response.status_code == 202
#     res_data = response.json()
#     assert res_data["ingested"] == 2

# @pytest.mark.asyncio
# async def test_ingest_normalization(db_session: AsyncSession, admin_token_headers):
#     # 1. Setup Source
#     source = Source(
#         name="Normalization Source",
#         category=SourceCategory.internal,
#         trust_tier=TrustTier.HIGH,
#         default_weight=1.0
#     )
#     db_session.add(source)
#     await db_session.commit()
#     await db_session.refresh(source)

#     # 2. Ingest duplicate with different formatting
#     # First ingestion
#     client.post(
#         "/api/v1/indicators/",
#         json={"source_id": str(source.id), "indicators": [{"type": "DOMAIN", "value": "EVIL.com"}]},
#         headers=admin_token_headers
#     )
    
#     # Second ingestion (should be duplicate)
#     response = client.post(
#         "/api/v1/indicators/",
#         json={"source_id": str(source.id), "indicators": [{"type": "DOMAIN", "value": "evil.com"}]},
#         headers=admin_token_headers
#     )
    
#     data = response.json()
#     assert data["duplicates"] == 1
#     assert data["ingested"] == 0
