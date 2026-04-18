"""add source pull fields

Revision ID: a02
Revises: a01
Create Date: 2026-04-18 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a02'
down_revision = 'a01'
branch_labels = None
depends_on = None


def upgrade():
    # Add fields to sources table
    op.add_column('sources', sa.Column('last_pull_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sources', sa.Column('last_pull_status', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('sources', 'last_pull_status')
    op.drop_column('sources', 'last_pull_at')
