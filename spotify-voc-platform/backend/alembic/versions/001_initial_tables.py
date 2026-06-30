"""Initial tables

Revision ID: 001
Revises: None
Create Date: 2025-06-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Scrape Runs (must be created before Reviews due to FK)
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("reviews_found", sa.Integer(), server_default="0"),
        sa.Column("reviews_new", sa.Integer(), server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("runtime_seconds", sa.Float(), nullable=True),
        sa.Column("config_snapshot", sa.JSON(), nullable=True),
        sa.Column("progress_current", sa.Integer(), server_default="0"),
        sa.Column("progress_total", sa.Integer(), server_default="0"),
        sa.Column("progress_message", sa.String(), server_default=""),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_scrape_runs_status", "scrape_runs", ["status"])

    # Reports (must be created before Insights due to FK)
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflows", sa.JSON(), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("date_range_start", sa.DateTime(), nullable=True),
        sa.Column("date_range_end", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), server_default="completed"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # Reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("text_original", sa.Text(), nullable=False),
        sa.Column("text_clean", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("sentiment", sa.String(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("language", sa.String(), server_default="en"),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("relevance", sa.String(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("scrape_run_id", sa.Integer(), sa.ForeignKey("scrape_runs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reviews_source", "reviews", ["source"])
    op.create_index("idx_reviews_date", "reviews", ["date"])
    op.create_index("idx_reviews_sentiment", "reviews", ["sentiment"])
    op.create_index("idx_reviews_rating", "reviews", ["rating"])
    op.create_index("idx_reviews_scrape_run", "reviews", ["scrape_run_id"])

    # Insights
    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("sources_used", sa.JSON(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("date_range_start", sa.DateTime(), nullable=True),
        sa.Column("date_range_end", sa.DateTime(), nullable=True),
        sa.Column("ai_model", sa.String(), nullable=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_insights_workflow", "insights", ["workflow"])
    op.create_index("idx_insights_report", "insights", ["report_id"])

    # Settings
    op.create_table(
        "settings",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("insights")
    op.drop_table("reviews")
    op.drop_table("reports")
    op.drop_table("scrape_runs")
