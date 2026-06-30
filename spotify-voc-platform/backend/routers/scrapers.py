"""
Scraper endpoints — list, run, status, history, logs.
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import ScrapeRun, Review
from schemas import RunScrapersRequest, ScraperStatus, ScraperInfo
from services.scraper_service import (
    SCRAPER_REGISTRY,
    execute_scrapers,
    scrape_state,
)

router = APIRouter(prefix="/api/v1/scrapers", tags=["scrapers"])


@router.get("")
def list_scrapers(db: Session = Depends(get_db)):
    """List all available scrapers with their last run info."""
    scrapers = []
    for source, scraper_cls in SCRAPER_REGISTRY.items():
        scraper = scraper_cls()

        # Get last completed run for this source
        last_run = (
            db.query(ScrapeRun)
            .filter(ScrapeRun.source.contains(source))
            .filter(ScrapeRun.status == "completed")
            .order_by(ScrapeRun.completed_at.desc())
            .first()
        )

        # Total reviews from this source
        total_reviews = db.query(Review).filter(Review.source == source).count()

        # Check if currently running
        is_running = (
            scrape_state.status == "running"
            and source in scrape_state.sources
        )

        scrapers.append(ScraperInfo(
            name=scraper.name,
            source=source,
            status="running" if is_running else "ready",
            last_run=last_run.completed_at if last_run else None,
            reviews_collected=total_reviews,
            runtime_seconds=last_run.runtime_seconds if last_run else None,
        ))
    return scrapers


@router.post("/run")
def run_scrapers(
    request: RunScrapersRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start scraping selected sources in background."""
    if scrape_state.status == "running":
        return {"error": "A scrape is already running", "status": "busy"}

    # Validate sources
    invalid = [s for s in request.sources if s not in SCRAPER_REGISTRY]
    if invalid:
        return {"error": f"Unknown sources: {invalid}", "status": "error"}

    # Reset state from any previous completed/failed run
    scrape_state.reset()

    # Create scrape run record
    run = ScrapeRun(
        source=",".join(request.sources),
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Launch background execution
    background_tasks.add_task(execute_scrapers, run.id, request.sources)

    return {"run_id": run.id, "status": "started", "sources": request.sources}


@router.get("/status")
def get_status():
    """Get current scrape run progress (polled by frontend)."""
    return ScraperStatus(**scrape_state.to_dict())


@router.get("/logs")
def get_logs():
    """Get live logs from current/last run."""
    return {"logs": scrape_state.logs}


@router.get("/history")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """Get past scrape runs."""
    runs = (
        db.query(ScrapeRun)
        .order_by(ScrapeRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "source": r.source,
            "status": r.status,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "reviews_found": r.reviews_found,
            "reviews_new": r.reviews_new,
            "runtime_seconds": r.runtime_seconds,
        }
        for r in runs
    ]


@router.post("/stop")
def stop_scraper():
    """Request cancellation of current run."""
    if scrape_state.status != "running":
        return {"status": "not_running"}
    # Simple cancellation via state flag (scrapers check this)
    scrape_state.status = "cancelled"
    scrape_state.log("⚠️ Cancellation requested")
    return {"status": "cancelling"}
