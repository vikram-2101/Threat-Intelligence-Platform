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
    # Step 1: Delete all INGESTION evidence rows. These are spec-non-compliant rows
    # that were polluting scores. Safe to remove — they were never real enrichment data.
    op.execute("DELETE FROM evidence WHERE evidence_type::text = 'INGESTION'")

    # Step 2: Reset current_confidence to 0 for any indicator with no remaining evidence.
    # These are un-enriched indicators whose score was driven by the now-deleted INGESTION rows.
    op.execute("""
        UPDATE indicators
        SET current_confidence = 0
        WHERE id NOT IN (
            SELECT DISTINCT indicator_id FROM evidence
        )
    """)

    # Step 3: Safe enum replacement in PostgreSQL —
    # (a) cast the column to TEXT (breaks the type dependency)
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE TEXT
            USING evidence_type::TEXT
    """)

    # (b) drop the old enum
    op.execute("DROP TYPE evidence_type")

    # (c) create the new enum without INGESTION
    op.execute("""
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
        )
    """)

    # (d) cast the column back to the new enum
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE evidence_type
            USING evidence_type::evidence_type
    """)


def downgrade():
    # Re-add INGESTION to the enum (for rollback only)
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE TEXT
            USING evidence_type::TEXT
    """)
    op.execute("DROP TYPE evidence_type")
    op.execute("""
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
            'REVOCATION',
            'INGESTION'
        )
    """)
    op.execute("""
        ALTER TABLE evidence
            ALTER COLUMN evidence_type TYPE evidence_type
            USING evidence_type::evidence_type
    """)
