"""make audit log entity fields optional

Revision ID: a03
Revises: a02
Create Date: 2026-04-18 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a03'
down_revision = 'a02'
branch_labels = None
depends_on = None


def upgrade():
    # Make entity_type and entity_id nullable
    op.alter_column('audit_logs', 'entity_type',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('audit_logs', 'entity_id',
               existing_type=postgresql.UUID(),
               nullable=True)


def downgrade():
    op.alter_column('audit_logs', 'entity_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.alter_column('audit_logs', 'entity_type',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
