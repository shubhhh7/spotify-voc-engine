"""
Social/Twitter Scraper FINAL - Focused on WORKING methods
==========================================================
Based on testing: Reddit PullPush API is the most reliable source.
Also tries Bluesky and Hacker News (both reliable).
Skips methods proven to fail (Nitter, Google, Bing, DuckDuckGo).

Output: data/raw/twitter_posts.csv
"""

import requests
import pandas as pd
import time
import re
import os
from datetime import datetime
from tqdm import tqdm

MIN_TEXT_LENGTH = 30
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


# ============================================================
# METHOD 1: REDDIT (PullPush API) - PROVEN WORKING
# ============================================================

def fetch_reddit_posts():
    """Fetch Reddit submissions about Spotify discovery issues."""
    posts = []
    queries_by_subreddit = {
        "spotify": [
            "algorithm", "recommendations bad", "discover weekly terrible",
            "shuffle broken", "same songs", "daily mix repetitive",
            "can't find new music", "discovery sucks", "repetitive",
            "frustrating", "switched to", "echo chamber", "stuck in loop",
            "algorithm broken", "new music", "on repeat", "shuffle",
        ],
        "truespotify": [
            "algorithm", "recommendations", "discovery", "shuffle",
            "repetitive", "same artists", "frustrating", "daily mix",
            "discover weekly", "stuck", "broken", "terrible",
        ],
        "music": [
            "spotify algorithm", "spotify recommendations",
            "spotify discovery broken", "spotify same songs",
            "spotify echo chamber", "streaming recommendations",
        ],
        "musicsuggestions": [
            "spotify won't recommend", "spotify stuck", "spotify boring",
            "spotify suggestions", "spotify discovery",
        ],
        "LetsTalkMusic": [
            "spotify algorithm", "streaming discovery",
            "spotify recommendations", "music discovery",
            "algorithmic playlist", "recommendation engine",
        ],
        "AppleMusic": [
            "switched from spotify", "spotify algorithm",
            "spotify recommendations", "left spotify",
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
                response = requests.get(url, headers=HEADERS, params=params, timeout=20)
                if response.status_code != 200:
                    continue

                data = response.json()
                for post in data.get("data", []):
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
                        created_str = datetime.fromtimestamp(int(created)).isoformat()
                    except (ValueError, TypeError, OSError):
                        created_str = ""

                    posts.append({
                        "id": f"reddit_{post.get('id', len(posts))}",
                        "source": "reddit",
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

                time.sleep(1.2)
            except Exception:
                continue

        if sub_count > 0:
            print(f"   r/{subreddit}: {sub_count} posts")

    return posts


def fetch_reddit_comments():
    """Fetch Reddit comments - rich qualitative data."""
    posts = []
    queries = [
        "spotify algorithm terrible",
        "spotify recommendations same",
        "spotify discovery broken",
        "spotify shuffle not random",
        "spotify stuck same artists",
        "spotify echo chamber",
        "spotify daily mix boring",
        "spotify suggest same songs",
        "spotify discover weekly bad",
        "spotify repetitive playlist",
    ]

    for query in tqdm(queries, desc="   Reddit comments"):
        try:
            url = "https://api.pullpush.io/reddit/search/comment/"
            params = {"q": query, "size": 40, "sort": "desc", "sort_type": "score"}
            response = requests.get(url, headers=HEADERS, params=params, timeout=20)
            if response.status_code != 200:
                continue

            data = response.json()
            for comment in data.get("data", []):
                text = comment.get("body", "")
                if text in ("[removed]", "[deleted]", ""):
                    continue
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if comment.get("score", 0) < 2:
                    continue

                created = comment.get("created_utc", 0)
                try:
                    created_str = datetime.fromtimestamp(int(created)).isoformat()
                except (ValueError, TypeError, OSError):
                    created_str = ""

                sub = comment.get("subreddit", "unknown")
                posts.append({
                    "id": f"reddit_c_{comment.get('id', len(posts))}",
                    "source": "reddit_comment",
                    "platform": f"Reddit r/{sub}",
                    "query": query,
                    "title": f"Comment in r/{sub}",
                    "text": text,
                    "author": comment.get("author", "[deleted]"),
                    "created_utc": created_str,
                    "score": comment.get("score", 0),
                    "num_comments": 0,
                    "url": f"https://reddit.com{comment.get('permalink', '')}",
                    "type": "comment",
                })

            time.sleep(1.2)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 2: HACKER NEWS (Algolia API) - VERY RELIABLE
# ============================================================

def fetch_hackernews():
    """Search Hacker News - comments are gold for insights."""
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations", "spotify discovery",
        "spotify music discovery", "spotify playlist", "spotify shuffle",
        "spotify repeat", "music recommendation", "streaming discovery",
        "discover weekly", "spotify alternative", "spotify echo chamber",
        "spotify monopoly", "spotify AI", "spotify daylist",
    ]

    for query in tqdm(queries, desc="   Hacker News"):
        try:
            url = "https://hn.algolia.com/api/v1/search"
            # Stories
            params = {"query": query, "tags": "story", "hitsPerPage": 20}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if resp.status_code == 200:
                for hit in resp.json().get("hits", []):
                    title = hit.get("title", "") or ""
                    text = title
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    oid = hit.get("objectID", str(len(posts)))
                    posts.append({
                        "id": f"hn_{oid}",
                        "source": "hackernews",
                        "platform": "Hacker News",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": hit.get("author", "unknown"),
                        "created_utc": hit.get("created_at", ""),
                        "score": hit.get("points", 0) or 0,
                        "num_comments": hit.get("num_comments", 0) or 0,
                        "url": f"https://news.ycombinator.com/item?id={oid}",
                        "type": "post",
                    })

            # Comments (much richer data)
            params = {"query": query, "tags": "comment", "hitsPerPage": 40}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if resp.status_code == 200:
                for hit in resp.json().get("hits", []):
                    text = hit.get("comment_text", "") or ""
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue
                    oid = hit.get("objectID", str(len(posts)))
                    posts.append({
                        "id": f"hn_c_{oid}",
                        "source": "hackernews",
                        "platform": "Hacker News",
                        "query": query,
                        "title": f"Comment on: {hit.get('story_title', query)}",
                        "text": text,
                        "author": hit.get("author", "unknown"),
                        "created_utc": hit.get("created_at", ""),
                        "score": hit.get("points", 0) or 0,
                        "num_comments": 0,
                        "url": f"https://news.ycombinator.com/item?id={oid}",
                        "type": "comment",
                    })

            time.sleep(0.3)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 3: BLUESKY (Public API)
# ============================================================

def fetch_bluesky():
    """Bluesky public search - no auth needed."""
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations", "spotify discovery",
        "spotify shuffle", "spotify repetitive", "spotify same songs",
        "spotify daily mix", "spotify discover weekly", "spotify broken",
        "spotify frustrating", "spotify sucks", "left spotify",
        "spotify stuck", "spotify echo chamber", "spotify playlist",
        "spotify on repeat", "switching from spotify", "spotify needs",
        "spotify indie", "spotify niche", "spotify new music",
    ]

    for query in tqdm(queries, desc="   Bluesky"):
        try:
            url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 50}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if resp.status_code != 200:
                continue

            for post in resp.json().get("posts", []):
                record = post.get("record", {})
                text = record.get("text", "")
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue

                author = post.get("author", {})
                handle = author.get("handle", "unknown")
                uri = post.get("uri", "")
                pid = uri.split("/")[-1] if uri else str(len(posts))

                posts.append({
                    "id": f"bsky_{pid}",
                    "source": "bluesky",
                    "platform": "Bluesky",
                    "query": query,
                    "title": f"Post by @{handle}",
                    "text": text,
                    "author": handle,
                    "created_utc": record.get("createdAt", ""),
                    "score": post.get("likeCount", 0),
                    "num_comments": post.get("replyCount", 0),
                    "url": f"https://bsky.app/profile/{handle}/post/{pid}",
                    "type": "tweet",
                })

            time.sleep(0.5)
        except Exception:
            continue

    return posts


# ============================================================
# METHOD 4: MASTODON
# ============================================================

def fetch_mastodon():
    """Mastodon public search across instances."""
    posts = []
    instances = [
        "https://mastodon.social",
        "https://fosstodon.org",
        "https://hachyderm.io",
        "https://techhub.social",
        "https://mas.to",
    ]
    queries = [
        "spotify algorithm", "spotify recommendations", "spotify discovery",
        "spotify shuffle", "spotify repetitive", "spotify same",
        "spotify daily mix", "spotify broken", "spotify frustrating",
        "left spotify", "spotify sucks", "spotify stuck",
    ]

    for instance in instances:
        inst_count = 0
        for query in queries:
            try:
                url = f"{instance}/api/v2/search"
                params = {"q": query, "type": "statuses", "limit": 40}
                resp = requests.get(url, headers=HEADERS, params=params, timeout=8)
                if resp.status_code != 200:
                    continue

                for status in resp.json().get("statuses", []):
                    text = re.sub(r"<[^>]+>", " ", status.get("content", ""))
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    acct = status.get("account", {}).get("acct", "unknown")
                    posts.append({
                        "id": f"mast_{status.get('id', len(posts))}",
                        "source": "mastodon",
                        "platform": "Mastodon",
                        "query": query,
                        "title": f"Toot by @{acct}",
                        "text": text,
                        "author": acct,
                        "created_utc": status.get("created_at", ""),
                        "score": status.get("favourites_count", 0),
                        "num_comments": status.get("replies_count", 0),
                        "url": status.get("url", ""),
                        "type": "tweet",
                    })
                    inst_count += 1

                time.sleep(0.5)
            except Exception:
                continue

        if inst_count > 0:
            print(f"   {instance}: {inst_count} posts")
        time.sleep(0.5)

    return posts


# ============================================================
# METHOD 5: LEMMY
# ============================================================

def fetch_lemmy():
    """Lemmy instances - Reddit alternative."""
    posts = []
    instances = [
        "https://lemmy.world", "https://lemmy.ml",
        "https://lemm.ee", "https://sh.itjust.works",
    ]
    queries = [
        "spotify", "spotify algorithm", "spotify recommendations",
        "spotify discovery", "spotify shuffle", "music streaming",
    ]

    for instance in instances:
        inst_count = 0
        for query in queries:
            try:
                url = f"{instance}/api/v3/search"
                params = {"q": query, "type_": "Posts", "sort": "TopAll", "limit": 25}
                resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
                if resp.status_code != 200:
                    continue

                for item in resp.json().get("posts", []):
                    pd_data = item.get("post", {})
                    counts = item.get("counts", {})
                    creator = item.get("creator", {})

                    title = pd_data.get("name", "")
                    body = pd_data.get("body", "")
                    text = f"{title}. {body}".strip() if body else title

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    posts.append({
                        "id": f"lemmy_{pd_data.get('id', len(posts))}",
                        "source": "lemmy",
                        "platform": "Lemmy",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": creator.get("name", "unknown"),
                        "created_utc": pd_data.get("published", ""),
                        "score": counts.get("score", 0),
                        "num_comments": counts.get("comments", 0),
                        "url": pd_data.get("ap_id", ""),
                        "type": "post",
                    })
                    inst_count += 1

                time.sleep(0.5)
            except Exception:
                continue

        if inst_count > 0:
            print(f"   {instance}: {inst_count} posts")
        time.sleep(0.5)

    return posts


# ============================================================
# HELPERS & MAIN
# ============================================================

def categorize(text):
    """Map to research question."""
    t = text.lower()
    if any(w in t for w in ["discover", "find new", "explore", "new music", "new artist"]):
        return "Q1_discovery_struggle"
    elif any(w in t for w in ["recommend", "algorithm", "suggestion", "ai playlist", "daylist"]):
        return "Q2_recommendation_frustration"
    elif any(w in t for w in ["mood", "vibe", "focus", "workout", "trying to listen", "genre"]):
        return "Q3_listening_behavior"
    elif any(w in t for w in ["same", "repeat", "loop", "stuck", "over and over", "shuffle"]):
        return "Q4_repetition_cause"
    elif any(w in t for w in ["free", "premium", "indie", "niche", "new user", "casual"]):
        return "Q5_segment_challenge"
    elif any(w in t for w in ["need", "should", "wish", "missing", "switch", "left", "alternative"]):
        return "Q6_unmet_need"
    return "general"


def main():
    print("🐦 Social Media Scraper - FINAL (Focused on working methods)")
    print("=" * 60)
    print("Methods: Reddit Posts → Reddit Comments → HN → Bluesky → Mastodon → Lemmy")
    print("All FREE, no API keys")
    print("=" * 60)

    all_posts = []
    results = {}

    # 1. Reddit Posts (most reliable, most data)
    print("\n📡 [1/6] Reddit Posts (PullPush API)...")
    try:
        r = fetch_reddit_posts()
        results["Reddit Posts"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} posts")
    except Exception as e:
        results["Reddit Posts"] = 0
        print(f"   ❌ Failed: {e}")

    # 2. Reddit Comments
    print("\n📡 [2/6] Reddit Comments...")
    try:
        r = fetch_reddit_comments()
        results["Reddit Comments"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} comments")
    except Exception as e:
        results["Reddit Comments"] = 0
        print(f"   ❌ Failed: {e}")

    # 3. Hacker News
    print("\n📡 [3/6] Hacker News (Algolia)...")
    try:
        r = fetch_hackernews()
        results["Hacker News"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} posts/comments")
    except Exception as e:
        results["Hacker News"] = 0
        print(f"   ❌ Failed: {e}")

    # 4. Bluesky
    print("\n📡 [4/6] Bluesky (public API)...")
    try:
        r = fetch_bluesky()
        results["Bluesky"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} posts")
    except Exception as e:
        results["Bluesky"] = 0
        print(f"   ❌ Failed: {e}")

    # 5. Mastodon
    print("\n📡 [5/6] Mastodon...")
    try:
        r = fetch_mastodon()
        results["Mastodon"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} posts")
    except Exception as e:
        results["Mastodon"] = 0
        print(f"   ❌ Failed: {e}")

    # 6. Lemmy
    print("\n📡 [6/6] Lemmy...")
    try:
        r = fetch_lemmy()
        results["Lemmy"] = len(r)
        all_posts.extend(r)
        print(f"   ✅ Total: {len(r)} posts")
    except Exception as e:
        results["Lemmy"] = 0
        print(f"   ❌ Failed: {e}")

    # Post-processing
    print(f"\n{'=' * 60}")
    print("🔄 Post-processing...")

    if not all_posts:
        print("❌ No data collected at all. Check internet connection.")
        return

    # Clean
    for p in all_posts:
        p["text"] = re.sub(r"https?://\S+", "", p["text"])
        p["text"] = re.sub(r"\s+", " ", p["text"]).strip()

    # Deduplicate
    seen = set()
    unique = []
    for p in all_posts:
        key = p["text"][:100].lower().strip()
        if key not in seen and len(p["text"]) >= MIN_TEXT_LENGTH:
            seen.add(key)
            unique.append(p)

    # Categorize
    for p in unique:
        p["research_category"] = categorize(p["text"])

    # Save
    df = pd.DataFrame(unique)
    out_path = f"{RAW_DIR}/twitter_posts.csv"
    df.to_csv(out_path, index=False)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"✅ COMPLETE: {len(unique)} unique posts collected")
    print(f"   (from {len(all_posts)} raw, after dedup)")
    print(f"📁 Saved: {out_path}")

    print(f"\n📊 Method Breakdown:")
    for method, count in results.items():
        s = "✅" if count > 0 else "❌"
        print(f"   {s} {method}: {count}")

    print(f"\n📊 Platform Distribution:")
    print(df["platform"].value_counts().to_string())

    print(f"\n📊 Research Category Distribution:")
    print(df["research_category"].value_counts().to_string())

    print(f"\n📊 Quality Metrics:")
    print(f"   Avg text length: {df['text'].str.len().mean():.0f} chars")
    print(f"   Median score: {df['score'].median():.0f}")
    print(f"   Posts with comments: {(df['num_comments'] > 0).sum()}")
    print(f"   High-quality (score>10): {(df['score'] > 10).sum()}")

    if len(unique) >= 200:
        print(f"\n🎉 {len(unique)} posts - excellent dataset for insights!")
    elif len(unique) >= 100:
        print(f"\n👍 {len(unique)} posts - good enough for meaningful analysis.")
    else:
        print(f"\n⚠️ {len(unique)} posts - may need more data.")


if __name__ == "__main__":
    main()
