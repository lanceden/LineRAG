"""add plan A extended fields

Revision ID: add_plan_a_fields
Revises: add_lightrag_doc_id
Create Date: 2025-08-27 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_plan_a_fields"
down_revision: Union[str, Sequence[str], None] = "add_lightrag_doc_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增多模態狀態 / 內容雜湊 / 原始狀態 JSON
    op.add_column(
        "document_metadata",
        sa.Column("multimodal_processed", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "document_metadata",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "document_metadata", sa.Column("raw_status_json", sa.Text(), nullable=True)
    )
    # 索引
    op.create_index(
        "ix_document_metadata_content_hash", "document_metadata", ["content_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_document_metadata_content_hash", "document_metadata")
    op.drop_column("document_metadata", "raw_status_json")
    op.drop_column("document_metadata", "content_hash")
    op.drop_column("document_metadata", "multimodal_processed")
