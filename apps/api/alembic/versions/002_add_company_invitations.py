"""Add company invitations table

Revision ID: 002_add_company_invitations
Revises: add_company_fields
Create Date: 2024-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_company_invitations'
down_revision = 'add_company_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Create company_invitations table"""
    
    op.create_table(
        'company_invitations',
        sa.Column('id', sa.String(36), primary_key=True, comment='邀請 ID'),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False, comment='公司 ID'),
        sa.Column('email', sa.String(255), nullable=False, comment='被邀請者郵箱'),
        sa.Column('name', sa.String(255), nullable=False, comment='被邀請者姓名'),
        sa.Column('role', sa.String(50), nullable=False, default='cs_agent', comment='角色'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, default=False, comment='是否已接受'),
        sa.Column('is_expired', sa.Boolean(), nullable=False, default=False, comment='是否已過期'),
        sa.Column('invited_by', sa.Integer(), sa.ForeignKey('system_users.id'), nullable=False, comment='邀請者 ID'),
        sa.Column('invited_at', sa.DateTime(), nullable=False, comment='邀請時間'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='過期時間'),
        sa.Column('accepted_at', sa.DateTime(), nullable=True, comment='接受時間'),
        sa.Column('message', sa.Text(), nullable=True, comment='邀請訊息'),
    )
    
    # 建立索引
    op.create_index('ix_company_invitations_company_id', 'company_invitations', ['company_id'])
    op.create_index('ix_company_invitations_email', 'company_invitations', ['email'])
    op.create_index('ix_company_invitations_invited_by', 'company_invitations', ['invited_by'])


def downgrade():
    """Drop company_invitations table"""
    
    op.drop_index('ix_company_invitations_invited_by', 'company_invitations')
    op.drop_index('ix_company_invitations_email', 'company_invitations')
    op.drop_index('ix_company_invitations_company_id', 'company_invitations')
    op.drop_table('company_invitations')
