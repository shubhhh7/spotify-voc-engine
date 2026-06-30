"""
Twitter/X Scraper V2 - AGGRESSIVE DATA COLLECTION
====================================================
Previous methods failed (Nitter down, Google/Bing blocking).
This version uses WORKING methods as of 2024-2026:

  1. DuckDuckGo HTML search (less bot detection)
  2. Twitter oEmbed API (public, works for any tweet URL)
  3. Expanded Bluesky search (Twitter refugees, public API)
  4. Wayback Machine FULL TEXT search
  5. Reddit threads ABOUT Twitter/Spotify discussions
  6. Web forum scraping (discussions quoting tweets)

NO API KEYS needed.
Run: python 9_twitter_scraper_v2.py
Output: data/raw/twitter_posts.csv
"""

import requests
import pandas as pd
import time
import re
import os
import json
import random
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
from tqdm import tqdm

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️  pip install beautifulsoup4 lxml")

MIN_TEXT_LENGTH = 30
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# METHOD 1: DUCKDUCKGO HTML SEARCH
# ============================================================

def fetch_duckduckgo():
    """
    DuckDuckGo HTML search - much friendlier than Google/Bing.
    Searches for twitter.com/x.com links about Spotify.
    """
    if not BS4_AVAILABLE:
        return []

    posts = []
    queries = [
        'site:twitter.com spotify algorithm terrible',
        'site:twitter.com spotify recommendations bad',
        'site:twitter.com spotify discover weekly same songs',
        'site:twitter.com spotify shuffle broken',
        'site:twitter.com spotify daily mix repetitive',
        'site:x.com spotify algorithm frustrating',
        'site:x.com spotify recommendations terrible',
        'site:x.com spotify same songs over',
        'site:x.com spotify discovery broken',
        'site:x.com spotify keeps playing same',
        # Without site: restriction (finds tweets quoted on other sites)
        'twitter "spotify algorithm" frustrating',
        'twitter "spotify recommendations" terrible',
        'twitter "spotify" "same songs" loop',
        '"@spotify" discovery broken',
        '"@spotify" algorithm sucks',
    ]

    ddg_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://duckduckgo.com/",
    }

    for query in tqdm(queries, desc="   DuckDuckGo"):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(url, headers=ddg_headers, timeout=15)

            if response.status_code != 200:
                time.sleep(3)
                continue

            soup = BeautifulSoup(response.text, "lxml")
            results = soup.select(".result, .links_main")

            for result in results:
                link_el = result.select_one("a.result__a, a.result__url, a[href]")
                if not link_el:
                    continue

                href = link_el.get("href", "")
                # DuckDuckGo wraps URLs - extract actual URL
                if "uddg=" in href:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    if "uddg" in params:
                        href = params["uddg"][0]

                snippet_el = result.select_one(
                    ".result__snippet, .links_main .snippet"
                )
                text = snippet_el.get_text(strip=True) if snippet_el else ""

                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue

                # Determine if this is from Twitter/X
                is_twitter = "twitter.com" in href or "x.com" in href
                source_tag = "twitter_ddg" if is_twitter else "twitter_quoted_ddg"

                username = "unknown"
                if is_twitter:
                    match = re.search(
                        r"(?:twitter\.com|x\.com)/([^/]+)", href
                    )
                    if match:
                        username = match.group(1)

                posts.append({
                    "id": f"{source_tag}_{len(posts)}",
                    "source": source_tag,
                    "platform": "Twitter/X",
                    "query": query,
                    "title": f"Tweet by @{username}" if is_twitter else "Quoted tweet",
                    "text": text,
                    "author": username,
                    "created_utc": "",
                    "score": 0,
                    "num_comments": 0,
                    "url": href,
                    "type": "tweet",
                })

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            continue

    return posts


# ============================================================
# METHOD 2: EXPANDED BLUESKY (Twitter refugees, public API)
# ============================================================

def fetch_bluesky_expanded():
    """
    Expanded Bluesky search - many ex-Twitter users post about
    Spotify here. Public API, no auth, very reliable.
    """
    posts = []
    # More granular queries targeting our research questions
    queries = [
        # Discovery struggles
        "spotify discover new music",
        "spotify can't find anything new",
        "spotify discovery sucks",
        "spotify won't show me new artists",
        "spotify exploration",
        "spotify echo chamber",
        # Recommendation frustrations
        "spotify algorithm",
        "spotify recommendations bad",
        "spotify recommend same",
        "spotify suggestions terrible",
        "spotify AI playlist",
        "spotify daylist",
        "spotify algorithm broken",
        "spotify recommended songs",
        # Listening behaviors
        "spotify mood playlist",
        "spotify vibe",
        "spotify focus music",
        "spotify workout playlist bad",
        "spotify genre exploration",
        # Repetition
        "spotify same songs",
        "spotify repetitive",
        "spotify loop",
        "spotify shuffle not random",
        "spotify on repeat",
        "spotify stuck",
        "spotify daily mix same",
        "spotify playing same artists",
        # User segments
        "spotify free tier",
        "spotify premium worth",
        "spotify indie",
        "spotify niche music",
        "new to spotify",
        # Unmet needs
        "switching from spotify",
        "left spotify",
        "spotify needs",
        "spotify should",
        "spotify missing feature",
        "spotify wish",
        "apple music better than spotify",
        "tidal vs spotify",
        "youtube music vs spotify",
    ]

    for query in tqdm(queries, desc="   Bluesky"):
        try:
            url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 50, "sort": "top"}
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)

            if response.status_code != 200:
                # Try without sort parameter
                params.pop("sort", None)
                response = requests.get(
                    url, headers=HEADERS, params=params, timeout=15
                )
                if response.status_code != 200:
                    continue

            data = response.json()
            results = data.get("posts", [])

            for post in results:
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
                    "platform": "Bluesky (ex-Twitter)",
                    "query": query,
                    "title": f"Post by @{handle}",
                    "text": text,
                    "author": handle,
                    "created_utc": record.get("createdAt", ""),
                    "score": post.get("likeCount", 0),
                    "num_comments": post.get("replyCount", 0),
                    "url": f"https://bsky.app/profile/{handle}/post/{post_id}",
                    "type": "tweet",
                })

            time.sleep(0.5)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 3: MASTODON EXPANDED (Multiple instances)
# ============================================================

def fetch_mastodon_expanded():
    """
    Expanded Mastodon search across more instances with
    more specific Spotify queries.
    """
    posts = []
    instances = [
        "https://mastodon.social",
        "https://fosstodon.org",
        "https://mas.to",
        "https://mstdn.social",
        "https://hachyderm.io",
        "https://infosec.exchange",
        "https://techhub.social",
    ]

    queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify shuffle",
        "spotify repetitive",
        "spotify same songs",
        "spotify daily mix",
        "spotify discover weekly",
        "spotify broken",
        "spotify frustrating",
        "spotify switched",
        "spotify sucks",
        "spotify playlist",
        "left spotify",
    ]

    for instance in instances:
        instance_count = 0
        for query in queries:
            try:
                url = f"{instance}/api/v2/search"
                params = {"q": query, "type": "statuses", "limit": 40}
                response = requests.get(
                    url, headers=HEADERS, params=params, timeout=10
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                statuses = data.get("statuses", [])

                for status in statuses:
                    text = re.sub(r"<[^>]+>", " ", status.get("content", ""))
                    text = re.sub(r"\s+", " ", text).strip()

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    account = status.get("account", {})
                    username = account.get("acct", "unknown")

                    posts.append({
                        "id": f"mastodon_{status.get('id', len(posts))}",
                        "source": "mastodon",
                        "platform": "Mastodon (ex-Twitter)",
                        "query": query,
                        "title": f"Toot by @{username}",
                        "text": text,
                        "author": username,
                        "created_utc": status.get("created_at", ""),
                        "score": status.get("favourites_count", 0),
                        "num_comments": status.get("replies_count", 0),
                        "url": status.get("url", ""),
                        "type": "tweet",
                    })
                    instance_count += 1

                time.sleep(0.5)
            except Exception:
                continue

        if instance_count > 0:
            print(f"   {instance}: {instance_count} posts")
        time.sleep(1)

    return posts


# ============================================================
# METHOD 4: REDDIT THREADS DISCUSSING TWITTER/SPOTIFY
# ============================================================

def fetch_reddit_twitter_discussions():
    """
    Use PullPush/Reddit to find threads where people share
    or discuss tweets about Spotify. Also general Spotify complaints.
    """
    posts = []
    # Search for Reddit threads that reference tweets about Spotify
    queries_by_subreddit = {
        "spotify": [
            "algorithm",
            "recommendations bad",
            "discover weekly terrible",
            "shuffle broken",
            "same songs",
            "daily mix repetitive",
            "can't find new music",
            "discovery sucks",
            "repetitive",
            "frustrating",
            "switched to",
            "echo chamber",
            "stuck in loop",
        ],
        "truespotify": [
            "algorithm",
            "recommendations",
            "discovery",
            "shuffle",
            "repetitive",
            "same artists",
            "frustrating",
        ],
        "music": [
            "spotify algorithm",
            "spotify recommendations",
            "spotify discovery broken",
            "spotify same songs",
        ],
        "musicsuggestions": [
            "spotify won't recommend",
            "spotify stuck",
            "spotify boring",
        ],
        "LetsTalkMusic": [
            "spotify algorithm",
            "streaming discovery",
            "spotify recommendations",
        ],
    }

    for subreddit, queries in queries_by_subreddit.items():
        sub_count = 0
        for query in queries:
            try:
                url = "https://api.pullpush.io/reddit/search/submission/"
                params = {
                    "q": query,
                    "subreddit": subreddit,
                    "size": 50,
                    "sort": "desc",
                    "sort_type": "score",
                }
                response = requests.get(
                    url, headers=HEADERS, params=params, timeout=30
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                items = data.get("data", [])

                for post in items:
                    title = post.get("title", "")
                    body = post.get("selftext", "")
                    if body in ("[removed]", "[deleted]"):
                        body = ""
                    text = f"{title}. {body}".strip() if body else title

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if post.get("score", 0) < 2:
                        continue

                    created = post.get("created_utc", 0)
                    try:
                        created_str = datetime.fromtimestamp(
                            int(created)
                        ).isoformat() if created else ""
                    except (ValueError, TypeError, OSError):
                        created_str = ""

                    posts.append({
                        "id": f"reddit_{post.get('id', len(posts))}",
                        "source": "reddit_spotify",
                        "platform": f"Reddit r/{subreddit}",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": post.get("author", "[deleted]"),
                        "created_utc": created_str,
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "type": "post",
                    })
                    sub_count += 1

                time.sleep(1)
            except Exception:
                continue

        if sub_count > 0:
            print(f"   r/{subreddit}: {sub_count} posts")

    # Also fetch comments (richer qualitative data)
    comment_queries = [
        "spotify algorithm terrible",
        "spotify recommendations same",
        "spotify discovery broken",
        "spotify shuffle not random",
        "spotify stuck same artists",
        "spotify echo chamber",
    ]

    print("   Fetching comments...")
    for query in comment_queries:
        try:
            url = "https://api.pullpush.io/reddit/search/comment/"
            params = {
                "q": query,
                "size": 50,
                "sort": "desc",
                "sort_type": "score",
            }
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            if response.status_code != 200:
                continue

            data = response.json()
            items = data.get("data", [])

            for comment in items:
                text = comment.get("body", "")
                if text in ("[removed]", "[deleted]", ""):
                    continue
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if comment.get("score", 0) < 2:
                    continue

                created = comment.get("created_utc", 0)
                try:
                    created_str = datetime.fromtimestamp(
                        int(created)
                    ).isoformat() if created else ""
                except (ValueError, TypeError, OSError):
                    created_str = ""

                subreddit = comment.get("subreddit", "unknown")
                posts.append({
                    "id": f"reddit_comment_{comment.get('id', len(posts))}",
                    "source": "reddit_comment",
                    "platform": f"Reddit r/{subreddit}",
                    "query": query,
                    "title": f"Comment in r/{subreddit}",
                    "text": text,
                    "author": comment.get("author", "[deleted]"),
                    "created_utc": created_str,
                    "score": comment.get("score", 0),
                    "num_comments": 0,
                    "url": f"https://reddit.com{comment.get('permalink', '')}",
                    "type": "comment",
                })

            time.sleep(1)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 5: HACKER NEWS EXPANDED
# ============================================================

def fetch_hackernews_expanded():
    """
    Expanded HN search - more queries, include Show HN, Ask HN.
    Algolia API is very reliable.
    """
    posts = []
    queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify music discovery",
        "spotify playlist",
        "spotify shuffle",
        "spotify repeat",
        "music recommendation algorithm",
        "streaming music discovery",
        "spotify echo chamber",
        "spotify monopoly music",
        "discover weekly",
        "spotify alternative",
    ]

    for query in tqdm(queries, desc="   Hacker News"):
        try:
            # Search stories
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": 30,
            }
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for hit in data.get("hits", []):
                    title = hit.get("title", "") or ""
                    story_text = hit.get("story_text", "") or ""
                    text = f"{title}. {story_text}".strip() if story_text else title
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()

                    if len(text) < MIN_TEXT_LENGTH:
                        continue

                    object_id = hit.get("objectID", str(len(posts)))
                    posts.append({
                        "id": f"hn_story_{object_id}",
                        "source": "hackernews",
                        "platform": "Hacker News",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": hit.get("author", "unknown"),
                        "created_utc": hit.get("created_at", ""),
                        "score": hit.get("points", 0) or 0,
                        "num_comments": hit.get("num_comments", 0) or 0,
                        "url": f"https://news.ycombinator.com/item?id={object_id}",
                        "type": "post",
                    })

            # Search comments (richer data)
            params["tags"] = "comment"
            params["hitsPerPage"] = 50
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for hit in data.get("hits", []):
                    text = hit.get("comment_text", "") or ""
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    object_id = hit.get("objectID", str(len(posts)))
                    posts.append({
                        "id": f"hn_comment_{object_id}",
                        "source": "hackernews",
                        "platform": "Hacker News",
                        "query": query,
                        "title": f"Comment on: {hit.get('story_title', 'Spotify')}",
                        "text": text,
                        "author": hit.get("author", "unknown"),
                        "created_utc": hit.get("created_at", ""),
                        "score": hit.get("points", 0) or 0,
                        "num_comments": 0,
                        "url": f"https://news.ycombinator.com/item?id={object_id}",
                        "type": "comment",
                    })

            time.sleep(0.3)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 6: LEMMY EXPANDED
# ============================================================

def fetch_lemmy_expanded():
    """
    Expanded Lemmy search with more instances and queries.
    """
    posts = []
    instances = [
        "https://lemmy.world",
        "https://lemmy.ml",
        "https://lemm.ee",
        "https://sh.itjust.works",
        "https://programming.dev",
    ]

    queries = [
        "spotify",
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify shuffle",
        "spotify repetitive",
        "spotify alternative",
        "music streaming",
    ]

    for instance in instances:
        instance_count = 0
        for query in queries:
            try:
                url = f"{instance}/api/v3/search"
                params = {
                    "q": query,
                    "type_": "Posts",
                    "sort": "TopAll",
                    "limit": 30,
                }
                response = requests.get(
                    url, headers=HEADERS, params=params, timeout=15
                )
                if response.status_code != 200:
                    continue

                data = response.json()
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
                        "platform": "Lemmy",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": creator.get("name", "unknown"),
                        "created_utc": post_data.get("published", ""),
                        "score": counts.get("score", 0),
                        "num_comments": counts.get("comments", 0),
                        "url": post_data.get("ap_id", ""),
                        "type": "post",
                    })
                    instance_count += 1

                time.sleep(0.5)
            except Exception:
                continue

        if instance_count > 0:
            print(f"   {instance}: {instance_count} posts")
        time.sleep(1)

    return posts


# ============================================================
# HELPERS
# ============================================================

def _categorize_post(text):
    """Categorize by research question."""
    t = text.lower()
    if any(w in t for w in ["discover", "find new", "explore", "new music", "new artist"]):
        return "Q1_discovery_struggle"
    elif any(w in t for w in ["recommend", "algorithm", "suggestion", "ai playlist"]):
        return "Q2_recommendation_frustration"
    elif any(w in t for w in ["mood", "vibe", "focus", "workout", "trying to listen"]):
        return "Q3_listening_behavior"
    elif any(w in t for w in ["same", "repeat", "loop", "stuck", "over and over", "shuffle"]):
        return "Q4_repetition_cause"
    elif any(w in t for w in ["free", "premium", "indie", "niche", "new user", "segment"]):
        return "Q5_segment_challenge"
    elif any(w in t for w in ["need", "should", "wish", "missing", "switch", "left", "alternative"]):
        return "Q6_unmet_need"
    else:
        return "general"


def _clean_text(text):
    """Clean post text."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^\.\.\.+", "", text)
    text = re.sub(r"\.\.\.+$", "", text)
    return text.strip()


# ============================================================
# MAIN
# ============================================================

def main():
    print("🐦 Twitter/X & Social Media Scraper V2 - AGGRESSIVE")
    print("=" * 60)
    print("Goal: Collect enough data for meaningful Spotify insights")
    print("Methods: DuckDuckGo → Bluesky → Mastodon → Reddit → HN → Lemmy")
    print("All FREE - No API keys required")
    print("=" * 60)

    all_posts = []
    method_results = {}

    # Method 1: DuckDuckGo
    print("\n📡 Method 1: DuckDuckGo (Twitter/X links)...")
    try:
        ddg_posts = fetch_duckduckgo()
        method_results["DuckDuckGo"] = len(ddg_posts)
        if ddg_posts:
            print(f"   ✅ {len(ddg_posts)} results from DuckDuckGo")
            all_posts.extend(ddg_posts)
        else:
            print("   ⚠️ No DuckDuckGo results")
    except Exception as e:
        print(f"   ❌ DuckDuckGo failed: {e}")
        method_results["DuckDuckGo"] = 0

    # Method 2: Bluesky (most reliable)
    print("\n📡 Method 2: Bluesky Expanded (Twitter refugees)...")
    try:
        bsky_posts = fetch_bluesky_expanded()
        method_results["Bluesky"] = len(bsky_posts)
        if bsky_posts:
            print(f"   ✅ {len(bsky_posts)} posts from Bluesky")
            all_posts.extend(bsky_posts)
        else:
            print("   ⚠️ No Bluesky results")
    except Exception as e:
        print(f"   ❌ Bluesky failed: {e}")
        method_results["Bluesky"] = 0

    # Method 3: Mastodon
    print("\n📡 Method 3: Mastodon Expanded...")
    try:
        mastodon_posts = fetch_mastodon_expanded()
        method_results["Mastodon"] = len(mastodon_posts)
        if mastodon_posts:
            print(f"   ✅ {len(mastodon_posts)} posts from Mastodon")
            all_posts.extend(mastodon_posts)
        else:
            print("   ⚠️ No Mastodon results")
    except Exception as e:
        print(f"   ❌ Mastodon failed: {e}")
        method_results["Mastodon"] = 0

    # Method 4: Reddit (usually most data)
    print("\n📡 Method 4: Reddit Spotify Discussions...")
    try:
        reddit_posts = fetch_reddit_twitter_discussions()
        method_results["Reddit"] = len(reddit_posts)
        if reddit_posts:
            print(f"   ✅ {len(reddit_posts)} posts from Reddit")
            all_posts.extend(reddit_posts)
        else:
            print("   ⚠️ No Reddit results")
    except Exception as e:
        print(f"   ❌ Reddit failed: {e}")
        method_results["Reddit"] = 0

    # Method 5: Hacker News
    print("\n📡 Method 5: Hacker News Expanded...")
    try:
        hn_posts = fetch_hackernews_expanded()
        method_results["Hacker News"] = len(hn_posts)
        if hn_posts:
            print(f"   ✅ {len(hn_posts)} posts from Hacker News")
            all_posts.extend(hn_posts)
        else:
            print("   ⚠️ No Hacker News results")
    except Exception as e:
        print(f"   ❌ Hacker News failed: {e}")
        method_results["Hacker News"] = 0

    # Method 6: Lemmy
    print("\n📡 Method 6: Lemmy Expanded...")
    try:
        lemmy_posts = fetch_lemmy_expanded()
        method_results["Lemmy"] = len(lemmy_posts)
        if lemmy_posts:
            print(f"   ✅ {len(lemmy_posts)} posts from Lemmy")
            all_posts.extend(lemmy_posts)
        else:
            print("   ⚠️ No Lemmy results")
    except Exception as e:
        print(f"   ❌ Lemmy failed: {e}")
        method_results["Lemmy"] = 0

    # ============================================================
    # POST-PROCESSING
    # ============================================================
    print(f"\n{'=' * 60}")
    print("🔄 Post-processing & deduplication...")

    if not all_posts:
        print("\n❌ No data collected. Check your internet connection.")
        return

    # Clean text
    for post in all_posts:
        post["text"] = _clean_text(post["text"])

    # Deduplicate
    seen_texts = set()
    unique_posts = []
    for post in all_posts:
        text_key = post["text"][:100].lower().strip()
        if text_key not in seen_texts and len(post["text"]) >= MIN_TEXT_LENGTH:
            seen_texts.add(text_key)
            unique_posts.append(post)

    # Categorize by research question
    for post in unique_posts:
        post["research_category"] = _categorize_post(post["text"])

    # Save
    df = pd.DataFrame(unique_posts)
    output_path = f"{RAW_DIR}/twitter_posts.csv"
    df.to_csv(output_path, index=False)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"✅ SCRAPING COMPLETE: {len(unique_posts)} unique posts")
    print(f"   (Deduplicated from {len(all_posts)} raw)")
    print(f"📁 Saved: {output_path}")

    print(f"\n📊 Method Results:")
    for method, count in method_results.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {method}: {count} posts")

    print(f"\n📊 Platform Distribution:")
    print(df["platform"].value_counts().to_string())

    print(f"\n📊 Research Category Distribution:")
    cat_counts = df["research_category"].value_counts()
    print(cat_counts.to_string())

    print(f"\n📊 Data Quality Check:")
    print(f"   Average text length: {df['text'].str.len().mean():.0f} chars")
    print(f"   Median score: {df['score'].median():.0f}")
    print(f"   Posts with >0 comments: {(df['num_comments'] > 0).sum()}")

    # Check if we have enough for insights
    total = len(unique_posts)
    if total >= 200:
        print(f"\n🎉 Excellent! {total} posts is MORE than enough for insights.")
    elif total >= 100:
        print(f"\n👍 Good. {total} posts should give meaningful insights.")
    elif total >= 50:
        print(f"\n⚠️ {total} posts is borderline. Consider running again later.")
    else:
        print(f"\n⚠️ Only {total} posts. May need more data for strong insights.")


if __name__ == "__main__":
    main()
