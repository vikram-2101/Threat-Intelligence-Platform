"""initial schema

Revision ID: a01
Revises: 
Create Date: 2026-04-18 14:14:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enums
    op.execute("CREATE TYPE source_category AS ENUM ('community', 'research', 'commercial', 'internal')")
    op.execute("CREATE TYPE trust_tier AS ENUM ('LOW', 'MEDIUM', 'HIGH')")
    op.execute("CREATE TYPE indicator_type AS ENUM ('IPV4', 'IPV6', 'DOMAIN', 'URL', 'MD5', 'SHA1', 'SHA256')")
    op.execute("CREATE TYPE indicator_status AS ENUM ('ACTIVE', 'EXPIRED', 'REVOKED')")
    op.execute("CREATE TYPE evidence_type AS ENUM ('WHOIS', 'PASSIVE_DNS', 'ASN', 'SSL_CERT', 'CORRELATION_INFRA', 'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING', 'ANALYST_NOTE', 'ANALYST_ADJUSTMENT', 'REVOCATION')")
    op.execute("CREATE TYPE role_name AS ENUM ('ADMIN', 'ANALYST', 'API_CONSUMER')")

    # Tables
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', postgresql.ENUM('ADMIN', 'ANALYST', 'API_CONSUMER', name='role_name', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uix_user_role')
    )

    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', postgresql.ENUM('community', 'research', 'commercial', 'internal', name='source_category', create_type=False), nullable=False),
        sa.Column('trust_tier', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='trust_tier', create_type=False), nullable=False),
        sa.Column('default_weight', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('intent_description', sa.Text(), nullable=True),
        sa.Column('pull_url', sa.String(length=2048), nullable=True),
        sa.Column('pull_schedule', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Indicators table with fillfactor=70
    op.create_table(
        'indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('IPV4', 'IPV6', 'DOMAIN', 'URL', 'MD5', 'SHA1', 'SHA256', name='indicator_type', create_type=False), nullable=False),
        sa.Column('value', sa.String(length=2048), nullable=False),
        sa.Column('first_seen', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ttl', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'EXPIRED', 'REVOKED', name='indicator_status', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('current_confidence', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type', 'value', name='uix_indicator_type_value')
    )

    # Hash constraints
    op.create_check_constraint(
        'chk_hash_length',
        'indicators',
        sa.text("(type = 'MD5' AND length(value) = 32) OR (type = 'SHA1' AND length(value) = 40) OR (type = 'SHA256' AND length(value) = 64) OR (type NOT IN ('MD5', 'SHA1', 'SHA256'))")
    )
    op.create_check_constraint(
        'chk_hash_hex',
        'indicators',
        sa.text("(type NOT IN ('MD5', 'SHA1', 'SHA256')) OR (value ~ '^[a-f0-9]+$')")
    )

    op.create_table(
        'indicator_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_reported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_reported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('indicator_id', 'source_id', name='uix_indicator_source')
    )

    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_type', postgresql.ENUM('WHOIS', 'PASSIVE_DNS', 'ASN', 'SSL_CERT', 'CORRELATION_INFRA', 'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING', 'ANALYST_NOTE', 'ANALYST_ADJUSTMENT', 'REVOCATION', name='evidence_type', create_type=False), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('confidence_delta', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('reversible', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reversed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.ForeignKeyConstraint(['reversed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'confidence_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reason_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('trigger', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.execute("CREATE INDEX idx_indicators_status_confidence ON indicators (status, current_confidence DESC)")
    op.create_index('idx_indicators_type', 'indicators', ['type'])
    op.create_index('idx_indicators_last_seen', 'indicators', [sa.text('last_seen DESC')])

    op.create_index('idx_evidence_indicator_id', 'evidence', ['indicator_id'])
    op.create_index('idx_evidence_indicator_timestamp', 'evidence', ['indicator_id', sa.text('timestamp DESC')])
    op.create_index('idx_evidence_type', 'evidence', ['evidence_type'])
    
    op.create_index('idx_evidence_asn', 'evidence', ['raw_payload'], postgresql_using='gin', postgresql_where=sa.text("evidence_type = 'ASN'"))
    op.create_index('idx_evidence_ssl', 'evidence', ['raw_payload'], postgresql_using='gin', postgresql_where=sa.text("evidence_type = 'SSL_CERT'"))

    op.create_index('idx_snapshots_indicator_calculated', 'confidence_snapshots', ['indicator_id', sa.text('calculated_at DESC')])

    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id', sa.text('timestamp DESC')])

    # TODO Phase 4: add GIN index on details once audit viewer query patterns are known
    # op.create_index("idx_audit_details_gin", "audit_logs", ["details"], postgresql_using="gin")

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('confidence_snapshots')
    op.drop_table('evidence')
    op.drop_table('indicator_sources')
    op.drop_table('indicators')
    op.drop_table('sources')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')
    op.execute("DROP TYPE role_name")
    op.execute("DROP TYPE evidence_type")
    op.execute("DROP TYPE indicator_status")
    op.execute("DROP TYPE indicator_type")
    op.execute("DROP TYPE trust_tier")
    op.execute("DROP TYPE source_category")
