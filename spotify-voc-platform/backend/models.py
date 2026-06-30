"""
SQLAlchemy ORM models for the Spotify VoC Platform.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
)
from sqlalchemy.sql import func

from database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False, index=True)
    text_original = Column(Text, nullable=False)
    text_clean = Column(Text)
    title = Column(Text)
    author = Column(String)
    rating = Column(Float)
    score = Column(Integer)
    sentiment = Column(String, index=True)
    date = Column(DateTime, index=True)
    url = Column(Text)
    country = Column(String)
    language = Column(String, default="en")
    quality_score = Column(Integer)
    relevance = Column(String)
    metadata_ = Column("metadata", JSON)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_analyzed_at = Column(DateTime, nullable=True, index=True)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    reviews_found = Column(Integer, default=0)
    reviews_new = Column(Integer, default=0)
    errors = Column(JSON, default=[])
    runtime_seconds = Column(Float)
    config_snapshot = Column(JSON)
    progress_current = Column(Integer, default=0)
    progress_total = Column(Integer, default=0)
    progress_message = Column(String, default="")


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow = Column(String, nullable=False, index=True)
    title = Column(String)
    content = Column(JSON, nullable=False)
    sources_used = Column(JSON, default=[])
    review_count = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    ai_model = Column(String)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    workflows = Column(JSON, default=[])
    sources = Column(JSON, default=[])
    review_count = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    status = Column(String, default="completed")
    created_at = Column(DateTime, server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
