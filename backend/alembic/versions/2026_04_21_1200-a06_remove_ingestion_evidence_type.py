"""remove INGESTION evidence type (spec deviation)

Revision ID: a06
Revises: a05
Create Date: 2026-04-21 12:00:00.000000

INGESTION was added as a workaround but is not in Agent.md spec.
Indicators start at current_confidence=0 and score only after enrichment.
This migration:
  1. Deletes all INGESTION evidence rows (stale / polluting test state)
  2. Removes INGESTION from the evidence_type PostgreSQL enum
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a06'
down_revision = 'a05'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM evidence WHERE evidence_type::text = 'INGESTION'")
    op.execute("""
        UPDATE indicators
        SET current_confidence = 0
        WHERE id NOT IN (
            SELECT DISTINCT indicator_id FROM evidence
        )
    """)

    # Drop partial indexes on evidence_type before mutating the type
    op.execute("DROP INDEX IF EXISTS idx_evidence_asn")
    op.execute("DROP INDEX IF EXISTS idx_evidence_ssl")

    op.execute("ALTER TYPE evidence_type RENAME TO evidence_type_old")
    op.execute("""
        CREATE TYPE evidence_type AS ENUM (
            'WHOIS', 'PASSIVE_DNS', 'ASN', 'SSL_CERT', 'CORRELATION_INFRA',
            'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING', 'ANALYST_NOTE',
            'ANALYST_ADJUSTMENT', 'REVOCATION'
        )
    """)
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE evidence_type
            USING evidence_type::text::evidence_type
    """)
    op.execute("DROP TYPE evidence_type_old")

    # Recreate partial indexes
    op.execute("CREATE INDEX idx_evidence_asn ON evidence USING GIN(raw_payload) WHERE evidence_type = 'ASN'")
    op.execute("CREATE INDEX idx_evidence_ssl ON evidence USING GIN(raw_payload) WHERE evidence_type = 'SSL_CERT'")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_evidence_asn")
    op.execute("DROP INDEX IF EXISTS idx_evidence_ssl")

    op.execute("ALTER TYPE evidence_type RENAME TO evidence_type_old")
    op.execute("""
        CREATE TYPE evidence_type AS ENUM (
            'WHOIS', 'PASSIVE_DNS', 'ASN', 'SSL_CERT', 'CORRELATION_INFRA',
            'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING', 'ANALYST_NOTE',
            'ANALYST_ADJUSTMENT', 'REVOCATION', 'INGESTION'
        )
    """)
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE evidence_type
            USING evidence_type::text::evidence_type
    """)
    op.execute("DROP TYPE evidence_type_old")

    op.execute("CREATE INDEX idx_evidence_asn ON evidence USING GIN(raw_payload) WHERE evidence_type = 'ASN'")
    op.execute("CREATE INDEX idx_evidence_ssl ON evidence USING GIN(raw_payload) WHERE evidence_type = 'SSL_CERT'")


