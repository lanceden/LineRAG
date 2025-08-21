"""add lightrag_doc_id to document_metadata

Revision ID: add_lightrag_doc_id
Revises: c982e1ac5b4f
Create Date: 2025-08-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_lightrag_doc_id'
down_revision: Union[str, Sequence[str], None] = 'c982e1ac5b4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 lightrag_doc_id 欄位到 document_metadata 表
    op.add_column('document_metadata', 
                  sa.Column('lightrag_doc_id', sa.String(255), nullable=True))
    
    # 創建索引以提升查詢性能
    op.create_index('ix_document_metadata_lightrag_doc_id', 
                   'document_metadata', 
                   ['lightrag_doc_id'])


def downgrade() -> None:
    # 移除索引
    op.drop_index('ix_document_metadata_lightrag_doc_id', 'document_metadata')
    
    # 移除欄位
    op.drop_column('document_metadata', 'lightrag_doc_id')