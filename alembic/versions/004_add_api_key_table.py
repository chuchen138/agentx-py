"""Add API Key table

Revision ID: 004
Revises: 003
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_api_key'), 'api_keys', ['api_key'], unique=True)
    op.create_index(op.f('ix_api_keys_agent_id'), 'api_keys', ['agent_id'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)

def downgrade() -> None:
    # Drop api_keys table
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_agent_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_api_key'), table_name='api_keys')
    op.drop_table('api_keys')
