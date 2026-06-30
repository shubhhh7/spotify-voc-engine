"""
FAST Social Scraper - Saves incrementally, strict timeouts.
Collects Spotify discovery/recommendation user feedback.
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
OUT_PATH = f"{RAW_DIR}/twitter_posts.csv"

HEADERS = {"User-Agent": "SpotifyVoCResearch/2.0", "Accept": "application/json"}
all_posts = []


def save_progress():
    """Save whatever we have so far."""
    if not all_posts:
        return
    seen = set()
    unique = []
    for p in all_posts:
        key = p["text"][:100].lower().strip()
        if key not in seen and len(p["text"]) >= MIN_TEXT_LENGTH:
            seen.add(key)
            unique.append(p)
    for p in unique:
        p["research_category"] = categorize(p["text"])
    df = pd.DataFrame(unique)
    df.to_csv(OUT_PATH, index=False)
    return len(unique)


def categorize(text):
    t = text.lower()
    if any(w in t for w in ["discover", "find new", "explore", "new music", "new artist"]):
        return "Q1_discovery_struggle"
    elif any(w in t for w in ["recommend", "algorithm", "suggestion", "ai playlist"]):
        return "Q2_recommendation_frustration"
    elif any(w in t for w in ["mood", "vibe", "focus", "workout", "trying to listen", "genre"]):
        return "Q3_listening_behavior"
    elif any(w in t for w in ["same", "repeat", "loop", "stuck", "over and over", "shuffle"]):
        return "Q4_repetition_cause"
    elif any(w in t for w in ["free", "premium", "indie", "niche", "new user"]):
        return "Q5_segment_challenge"
    elif any(w in t for w in ["need", "should", "wish", "missing", "switch", "left", "alternative"]):
        return "Q6_unmet_need"
    return "general"


# ============================================================
# REDDIT POSTS (PullPush) - reduced queries, strict timeout
# ============================================================
def fetch_reddit():
    print("\n📡 [1/5] Reddit (PullPush)...")
    posts = []
    # Focused high-value queries only
    queries = [
        ("spotify", "algorithm"),
        ("spotify", "recommendations bad"),
        ("spotify", "discover weekly"),
        ("spotify", "shuffle broken"),
        ("spotify", "same songs"),
        ("spotify", "daily mix repetitive"),
        ("spotify", "discovery broken"),
        ("spotify", "stuck same artists"),
        ("spotify", "echo chamber"),
        ("spotify", "frustrating"),
        ("truespotify", "algorithm"),
        ("truespotify", "recommendations"),
        ("truespotify", "discovery"),
        ("truespotify", "repetitive"),
        ("truespotify", "shuffle"),
        ("truespotify", "stuck"),
        ("truespotify", "daily mix"),
        ("truespotify", "frustrating"),
        ("music", "spotify algorithm"),
        ("music", "spotify recommendations"),
        ("LetsTalkMusic", "spotify algorithm"),
        ("LetsTalkMusic", "spotify recommendations"),
        ("LetsTalkMusic", "music discovery"),
        ("AppleMusic", "switched from spotify"),
        ("AppleMusic", "left spotify"),
    ]

    for sub, query in tqdm(queries, desc="   Reddit posts"):
        try:
            url = "https://api.pullpush.io/reddit/search/submission/"
            params = {"q": query, "subreddit": sub, "size": 40,
                      "sort": "desc", "sort_type": "score"}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=12)
            if resp.status_code != 200:
                continue
            for post in resp.json().get("data", []):
                title = post.get("title", "")
                body = post.get("selftext", "")
                if body in ("[removed]", "[deleted]"):
                    body = ""
                text = f"{title}. {body}".strip() if body else title
                if len(text) < MIN_TEXT_LENGTH or post.get("score", 0) < 2:
                    continue
                created = post.get("created_utc", 0)
                try:
                    ts = datetime.fromtimestamp(int(created)).isoformat()
                except (ValueError, TypeError, OSError):
                    ts = ""
                posts.append({
                    "id": f"r_{post.get('id', '')}",
                    "source": "reddit",
                    "platform": f"Reddit r/{sub}",
                    "query": query, "title": title, "text": text,
                    "author": post.get("author", ""),
                    "created_utc": ts,
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "type": "post",
                })
            time.sleep(1)
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    print(f"   ✅ {len(posts)} Reddit posts")
    return posts


# ============================================================
# REDDIT COMMENTS
# ============================================================
def fetch_reddit_comments():
    print("\n📡 [2/5] Reddit Comments...")
    posts = []
    queries = [
        "spotify algorithm terrible", "spotify recommendations same",
        "spotify discovery broken", "spotify shuffle not random",
        "spotify stuck same artists", "spotify echo chamber",
        "spotify daily mix boring", "spotify discover weekly bad",
    ]
    for query in tqdm(queries, desc="   Reddit comments"):
        try:
            url = "https://api.pullpush.io/reddit/search/comment/"
            params = {"q": query, "size": 30, "sort": "desc", "sort_type": "score"}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=12)
            if resp.status_code != 200:
                continue
            for c in resp.json().get("data", []):
                text = c.get("body", "")
                if text in ("[removed]", "[deleted]") or len(text) < MIN_TEXT_LENGTH:
                    continue
                if c.get("score", 0) < 2:
                    continue
                created = c.get("created_utc", 0)
                try:
                    ts = datetime.fromtimestamp(int(created)).isoformat()
                except (ValueError, TypeError, OSError):
                    ts = ""
                sub = c.get("subreddit", "unknown")
                posts.append({
                    "id": f"rc_{c.get('id', '')}",
                    "source": "reddit_comment",
                    "platform": f"Reddit r/{sub}",
                    "query": query, "title": f"Comment in r/{sub}",
                    "text": text, "author": c.get("author", ""),
                    "created_utc": ts, "score": c.get("score", 0),
                    "num_comments": 0,
                    "url": f"https://reddit.com{c.get('permalink', '')}",
                    "type": "comment",
                })
            time.sleep(1)
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue
    print(f"   ✅ {len(posts)} Reddit comments")
    return posts


# ============================================================
# HACKER NEWS (Algolia - fast & reliable)
# ============================================================
def fetch_hn():
    print("\n📡 [3/5] Hacker News...")
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations", "spotify discovery",
        "spotify playlist", "spotify shuffle", "spotify repeat",
        "music recommendation", "discover weekly", "spotify alternative",
        "spotify echo chamber", "spotify AI",
    ]
    for query in tqdm(queries, desc="   HN"):
        try:
            url = "https://hn.algolia.com/api/v1/search"
            # Comments first (richer)
            params = {"query": query, "tags": "comment", "hitsPerPage": 40}
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                for hit in resp.json().get("hits", []):
                    text = hit.get("comment_text", "") or ""
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue
                    oid = hit.get("objectID", "")
                    posts.append({
                        "id": f"hn_{oid}",
                        "source": "hackernews",
                        "platform": "Hacker News",
                        "query": query,
                        "title": f"Comment on: {hit.get('story_title', query)}",
                        "text": text,
                        "author": hit.get("author", ""),
                        "created_utc": hit.get("created_at", ""),
                        "score": hit.get("points", 0) or 0,
                        "num_comments": 0,
                        "url": f"https://news.ycombinator.com/item?id={oid}",
                        "type": "comment",
                    })
            time.sleep(0.3)
        except Exception:
            continue
    print(f"   ✅ {len(posts)} HN comments")
    return posts


# ============================================================
# BLUESKY (public API)
# ============================================================
def fetch_bluesky():
    print("\n📡 [4/5] Bluesky...")
    posts = []
    queries = [
        "spotify algorithm", "spotify recommendations", "spotify discovery",
        "spotify shuffle", "spotify repetitive", "spotify same songs",
        "spotify daily mix", "spotify discover weekly", "spotify broken",
        "spotify frustrating", "left spotify", "spotify stuck",
        "spotify sucks", "spotify echo chamber", "spotify playlist boring",
        "spotify on repeat", "switching from spotify", "spotify needs",
        "spotify niche", "spotify new music",
    ]
    for query in tqdm(queries, desc="   Bluesky"):
        try:
            url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 50}
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code != 200:
                continue
            for post in resp.json().get("posts", []):
                record = post.get("record", {})
                text = record.get("text", "")
                if len(text) < MIN_TEXT_LENGTH or "spotify" not in text.lower():
                    continue
                author = post.get("author", {})
                handle = author.get("handle", "unknown")
                uri = post.get("uri", "")
                pid = uri.split("/")[-1] if uri else str(len(posts))
                posts.append({
                    "id": f"bsky_{pid}",
                    "source": "bluesky",
                    "platform": "Bluesky",
                    "query": query, "title": f"@{handle}",
                    "text": text, "author": handle,
                    "created_utc": record.get("createdAt", ""),
                    "score": post.get("likeCount", 0),
                    "num_comments": post.get("replyCount", 0),
                    "url": f"https://bsky.app/profile/{handle}/post/{pid}",
                    "type": "tweet",
                })
            time.sleep(0.4)
        except Exception:
            continue
    print(f"   ✅ {len(posts)} Bluesky posts")
    return posts


# ============================================================
# MASTODON + LEMMY combined
# ============================================================
def fetch_mastodon_lemmy():
    print("\n📡 [5/5] Mastodon + Lemmy...")
    posts = []

    # Mastodon
    instances = ["https://mastodon.social", "https://fosstodon.org",
                 "https://hachyderm.io", "https://techhub.social"]
    mast_queries = ["spotify algorithm", "spotify recommendations",
                    "spotify discovery", "spotify shuffle", "spotify repetitive",
                    "spotify stuck", "left spotify", "spotify sucks"]

    for inst in instances:
        for q in mast_queries:
            try:
                resp = requests.get(f"{inst}/api/v2/search",
                    params={"q": q, "type": "statuses", "limit": 30},
                    headers=HEADERS, timeout=6)
                if resp.status_code != 200:
                    continue
                for s in resp.json().get("statuses", []):
                    text = re.sub(r"<[^>]+>", " ", s.get("content", ""))
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < MIN_TEXT_LENGTH or "spotify" not in text.lower():
                        continue
                    acct = s.get("account", {}).get("acct", "unknown")
                    posts.append({
                        "id": f"m_{s.get('id', '')}",
                        "source": "mastodon", "platform": "Mastodon",
                        "query": q, "title": f"@{acct}",
                        "text": text, "author": acct,
                        "created_utc": s.get("created_at", ""),
                        "score": s.get("favourites_count", 0),
                        "num_comments": s.get("replies_count", 0),
                        "url": s.get("url", ""), "type": "tweet",
                    })
                time.sleep(0.4)
            except Exception:
                continue

    mast_count = len(posts)
    if mast_count:
        print(f"   Mastodon: {mast_count} posts")

    # Lemmy
    lemmy_insts = ["https://lemmy.world", "https://lemmy.ml", "https://lemm.ee"]
    lemmy_queries = ["spotify", "spotify algorithm", "spotify recommendations",
                     "spotify discovery", "spotify shuffle"]
    for inst in lemmy_insts:
        for q in lemmy_queries:
            try:
                resp = requests.get(f"{inst}/api/v3/search",
                    params={"q": q, "type_": "Posts", "sort": "TopAll", "limit": 20},
                    headers=HEADERS, timeout=6)
                if resp.status_code != 200:
                    continue
                for item in resp.json().get("posts", []):
                    pd_ = item.get("post", {})
                    counts = item.get("counts", {})
                    title = pd_.get("name", "")
                    body = pd_.get("body", "")
                    text = f"{title}. {body}".strip() if body else title
                    if len(text) < MIN_TEXT_LENGTH or "spotify" not in text.lower():
                        continue
                    posts.append({
                        "id": f"l_{pd_.get('id', '')}",
                        "source": "lemmy", "platform": "Lemmy",
                        "query": q, "title": title,
                        "text": text,
                        "author": item.get("creator", {}).get("name", ""),
                        "created_utc": pd_.get("published", ""),
                        "score": counts.get("score", 0),
                        "num_comments": counts.get("comments", 0),
                        "url": pd_.get("ap_id", ""), "type": "post",
                    })
                time.sleep(0.4)
            except Exception:
                continue

    lemmy_count = len(posts) - mast_count
    if lemmy_count:
        print(f"   Lemmy: {lemmy_count} posts")
    print(f"   ✅ Total: {len(posts)} (Mastodon + Lemmy)")
    return posts


# ============================================================
# MAIN
# ============================================================
def main():
    global all_posts
    print("🚀 Spotify VoC - Social Media Scraper (Fast Mode)")
    print("=" * 60)

    # Method 1: Reddit posts
    try:
        r = fetch_reddit()
        all_posts.extend(r)
        n = save_progress()
        print(f"   💾 Saved progress: {n} unique posts so far")
    except Exception as e:
        print(f"   ❌ Reddit posts failed: {e}")

    # Method 2: Reddit comments
    try:
        r = fetch_reddit_comments()
        all_posts.extend(r)
        n = save_progress()
        print(f"   💾 Saved progress: {n} unique posts so far")
    except Exception as e:
        print(f"   ❌ Reddit comments failed: {e}")

    # Method 3: HN
    try:
        r = fetch_hn()
        all_posts.extend(r)
        n = save_progress()
        print(f"   💾 Saved progress: {n} unique posts so far")
    except Exception as e:
        print(f"   ❌ HN failed: {e}")

    # Method 4: Bluesky
    try:
        r = fetch_bluesky()
        all_posts.extend(r)
        n = save_progress()
        print(f"   💾 Saved progress: {n} unique posts so far")
    except Exception as e:
        print(f"   ❌ Bluesky failed: {e}")

    # Method 5: Mastodon + Lemmy
    try:
        r = fetch_mastodon_lemmy()
        all_posts.extend(r)
        n = save_progress()
        print(f"   💾 Saved progress: {n} unique posts so far")
    except Exception as e:
        print(f"   ❌ Mastodon/Lemmy failed: {e}")

    # Final summary
    if not all_posts:
        print("\n❌ No data collected.")
        return

    df = pd.read_csv(OUT_PATH)
    print(f"\n{'=' * 60}")
    print(f"🎉 DONE! {len(df)} unique posts saved to {OUT_PATH}")
    print(f"\n📊 Platform Distribution:")
    print(df["platform"].value_counts().to_string())
    print(f"\n📊 Research Categories:")
    print(df["research_category"].value_counts().to_string())
    print(f"\n📊 Quality:")
    print(f"   Avg length: {df['text'].str.len().mean():.0f} chars")
    print(f"   High engagement (score>10): {(df['score'] > 10).sum()}")
    print(f"   With discussion (comments>0): {(df['num_comments'] > 0).sum()}")


if __name__ == "__main__":
    main()
