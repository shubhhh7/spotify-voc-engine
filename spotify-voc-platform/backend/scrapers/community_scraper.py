"""
Community Forum Scraper Adapter
Scrapes Spotify Community forums + extra Reddit subreddits.
No API key required.
"""
import time
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScraperResult, ProgressCallback

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MIN_TEXT_LENGTH = 25

COMMUNITY_QUERIES = [
    "discover new music", "recommendation algorithm",
    "playlist stuck same songs", "bored with spotify",
    "discovery weekly bad", "radio repetitive",
    "shuffle algorithm", "can't find new music",
    "recommendations terrible", "daily mix same",
    "on repeat stuck", "algorithm broken",
]

EXTRA_SUBREDDITS = ["spotifytweaks", "spotifyplaylist", "musicproduction", "headphones"]
EXTRA_QUERIES = ["spotify discovery", "spotify recommendations", "spotify algorithm"]


def _fetch_spotify_community(query: str, max_pages: int = 2) -> list[dict]:
    """Search Spotify Community forum."""
    posts = []
    base_url = "https://community.spotify.com/t5/forums/searchpage/tab/message"

    for page in range(1, max_pages + 1):
        params = {"q": query, "page": page, "scope": "community", "search_type": "thread"}
        try:
            resp = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "html.parser")

            containers = (
                soup.find_all("div", class_=re.compile("lia-message"))
                or soup.find_all("div", class_=re.compile("MessageView"))
                or soup.find_all("tr", class_=re.compile("lia-data-row"))
            )

            for container in containers:
                try:
                    title_elem = container.find("a", class_=re.compile("lia-message-subject")) or \
                                 container.find("a", class_=re.compile("subject"))
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    text_elem = container.find("div", class_=re.compile("lia-message-body")) or \
                                container.find("div", class_=re.compile("body"))
                    text = text_elem.get_text(strip=True) if text_elem else ""

                    if len(text) < MIN_TEXT_LENGTH:
                        continue

                    url = ""
                    if title_elem and title_elem.get("href"):
                        href = title_elem.get("href")
                        url = href if href.startswith("http") else f"https://community.spotify.com{href}"

                    author_elem = container.find("a", class_=re.compile("lia-user-name"))
                    author = author_elem.get_text(strip=True) if author_elem else "anonymous"

                    posts.append({
                        "id": f"spotify_community_{len(posts)}_{hash(text[:50]) % 10000}",
                        "source": "spotify_community",
                        "title": title,
                        "text": text,
                        "author": author,
                        "created_utc": datetime.now().isoformat(),
                        "score": 0,
                        "num_comments": 0,
                        "url": url,
                        "type": "post",
                    })
                except Exception:
                    continue

            if not containers:
                break
            time.sleep(2)
        except Exception:
            break

    return posts


def _fetch_reddit_extra() -> list[dict]:
    """Fetch from supplementary Reddit subreddits."""
    posts = []
    for subreddit in EXTRA_SUBREDDITS:
        for query in EXTRA_QUERIES:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {"q": query, "sort": "relevance", "t": "year", "limit": 25, "restrict_sr": "on"}
                resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if "data" in data and "children" in data["data"]:
                    for child in data["data"]["children"]:
                        post = child["data"]
                        if post.get("num_comments", 0) < 3:
                            continue
                        created = post.get("created_utc", 0)
                        try:
                            created_str = datetime.fromtimestamp(int(created)).isoformat()
                        except (ValueError, TypeError, OSError):
                            created_str = ""
                        posts.append({
                            "id": f"reddit_community_{post['id']}",
                            "source": "spotify_community",
                            "title": post.get("title", ""),
                            "text": post.get("selftext", ""),
                            "author": post.get("author", "[deleted]"),
                            "created_utc": created_str,
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "type": "post",
                        })
                time.sleep(1.5)
            except Exception:
                continue
    return posts


class CommunityScraper(BaseScraper):
    name = "Spotify Community"
    source = "spotify_community"

    def validate_config(self) -> tuple[bool, str]:
        try:
            from bs4 import BeautifulSoup  # noqa: F401
            return True, "beautifulsoup4 installed"
        except ImportError:
            return False, "beautifulsoup4 not installed"

    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        start = time.time()
        all_posts = []
        errors = []
        queries_to_use = COMMUNITY_QUERIES[:8]  # Use subset for speed
        total = len(queries_to_use) + 1  # +1 for reddit extra

        # Spotify Community Forum
        for i, query in enumerate(queries_to_use):
            if progress_callback:
                progress_callback(i + 1, total, f"Community: '{query}'")
            try:
                posts = _fetch_spotify_community(query, max_pages=2)
                all_posts.extend(posts)
            except Exception as e:
                errors.append(f"Community '{query}': {str(e)}")
            time.sleep(3)

        # Extra Reddit
        if progress_callback:
            progress_callback(total, total, "Extra Reddit subreddits...")
        try:
            extra = _fetch_reddit_extra()
            all_posts.extend(extra)
        except Exception as e:
            errors.append(f"Reddit extra: {str(e)}")

        # Deduplicate
        seen = set()
        unique = []
        for post in all_posts:
            if post["id"] not in seen:
                seen.add(post["id"])
                unique.append(post)

        return ScraperResult(
            status="completed" if unique else "failed",
            reviews=unique,
            errors=errors,
            runtime_seconds=time.time() - start,
        )
