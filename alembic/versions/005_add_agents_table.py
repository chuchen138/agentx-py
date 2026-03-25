"""Add agents table

Revision ID: 005
Revises: 004
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('tool_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('knowledge_base_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('tool_presets', sa.JSON(), nullable=True),
        sa.Column('multimodal_config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_user_id'), 'agents', ['user_id'], unique=False)

def downgrade() -> None:
    # Drop agents table
    op.drop_index(op.f('ix_agents_user_id'), table_name='agents')
    op.drop_table('agents')
