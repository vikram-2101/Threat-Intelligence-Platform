"""add ingestion evidence type

Revision ID: a04
Revises: a03
Create Date: 2026-04-18 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a04'
down_revision = 'a03'
branch_labels = None
depends_on = None

def upgrade():
    # PostgreSQL specific: ADD VALUE to existing Enum type
    # This cannot be run inside a transaction in some cases, 
    # but Alembic handles it if we use op.execute with autocommit behavior
    op.execute("COMMIT") # Ensure we are not in a transaction
    op.execute("ALTER TYPE evidence_type ADD VALUE 'INGESTION'")

def downgrade():
    # Note: Removing a value from an ENUM is complex in Postgres and usually not recommended 
    # without recreating the type and table or just leaving it.
    pass
