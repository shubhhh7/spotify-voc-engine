"""
Reddit Scraper Adapter
Wraps the Reddit JSON API + PullPush fallback logic.
No API key required.
"""
import time
import requests
from datetime import datetime
from scrapers.base import BaseScraper, ScraperResult, ProgressCallback

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SUBREDDITS = [
    "spotify", "truespotify", "spotifywrapped",
    "WeAreTheMusicMakers", "music", "AppleMusic",
    "musicsuggestions", "spotifycommunity",
]

SEARCH_QUERIES = [
    "discover new music", "recommendation algorithm",
    "playlist stuck same songs", "bored with spotify",
    "discovery weekly bad", "radio repetitive",
    "shuffle algorithm", "can't find new music",
    "recommendations terrible", "daily mix same",
    "on repeat stuck", "algorithm broken",
    "new music discovery", "song repetition",
    "playlist rotation",
]

MIN_COMMENTS = 5
POST_LIMIT = 75
COMMENTS_PER_POST = 10


def _fetch_reddit_json(subreddit: str, query: str, limit: int = 75) -> list[dict]:
    """Fetch via Reddit's public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query, "sort": "relevance", "t": "year",
        "limit": limit, "restrict_sr": "on",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(30)
            return _fetch_reddit_json(subreddit, query, limit)
        if resp.status_code == 403:
            return _fetch_pullpush(subreddit, query, limit)
        resp.raise_for_status()
        data = resp.json()
        posts = []
        if "data" in data and "children" in data["data"]:
            for child in data["data"]["children"]:
                post = child["data"]
                if post.get("num_comments", 0) < MIN_COMMENTS:
                    continue
                posts.append({
                    "id": f"reddit_{post['id']}",
                    "source": "reddit",
                    "title": post.get("title", ""),
                    "text": post.get("selftext", ""),
                    "author": post.get("author", "[deleted]"),
                    "created_utc": datetime.fromtimestamp(
                        post.get("created_utc", 0)
                    ).isoformat(),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "type": "post",
                })
        return posts
    except Exception:
        return _fetch_pullpush(subreddit, query, limit)


def _fetch_pullpush(subreddit: str, query: str, limit: int = 75) -> list[dict]:
    """Fallback: PullPush API (successor to Pushshift)."""
    url = "https://api.pullpush.io/reddit/search/submission/"
    params = {
        "q": query, "subreddit": subreddit,
        "size": min(limit, 100), "sort": "desc", "sort_type": "score",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        posts = []
        if "data" in data:
            for post in data["data"]:
                if post.get("num_comments", 0) < MIN_COMMENTS:
                    continue
                created = post.get("created_utc", 0)
                try:
                    created_str = datetime.fromtimestamp(int(created)).isoformat()
                except (ValueError, TypeError, OSError):
                    created_str = ""
                posts.append({
                    "id": f"reddit_{post['id']}",
                    "source": "reddit",
                    "title": post.get("title", ""),
                    "text": post.get("selftext", ""),
                    "author": post.get("author", "[deleted]"),
                    "created_utc": created_str,
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "type": "post",
                })
        return posts
    except Exception:
        return []


def _fetch_comments(post_id: str, subreddit: str, max_comments: int = 10) -> list[dict]:
    """Fetch top comments for a post."""
    post_id_clean = post_id.replace("reddit_", "")
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id_clean}.json"
    try:
        resp = requests.get(url, headers=HEADERS, params={"limit": max_comments}, timeout=30)
        if resp.status_code in [429, 403]:
            return []
        resp.raise_for_status()
        data = resp.json()
        comments = []
        if len(data) > 1 and "data" in data[1] and "children" in data[1]["data"]:
            for child in data[1]["data"]["children"]:
                if child["kind"] != "t1":
                    continue
                comment = child["data"]
                body = comment.get("body", "")
                if len(body) < 25:
                    continue
                comments.append({
                    "id": f"reddit_comment_{comment['id']}",
                    "source": "reddit",
                    "title": "Comment",
                    "text": body,
                    "author": comment.get("author", "[deleted]"),
                    "created_utc": datetime.fromtimestamp(
                        comment.get("created_utc", 0)
                    ).isoformat() if comment.get("created_utc") else "",
                    "score": comment.get("score", 0),
                    "num_comments": 0,
                    "url": f"https://reddit.com{comment.get('permalink', '')}",
                    "type": "comment",
                })
        return comments
    except Exception:
        return []


class RedditScraper(BaseScraper):
    name = "Reddit"
    source = "reddit"

    def validate_config(self) -> tuple[bool, str]:
        return True, "No API key required"

    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        start = time.time()
        all_posts = []
        errors = []
        total_queries = len(SUBREDDITS) * len(SEARCH_QUERIES)
        current = 0

        for subreddit in SUBREDDITS:
            for query in SEARCH_QUERIES:
                current += 1
                if progress_callback:
                    progress_callback(current, total_queries, f"r/{subreddit}: '{query}'")

                try:
                    posts = _fetch_reddit_json(subreddit, query, POST_LIMIT)
                    if posts:
                        all_posts.extend(posts)

                        # Fetch comments for top 2 posts
                        top = sorted(posts, key=lambda x: x["score"], reverse=True)[:2]
                        for post in top:
                            time.sleep(1.5)
                            comments = _fetch_comments(post["id"], subreddit, COMMENTS_PER_POST)
                            all_posts.extend(comments)
                except Exception as e:
                    errors.append(f"r/{subreddit} '{query}': {str(e)}")

                time.sleep(2)

        # Deduplicate by ID
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
