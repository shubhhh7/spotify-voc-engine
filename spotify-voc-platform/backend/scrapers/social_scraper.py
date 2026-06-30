"""
Social Media Scraper Adapter
Collects from: Mastodon, Lemmy, Hacker News, Bluesky.
All public APIs, no auth needed.
"""
import time
import re
import requests
from datetime import datetime
from scrapers.base import BaseScraper, ScraperResult, ProgressCallback

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

MIN_TEXT_LENGTH = 25

SEARCH_QUERIES = [
    "spotify discover new music",
    "spotify recommendations bad",
    "spotify daily mix same",
    "spotify algorithm broken",
    "spotify playlist stuck",
    "spotify shuffle terrible",
]


def _fetch_hackernews() -> list[dict]:
    """Search Hacker News via Algolia API."""
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations",
        "spotify discovery", "spotify music discovery",
    ]
    for query in queries:
        try:
            url = "https://hn.algolia.com/api/v1/search"
            params = {"query": query, "tags": "(story,comment)", "hitsPerPage": 30}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for hit in data.get("hits", []):
                title = hit.get("title", "") or ""
                comment_text = hit.get("comment_text", "") or ""
                story_text = hit.get("story_text", "") or ""
                text = comment_text or story_text or title
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue
                object_id = hit.get("objectID", str(len(posts)))
                posts.append({
                    "id": f"hn_{object_id}",
                    "source": "hackernews",
                    "title": title or f"HN: {hit.get('story_title', 'Spotify')}",
                    "text": text,
                    "author": hit.get("author", "unknown"),
                    "created_utc": hit.get("created_at", ""),
                    "score": hit.get("points", 0) or 0,
                    "num_comments": hit.get("num_comments", 0) or 0,
                    "url": f"https://news.ycombinator.com/item?id={object_id}",
                    "type": "post" if title else "comment",
                })
            time.sleep(0.5)
        except Exception:
            continue
    return posts


def _fetch_lemmy() -> list[dict]:
    """Search Lemmy instances."""
    posts = []
    instances = ["https://lemmy.world", "https://lemmy.ml", "https://lemm.ee"]
    queries = ["spotify", "spotify algorithm", "spotify recommendations"]

    for instance in instances:
        for query in queries:
            try:
                url = f"{instance}/api/v3/search"
                params = {"q": query, "type_": "Posts", "sort": "TopAll", "limit": 20}
                resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for item in data.get("posts", []):
                    post_data = item.get("post", {})
                    counts = item.get("counts", {})
                    creator = item.get("creator", {})
                    title = post_data.get("name", "")
                    body = post_data.get("body", "")
                    text = f"{title}. {body}".strip() if body else title
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue
                    posts.append({
                        "id": f"lemmy_{post_data.get('id', len(posts))}",
                        "source": "lemmy",
                        "title": title,
                        "text": text,
                        "author": creator.get("name", "unknown"),
                        "created_utc": post_data.get("published", ""),
                        "score": counts.get("score", 0),
                        "num_comments": counts.get("comments", 0),
                        "url": post_data.get("ap_id", ""),
                        "type": "post",
                    })
                time.sleep(1)
            except Exception:
                continue
    return posts


def _fetch_bluesky() -> list[dict]:
    """Search Bluesky public API."""
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations",
        "spotify discovery", "spotify shuffle",
    ]
    for query in queries:
        try:
            url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 25}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for post in data.get("posts", []):
                record = post.get("record", {})
                text = record.get("text", "")
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue
                author_data = post.get("author", {})
                handle = author_data.get("handle", "unknown")
                uri = post.get("uri", "")
                post_id = uri.split("/")[-1] if uri else str(len(posts))
                posts.append({
                    "id": f"bluesky_{post_id}",
                    "source": "bluesky",
                    "title": f"Post by @{handle}",
                    "text": text,
                    "author": handle,
                    "created_utc": record.get("createdAt", ""),
                    "score": post.get("likeCount", 0),
                    "num_comments": post.get("replyCount", 0),
                    "url": f"https://bsky.app/profile/{handle}/post/{post_id}",
                    "type": "post",
                })
            time.sleep(1)
        except Exception:
            continue
    return posts


def _fetch_mastodon() -> list[dict]:
    """Search Mastodon public instances."""
    posts = []
    instances = ["https://mastodon.social", "https://fosstodon.org"]
    queries = ["spotify algorithm", "spotify recommendations", "spotify discovery"]

    for instance in instances:
        for query in queries:
            try:
                url = f"{instance}/api/v2/search"
                params = {"q": query, "type": "statuses", "limit": 20}
                resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for status in data.get("statuses", []):
                    text = re.sub(r"<[^>]+>", " ", status.get("content", ""))
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue
                    account = status.get("account", {})
                    posts.append({
                        "id": f"mastodon_{status.get('id', len(posts))}",
                        "source": "mastodon",
                        "title": f"Toot by @{account.get('acct', 'unknown')}",
                        "text": text,
                        "author": account.get("acct", "unknown"),
                        "created_utc": status.get("created_at", ""),
                        "score": status.get("favourites_count", 0),
                        "num_comments": status.get("replies_count", 0),
                        "url": status.get("url", ""),
                        "type": "post",
                    })
                time.sleep(1)
            except Exception:
                continue
    return posts


class SocialScraper(BaseScraper):
    name = "Social Media"
    source = "social"

    def validate_config(self) -> tuple[bool, str]:
        return True, "All public APIs, no keys needed"

    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        start = time.time()
        all_posts = []
        errors = []
        sources_to_run = [
            ("Hacker News", _fetch_hackernews),
            ("Lemmy", _fetch_lemmy),
            ("Bluesky", _fetch_bluesky),
            ("Mastodon", _fetch_mastodon),
        ]
        total = len(sources_to_run)

        for i, (name, fetch_fn) in enumerate(sources_to_run):
            if progress_callback:
                progress_callback(i + 1, total, f"Fetching {name}...")
            try:
                posts = fetch_fn()
                all_posts.extend(posts)
            except Exception as e:
                errors.append(f"{name}: {str(e)}")

        # Deduplicate by first 100 chars of text
        seen_texts = set()
        unique = []
        for post in all_posts:
            key = post["text"][:100].lower().strip()
            if key not in seen_texts:
                seen_texts.add(key)
                # Override source to "social" so the list endpoint counts correctly
                post["source"] = "social"
                unique.append(post)

        return ScraperResult(
            status="completed" if unique else "failed",
            reviews=unique,
            errors=errors,
            runtime_seconds=time.time() - start,
        )
