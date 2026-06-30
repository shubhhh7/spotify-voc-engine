"""
App Store Scraper Adapter
Uses Apple's public iTunes RSS feed (most reliable method).
No API key or third-party library required.
"""
import time
import requests
from scrapers.base import BaseScraper, ScraperResult, ProgressCallback

APP_ID = "324684580"  # Spotify iOS
COUNTRIES = ["us", "gb", "au", "ca", "in"]
REVIEWS_PER_COUNTRY = 200
MAX_PAGES = 10  # iTunes RSS supports up to 10 pages (50 reviews each)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _fetch_rss_page(app_id: str, country: str, page: int) -> list[dict]:
    """
    Fetch a single page of reviews via iTunes RSS feed.
    Returns up to 50 reviews per page.
    """
    url = (
        f"https://itunes.apple.com/{country}/rss/customerreviews/"
        f"page={page}/id={app_id}/sortBy=mostRecent/json"
    )

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return []

        data = resp.json()
        entries = data.get("feed", {}).get("entry", [])

        reviews = []
        for entry in entries:
            # Skip app metadata entry (no rating field)
            if "im:rating" not in entry:
                continue

            review_id = entry.get("id", {}).get("label", "")
            title = entry.get("title", {}).get("label", "")
            text = entry.get("content", {}).get("label", "")
            rating = int(entry.get("im:rating", {}).get("label", "0"))
            author = entry.get("author", {}).get("name", {}).get("label", "anonymous")
            version = entry.get("im:version", {}).get("label", "")
            vote_count = int(entry.get("im:voteCount", {}).get("label", "0"))
            date_str = entry.get("updated", {}).get("label", "")

            reviews.append({
                "id": f"appstore_{country}_{review_id}",
                "source": "app_store",
                "title": title,
                "text": text,
                "author": author,
                "rating": rating,
                "created_utc": date_str,
                "score": vote_count,
                "country": country,
                "version": version,
                "url": "",
                "type": "review",
            })

        return reviews

    except Exception:
        return []


def _fetch_country_reviews(country: str, target: int) -> list[dict]:
    """Fetch multiple pages of RSS reviews for a single country."""
    all_reviews = []
    for page in range(1, MAX_PAGES + 1):
        reviews = _fetch_rss_page(APP_ID, country, page)
        if not reviews:
            break
        all_reviews.extend(reviews)
        if len(all_reviews) >= target:
            break
        time.sleep(0.5)
    return all_reviews[:target]


class AppStoreScraper(BaseScraper):
    name = "App Store"
    source = "app_store"

    def validate_config(self) -> tuple[bool, str]:
        # No dependencies needed — uses requests (already available)
        return True, "iTunes RSS feed (no extra dependencies)"

    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        start = time.time()
        all_reviews = []
        errors = []
        total = len(COUNTRIES)

        for i, country in enumerate(COUNTRIES):
            if progress_callback:
                progress_callback(i + 1, total, f"Fetching {country.upper()} App Store...")

            try:
                reviews = _fetch_country_reviews(country, REVIEWS_PER_COUNTRY)
                all_reviews.extend(reviews)
            except Exception as e:
                errors.append(f"App Store {country}: {str(e)}")

            time.sleep(1)

        return ScraperResult(
            status="completed" if all_reviews else "failed",
            reviews=all_reviews,
            errors=errors,
            runtime_seconds=time.time() - start,
        )
