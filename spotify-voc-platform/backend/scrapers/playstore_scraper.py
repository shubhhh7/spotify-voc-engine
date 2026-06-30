"""
Play Store Scraper Adapter
Uses the google-play-scraper library.
No API key required.
"""
import time
from scrapers.base import BaseScraper, ScraperResult, ProgressCallback

APP_ID = "com.spotify.music"
COUNTRIES = ["us", "gb"]
REVIEWS_PER_COUNTRY = 300
LANGUAGE = "en"


class PlayStoreScraper(BaseScraper):
    name = "Play Store"
    source = "play_store"

    def validate_config(self) -> tuple[bool, str]:
        try:
            from google_play_scraper import reviews  # noqa: F401
            return True, "google-play-scraper installed"
        except ImportError:
            return False, "google-play-scraper not installed. Run: pip install google-play-scraper"

    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        start = time.time()
        all_reviews = []
        errors = []
        total = len(COUNTRIES)

        try:
            from google_play_scraper import reviews, Sort
        except ImportError:
            return ScraperResult(
                status="failed",
                errors=["google-play-scraper not installed"],
                runtime_seconds=time.time() - start,
            )

        for i, country in enumerate(COUNTRIES):
            if progress_callback:
                progress_callback(i + 1, total, f"Fetching {country.upper()} Play Store...")

            try:
                result, _ = reviews(
                    APP_ID,
                    lang=LANGUAGE,
                    country=country,
                    sort=Sort.NEWEST,
                    count=REVIEWS_PER_COUNTRY,
                    filter_score_with=None,
                )

                for review in result:
                    date_val = review.get("at", "")
                    if hasattr(date_val, "isoformat"):
                        date_val = date_val.isoformat()

                    all_reviews.append({
                        "id": f"playstore_{country}_{review.get('reviewId', '')}",
                        "source": "play_store",
                        "title": "",
                        "text": review.get("content", ""),
                        "author": review.get("userName", "anonymous"),
                        "rating": review.get("score", 0),
                        "created_utc": str(date_val),
                        "score": review.get("thumbsUpCount", 0),
                        "country": country,
                        "version": review.get("reviewCreatedVersion", ""),
                        "url": "",
                        "type": "review",
                    })

            except Exception as e:
                errors.append(f"Play Store {country}: {str(e)}")

            time.sleep(3)

        return ScraperResult(
            status="completed" if all_reviews else "failed",
            reviews=all_reviews,
            errors=errors,
            runtime_seconds=time.time() - start,
        )
