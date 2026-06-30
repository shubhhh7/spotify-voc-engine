"""
Social Media Scraper for Spotify VoC Research - V2
Collects discussions from WORKING public APIs (no auth needed):
  1. Mastodon (public federated search)
  2. Lemmy (Reddit alternative, public API)
  3. Hacker News (Algolia search API)
  4. Reddit social threads (PullPush API)
  5. Bluesky (public API)

NO API keys required for any of these.
Run: python 8_social_scraper.py
Output: data/raw/social_posts.csv
"""
import requests
import pandas as pd
import time
import re
import os
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

MIN_TEXT_LENGTH = 25
RAW_DIR = "data/raw"
FINAL_DIR = "data/final"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

SEARCH_QUERIES = [
    "spotify discover new music",
    "spotify recommendations bad",
    "spotify daily mix same",
    "spotify algorithm broken",
    "spotify playlist stuck",
    "spotify shuffle terrible",
    "spotify repetitive songs",
    "spotify discovery weekly",
]


# ============================================================
# METHOD 1: MASTODON (Public search, no auth)
# ============================================================

def fetch_mastodon():
    """
    Search Mastodon instances for Spotify discussions.
    Uses public search endpoints - no auth needed.
    """
    posts = []
    # Large public Mastodon instances with open search
    instances = [
        "https://mastodon.social",
        "https://fosstodon.org",
        "https://mas.to",
        "https://mstdn.social",
    ]
    
    queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify playlist",
        "spotify shuffle",
        "spotify repeat",
    ]
    
    for instance in instances:
        for query in queries:
            try:
                url = f"{instance}/api/v2/search"
                params = {"q": query, "type": "statuses", "limit": 20}
                response = requests.get(url, headers=HEADERS, params=params, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                statuses = data.get("statuses", [])
                
                for status in statuses:
                    # Strip HTML tags from content
                    text = re.sub(r'<[^>]+>', ' ', status.get("content", ""))
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue
                    
                    account = status.get("account", {})
                    username = account.get("acct", "unknown")
                    
                    posts.append({
                        "id": f"mastodon_{status.get('id', len(posts))}",
                        "source": "mastodon",
                        "platform": "Mastodon",
                        "query": query,
                        "title": f"Toot by @{username}",
                        "text": text,
                        "author": username,
                        "created_utc": status.get("created_at", ""),
                        "score": status.get("favourites_count", 0),
                        "num_comments": status.get("replies_count", 0),
                        "url": status.get("url", ""),
                        "type": "post"
                    })
                
                time.sleep(1)
            except Exception as e:
                continue
        
        if posts:
            print(f"   {instance}: {len(posts)} posts so far")
        time.sleep(1)
    
    return posts


# ============================================================
# METHOD 2: LEMMY (Reddit alternative, public API)
# ============================================================

def fetch_lemmy():
    """
    Search Lemmy instances for Spotify discussions.
    Public API, no auth needed.
    """
    posts = []
    instances = [
        "https://lemmy.world",
        "https://lemmy.ml",
        "https://lemm.ee",
        "https://sh.itjust.works",
    ]
    
    queries = ["spotify", "spotify algorithm", "spotify recommendations", "spotify discovery"]
    
    for instance in instances:
        for query in queries:
            try:
                url = f"{instance}/api/v3/search"
                params = {
                    "q": query,
                    "type_": "Posts",
                    "sort": "TopAll",
                    "limit": 20,
                }
                response = requests.get(url, headers=HEADERS, params=params, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                results = data.get("posts", [])
                
                for item in results:
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
                        "type": "post"
                    })
                
                time.sleep(1)
            except Exception as e:
                continue
        
        if posts:
            print(f"   {instance}: {len(posts)} posts so far")
        time.sleep(1)
    
    return posts


# ============================================================
# METHOD 3: HACKER NEWS (Algolia API, no auth)
# ============================================================

def fetch_hackernews():
    """
    Search Hacker News via Algolia API.
    Completely public, no auth needed, very reliable.
    """
    posts = []
    queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify music discovery",
        "spotify playlist",
    ]
    
    for query in queries:
        try:
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                "query": query,
                "tags": "(story,comment)",
                "hitsPerPage": 30,
            }
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            hits = data.get("hits", [])
            
            for hit in hits:
                title = hit.get("title", "") or ""
                comment_text = hit.get("comment_text", "") or ""
                story_text = hit.get("story_text", "") or ""
                
                # Clean HTML
                text = comment_text or story_text or title
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue
                
                object_id = hit.get("objectID", str(len(posts)))
                
                posts.append({
                    "id": f"hn_{object_id}",
                    "source": "hackernews",
                    "platform": "Hacker News",
                    "query": query,
                    "title": title if title else f"HN comment on: {hit.get('story_title', 'Spotify')}",
                    "text": text,
                    "author": hit.get("author", "unknown"),
                    "created_utc": hit.get("created_at", ""),
                    "score": hit.get("points", 0) or 0,
                    "num_comments": hit.get("num_comments", 0) or 0,
                    "url": f"https://news.ycombinator.com/item?id={object_id}",
                    "type": "post" if title else "comment"
                })
            
            time.sleep(0.5)
        except Exception as e:
            print(f"   HN error for '{query}': {e}")
            continue
    
    return posts


# ============================================================
# METHOD 4: REDDIT SOCIAL THREADS (PullPush API)
# ============================================================

def fetch_reddit_social():
    """
    Fetch Reddit threads discussing Spotify on social media.
    Uses PullPush API (no auth needed).
    """
    posts = []
    subreddits = ["spotify", "truespotify", "music", "AppleMusic", "musicsuggestions"]
    queries = [
        "spotify recommendation",
        "spotify algorithm sucks",
        "spotify discover weekly",
        "spotify daily mix repetitive",
        "switching from spotify",
        "spotify ruined my taste",
    ]
    
    for subreddit in subreddits:
        for query in queries:
            try:
                url = "https://api.pullpush.io/reddit/search/submission/"
                params = {
                    "q": query,
                    "subreddit": subreddit,
                    "size": 25,
                    "sort": "desc",
                    "sort_type": "score",
                }
                response = requests.get(url, headers=HEADERS, params=params, timeout=30)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                items = data.get("data", [])
                
                for post in items:
                    if post.get("num_comments", 0) < 3:
                        continue
                    
                    title = post.get("title", "")
                    body = post.get("selftext", "")
                    text = f"{title}. {body}".strip() if body else title
                    
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    
                    created = post.get("created_utc", 0)
                    try:
                        created_str = datetime.fromtimestamp(int(created)).isoformat() if created else ""
                    except (ValueError, TypeError, OSError):
                        created_str = ""
                    
                    posts.append({
                        "id": f"reddit_social_{post.get('id', len(posts))}",
                        "source": "reddit_social",
                        "platform": "Reddit",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": post.get("author", "[deleted]"),
                        "created_utc": created_str,
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "type": "post"
                    })
                
                time.sleep(1.5)
            except Exception:
                continue
    
    return posts


# ============================================================
# METHOD 5: BLUESKY (Public API, no auth needed for search)
# ============================================================

def fetch_bluesky():
    """
    Search Bluesky for Spotify discussions.
    Uses public search API - no auth needed.
    """
    posts = []
    queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify shuffle",
        "spotify daily mix",
        "spotify playlist repetitive",
    ]
    
    for query in queries:
        try:
            url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 25}
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            
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
                
                # Convert AT URI to web URL
                # at://did:plc:xxx/app.bsky.feed.post/yyy → https://bsky.app/profile/handle/post/yyy
                post_id = uri.split("/")[-1] if uri else str(len(posts))
                web_url = f"https://bsky.app/profile/{handle}/post/{post_id}"
                
                posts.append({
                    "id": f"bluesky_{post_id}",
                    "source": "bluesky",
                    "platform": "Bluesky",
                    "query": query,
                    "title": f"Post by @{handle}",
                    "text": text,
                    "author": handle,
                    "created_utc": record.get("createdAt", ""),
                    "score": post.get("likeCount", 0),
                    "num_comments": post.get("replyCount", 0),
                    "url": web_url,
                    "type": "post"
                })
            
            time.sleep(1)
        except Exception as e:
            continue
    
    return posts


# ============================================================
# MAIN
# ============================================================

def main():
    print("📱 Social Media Scraper V2")
    print("Methods: Mastodon → Lemmy → Hacker News → Reddit → Bluesky")
    print("All public APIs, NO auth keys needed")
    print("=" * 60)
    
    all_posts = []
    
    # 1. Mastodon
    print("\n📡 Method 1: Mastodon (federated search)...")
    mastodon_posts = fetch_mastodon()
    if mastodon_posts:
        print(f"   ✅ {len(mastodon_posts)} posts from Mastodon")
        all_posts.extend(mastodon_posts)
    else:
        print("   ⚠️ No Mastodon results (some instances may block search)")
    
    # 2. Lemmy
    print("\n📡 Method 2: Lemmy (Reddit alternative)...")
    lemmy_posts = fetch_lemmy()
    if lemmy_posts:
        print(f"   ✅ {len(lemmy_posts)} posts from Lemmy")
        all_posts.extend(lemmy_posts)
    else:
        print("   ⚠️ No Lemmy results")
    
    # 3. Hacker News
    print("\n📡 Method 3: Hacker News (Algolia API)...")
    hn_posts = fetch_hackernews()
    if hn_posts:
        print(f"   ✅ {len(hn_posts)} posts from Hacker News")
        all_posts.extend(hn_posts)
    else:
        print("   ⚠️ No Hacker News results")
    
    # 4. Reddit social threads
    print("\n📡 Method 4: Reddit social threads (PullPush)...")
    reddit_posts = fetch_reddit_social()
    if reddit_posts:
        print(f"   ✅ {len(reddit_posts)} posts from Reddit")
        all_posts.extend(reddit_posts)
    else:
        print("   ⚠️ No Reddit social results")
    
    # 5. Bluesky
    print("\n📡 Method 5: Bluesky (public API)...")
    bluesky_posts = fetch_bluesky()
    if bluesky_posts:
        print(f"   ✅ {len(bluesky_posts)} posts from Bluesky")
        all_posts.extend(bluesky_posts)
    else:
        print("   ⚠️ No Bluesky results")
    
    # Deduplicate by text similarity (exact match)
    seen_texts = set()
    unique_posts = []
    for post in all_posts:
        text_key = post["text"][:100].lower().strip()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_posts.append(post)
    
    if not unique_posts:
        print("\n❌ No social data collected from any source.")
        print("   This may be a network issue. Try again later.")
        return
    
    df = pd.DataFrame(unique_posts)
    output_path = f"{RAW_DIR}/social_posts.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Social scraping complete: {len(unique_posts)} unique posts")
    print(f"   (Deduplicated from {len(all_posts)} raw)")
    print(f"📁 Saved: {output_path}")
    print(f"\n📊 Platform distribution:")
    print(df["platform"].value_counts().to_string())
    print(f"\n📊 Source distribution:")
    print(df["source"].value_counts().to_string())


if __name__ == "__main__":
    main()
