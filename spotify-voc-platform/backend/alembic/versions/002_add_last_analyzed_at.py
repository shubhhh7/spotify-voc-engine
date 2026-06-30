"""Add last_analyzed_at column to reviews

Revision ID: 002
Revises: 001
Create Date: 2025-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reviews",
        sa.Column("last_analyzed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_reviews_last_analyzed_at", "reviews", ["last_analyzed_at"])


def downgrade() -> None:
    op.drop_index("idx_reviews_last_analyzed_at", table_name="reviews")
    op.drop_column("reviews", "last_analyzed_at")
