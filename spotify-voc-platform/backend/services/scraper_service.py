"""
Scraper Service — orchestrates scraper execution, stores results in DB.
"""
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import ScrapeRun, Review
from scrapers.base import BaseScraper
from scrapers.reddit_scraper import RedditScraper
from scrapers.appstore_scraper import AppStoreScraper
from scrapers.playstore_scraper import PlayStoreScraper
from scrapers.community_scraper import CommunityScraper
from scrapers.social_scraper import SocialScraper
from services.cleaning_service import clean_reviews_for_run


# Registry: maps source key → scraper class
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "reddit": RedditScraper,
    "app_store": AppStoreScraper,
    "play_store": PlayStoreScraper,
    "spotify_community": CommunityScraper,
    "social": SocialScraper,
}


# Global state for current scrape run (single-user tool, no need for Redis)
class ScrapeState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.run_id: int = 0
        self.status: str = "idle"
        self.sources: list[str] = []
        self.progress_current: int = 0
        self.progress_total: int = 0
        self.current_source = None
        self.current_message = None
        self.reviews_collected: int = 0
        self.logs: list[str] = []
        self._lock = threading.Lock()

    def log(self, message: str):
        with self._lock:
            self.logs.append(message)
            # Keep last 200 lines
            if len(self.logs) > 200:
                self.logs = self.logs[-200:]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "sources": self.sources,
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "current_source": self.current_source,
            "current_message": self.current_message,
            "reviews_collected": self.reviews_collected,
        }


scrape_state = ScrapeState()


def execute_scrapers(run_id: int, sources: list[str]):
    """
    Background task that runs scrapers sequentially and stores results.
    Called from the router's BackgroundTasks.
    """
    global scrape_state

    scrape_state.run_id = run_id
    scrape_state.status = "running"
    scrape_state.sources = sources
    scrape_state.progress_total = len(sources)
    scrape_state.progress_current = 0
    scrape_state.reviews_collected = 0
    scrape_state.logs = [f"▶ Starting scrape run #{run_id}"]
    scrape_state.logs.append(f"  Sources: {', '.join(sources)}")

    # Use a fresh DB session for the background task
    db = SessionLocal()
    run_start = time.time()

    try:
        total_new = 0

        for i, source in enumerate(sources):
            scrape_state.progress_current = i
            scrape_state.current_source = source

            scraper_cls = SCRAPER_REGISTRY.get(source)
            if not scraper_cls:
                scrape_state.log(f"❌ Unknown source: {source}")
                continue

            scraper = scraper_cls()
            scrape_state.log(f"\n▶ Starting {scraper.name}...")

            # Validate
            valid, msg = scraper.validate_config()
            if not valid:
                scrape_state.log(f"  ⚠️ {scraper.name} skipped: {msg}")
                continue

            # Progress callback
            def progress_cb(current, total, message):
                scrape_state.current_message = f"{scraper.name}: {message}"
                scrape_state.log(f"  [{current}/{total}] {message}")

            # Execute
            start_time = time.time()
            try:
                result = scraper.run(progress_callback=progress_cb)
            except Exception as e:
                scrape_state.log(f"  ❌ {scraper.name} crashed: {str(e)}")
                continue
            elapsed = time.time() - start_time

            # Store reviews in DB (deduplicate by ID)
            new_count = 0
            for review_data in result.reviews:
                review_id = review_data.get("id", "")
                if not review_id:
                    continue

                existing = db.query(Review).filter(Review.id == review_id).first()
                if existing:
                    continue

                # Parse date
                date_val = review_data.get("created_utc") or review_data.get("date")
                parsed_date = None
                if date_val:
                    try:
                        if isinstance(date_val, str) and date_val:
                            parsed_date = datetime.fromisoformat(
                                date_val.replace("Z", "+00:00")
                            )
                    except (ValueError, TypeError):
                        parsed_date = None

                review = Review(
                    id=review_id,
                    source=review_data.get("source", source),
                    text_original=review_data.get("text", "") or review_data.get("title", ""),
                    title=review_data.get("title"),
                    author=review_data.get("author"),
                    rating=review_data.get("rating"),
                    score=review_data.get("score"),
                    date=parsed_date,
                    url=review_data.get("url"),
                    country=review_data.get("country"),
                    scrape_run_id=run_id,
                )
                db.add(review)
                new_count += 1

            db.commit()
            total_new += new_count
            scrape_state.reviews_collected = total_new

            scrape_state.log(
                f"  ✅ {scraper.name}: {len(result.reviews)} found, "
                f"{new_count} new stored ({elapsed:.1f}s)"
            )

            if result.errors:
                for err in result.errors[:3]:
                    scrape_state.log(f"  ⚠️ {err}")

        # Clean reviews (text normalization, sentiment, quality score)
        scrape_state.log("\n🧹 Cleaning reviews...")
        scrape_state.current_message = "Cleaning & classifying reviews..."
        cleaned_count = clean_reviews_for_run(db, run_id)
        scrape_state.log(f"  ✅ Cleaned {cleaned_count} reviews")

        # Update the scrape run record
        run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
        if run:
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.reviews_found = scrape_state.reviews_collected
            run.reviews_new = total_new
            run.runtime_seconds = time.time() - run_start
            db.commit()

        scrape_state.progress_current = len(sources)
        scrape_state.status = "completed"
        scrape_state.current_message = f"All complete — {total_new} new reviews"
        scrape_state.log(f"\n✅ Scrape run #{run_id} complete: {total_new} new reviews stored")

    except Exception as e:
        scrape_state.status = "failed"
        scrape_state.log(f"\n❌ Fatal error: {str(e)}")

        run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.errors = [str(e)]
            run.runtime_seconds = time.time() - run_start
            db.commit()
    finally:
        db.close()
