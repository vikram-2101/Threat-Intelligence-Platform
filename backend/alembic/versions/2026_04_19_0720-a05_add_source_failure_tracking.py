"""add source failure tracking

Revision ID: a05
Revises: a04
Create Date: 2026-04-19 07:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a05'
down_revision = 'a04'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('sources', sa.Column('last_pull_error', sa.Text(), nullable=True))
    op.add_column('sources', sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    op.drop_column('sources', 'consecutive_failures')
    op.drop_column('sources', 'last_pull_error')
