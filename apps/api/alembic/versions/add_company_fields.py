"""Add company extended fields

Revision ID: add_company_fields
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_company_fields"
down_revision = "c982e1ac5b4f"
branch_labels = None
depends_on = None


def upgrade():
    """Add extended fields to companies table"""

    # Add new columns to companies table
    op.add_column(
        "companies",
        sa.Column("description", sa.Text(), nullable=True, comment="公司描述"),
    )
    op.add_column(
        "companies",
        sa.Column("website", sa.String(255), nullable=True, comment="公司網站"),
    )
    op.add_column(
        "companies",
        sa.Column("phone", sa.String(50), nullable=True, comment="聯絡電話"),
    )
    op.add_column(
        "companies",
        sa.Column("email", sa.String(255), nullable=True, comment="聯絡信箱"),
    )
    op.add_column(
        "companies", sa.Column("address", sa.Text(), nullable=True, comment="公司地址")
    )
    op.add_column(
        "companies",
        sa.Column("logo_url", sa.String(500), nullable=True, comment="公司 Logo URL"),
    )


def downgrade():
    """Remove extended fields from companies table"""

    # Remove added columns
    op.drop_column("companies", "logo_url")
    op.drop_column("companies", "address")
    op.drop_column("companies", "email")
    op.drop_column("companies", "phone")
    op.drop_column("companies", "website")
    op.drop_column("companies", "description")
