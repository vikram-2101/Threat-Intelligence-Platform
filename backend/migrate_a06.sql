-- Step 1: Delete all INGESTION evidence rows
DELETE FROM evidence WHERE evidence_type::text = 'INGESTION';

-- Step 2: Reset confidence for indicators with no remaining evidence
UPDATE indicators
SET current_confidence = 0
WHERE id NOT IN (SELECT DISTINCT indicator_id FROM evidence);

-- Step 3a: Cast the evidence_type column to plain TEXT (breaks enum dependency)
ALTER TABLE evidence ALTER COLUMN evidence_type TYPE TEXT USING evidence_type::TEXT;

-- Step 3b: Drop the old enum type
DROP TYPE evidence_type;

-- Step 3c: Recreate enum WITHOUT INGESTION
CREATE TYPE evidence_type AS ENUM (
    'WHOIS',
    'PASSIVE_DNS',
    'ASN',
    'SSL_CERT',
    'CORRELATION_INFRA',
    'CORRELATION_SSL',
    'MULTI_SOURCE_SIGHTING',
    'ANALYST_NOTE',
    'ANALYST_ADJUSTMENT',
    'REVOCATION'
);

-- Step 3d: Cast the column back to the new enum
ALTER TABLE evidence ALTER COLUMN evidence_type TYPE evidence_type USING evidence_type::evidence_type;

-- Step 4: Mark migration as applied in alembic_version table
INSERT INTO alembic_version (version_num) VALUES ('a06')
ON CONFLICT (version_num) DO NOTHING;

SELECT 'Migration a06 complete' AS status;
