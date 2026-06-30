"""
Dashboard endpoints — stats, trends, distributions.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from models import Review, ScrapeRun, Insight
from schemas import DashboardStats

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Review).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    reviews_today = db.query(Review).filter(Review.created_at >= today_start).count()

    sources_connected = db.query(Review.source).distinct().count()

    last_run = (
        db.query(ScrapeRun)
        .filter(ScrapeRun.status == "completed")
        .order_by(ScrapeRun.completed_at.desc())
        .first()
    )

    last_insight = (
        db.query(Insight)
        .order_by(Insight.created_at.desc())
        .first()
    )

    return DashboardStats(
        total_reviews=total,
        reviews_today=reviews_today,
        sources_connected=sources_connected,
        total_sources=5,
        last_scrape=last_run.completed_at if last_run else None,
        last_insight_run=last_insight.created_at if last_insight else None,
    )


@router.get("/trend")
def get_trend(days: int = 30, db: Session = Depends(get_db)):
    """Reviews per day for the last N days."""
    start_date = datetime.utcnow() - timedelta(days=days)

    results = (
        db.query(
            func.date(Review.created_at).label("day"),
            func.count(Review.id).label("count"),
        )
        .filter(Review.created_at >= start_date)
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
        .all()
    )

    return [{"date": str(r.day), "count": r.count} for r in results]


@router.get("/sources")
def get_source_distribution(db: Session = Depends(get_db)):
    """Review count per source."""
    results = (
        db.query(Review.source, func.count(Review.id).label("count"))
        .group_by(Review.source)
        .order_by(func.count(Review.id).desc())
        .all()
    )
    return [{"source": r.source, "count": r.count} for r in results]


@router.get("/sentiment")
def get_sentiment_distribution(db: Session = Depends(get_db)):
    """Sentiment breakdown."""
    results = (
        db.query(Review.sentiment, func.count(Review.id).label("count"))
        .filter(Review.sentiment.isnot(None))
        .group_by(Review.sentiment)
        .all()
    )
    return [{"sentiment": r.sentiment, "count": r.count} for r in results]


@router.get("/activity")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Recent scrape runs and insights."""
    runs = (
        db.query(ScrapeRun)
        .order_by(ScrapeRun.started_at.desc())
        .limit(limit)
        .all()
    )

    activities = []
    for run in runs:
        activities.append({
            "type": "scrape",
            "message": f"Scraped {run.source} — {run.reviews_new} new reviews",
            "status": run.status,
            "timestamp": run.completed_at or run.started_at,
        })

    insights = (
        db.query(Insight)
        .order_by(Insight.created_at.desc())
        .limit(5)
        .all()
    )

    for insight in insights:
        activities.append({
            "type": "insight",
            "message": f"Generated {insight.workflow} insight",
            "status": "completed",
            "timestamp": insight.created_at,
        })

    # Sort by timestamp descending
    activities.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)
    return activities[:limit]
