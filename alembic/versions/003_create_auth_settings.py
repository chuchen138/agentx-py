"""create auth_settings table

Revision ID: 003
Revises: 002
Create Date: 2026-03-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # 创建 auth_settings 表
    op.create_table('auth_settings',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('feature_type', sa.String(length=32), nullable=False),
        sa.Column('feature_key', sa.String(length=64), nullable=False),
        sa.Column('feature_name', sa.String(length=128), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('config_data', sa.JSON(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key')
    )
    
    # 创建索引
    op.create_index('idx_auth_settings_feature_type', 'auth_settings', ['feature_type'])
    op.create_index('idx_auth_settings_feature_key', 'auth_settings', ['feature_key'], unique=True)
    
    # 插入初始数据
    op.execute("""
        INSERT INTO auth_settings (id, feature_type, feature_key, feature_name, enabled, config_data, display_order, description)
        VALUES 
        ('1', 'LOGIN', 'NORMAL_LOGIN', '普通登录', true, '{}', 1, '用户名密码登录'),
        ('2', 'LOGIN', 'GITHUB_LOGIN', 'GitHub登录', false, '{}', 2, 'GitHub OAuth 登录'),
        ('3', 'LOGIN', 'COMMUNITY_LOGIN', '敲鸭登录', false, '{}', 3, '社区认证登录'),
        ('4', 'REGISTER', 'USER_REGISTER', '用户注册', true, '{}', 1, '用户注册功能')
    """)

def downgrade():
    # 删除 auth_settings 表
    op.drop_index('idx_auth_settings_feature_key', table_name='auth_settings')
    op.drop_index('idx_auth_settings_feature_type', table_name='auth_settings')
    op.drop_table('auth_settings')
