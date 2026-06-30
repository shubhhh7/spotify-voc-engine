"""
Reddit Scraper - NO API KEY VERSION
Uses Reddit's public JSON API (no authentication required)
Falls back to PullPush API if Reddit blocks requests.

This is the PRIMARY scraper. No Reddit app needed.
Run: python 1_reddit_scraper.py
Output: data/raw/reddit_posts.csv
"""
import requests
import pandas as pd
import time
import json
from datetime import datetime
from tqdm import tqdm
import config_turbo as config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_reddit_search_json(subreddit, query, limit=100, time_filter="year"):
    """
    Fetch search results from Reddit using public JSON API.
    No authentication required.

    Endpoint: https://www.reddit.com/r/{subreddit}/search.json
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "sort": "relevance",
        "t": time_filter,
        "limit": limit,
        "restrict_sr": "on"  # Restrict to subreddit
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)

        if response.status_code == 429:
            print(f"   ⚠️ Reddit rate limited. Waiting 30s...")
            time.sleep(30)
            return fetch_reddit_search_json(subreddit, query, limit, time_filter)

        if response.status_code == 403:
            print(f"   ⚠️ Reddit blocked request. Trying PullPush fallback...")
            return fetch_pullpush(subreddit, query, limit)

        response.raise_for_status()
        data = response.json()

        posts = []
        if "data" in data and "children" in data["data"]:
            for child in data["data"]["children"]:
                post = child["data"]

                # Skip low-engagement posts
                if post.get("num_comments", 0) < config.REDDIT_MIN_COMMENTS:
                    continue

                post_data = {
                    "id": f"reddit_{post['id']}",
                    "source": "reddit",
                    "subreddit": subreddit,
                    "query": query,
                    "title": post.get("title", ""),
                    "text": post.get("selftext", ""),
                    "author": post.get("author", "[deleted]"),
                    "created_utc": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat(),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "upvote_ratio": post.get("upvote_ratio", None),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "is_self": post.get("is_self", False),
                    "flair": post.get("link_flair_text", None),
                    "type": "post"
                }
                posts.append(post_data)

        return posts

    except Exception as e:
        print(f"   ❌ Reddit JSON API error: {e}")
        print(f"   🔄 Trying PullPush fallback...")
        return fetch_pullpush(subreddit, query, limit)

def fetch_pullpush(subreddit, query, limit=100):
    """
    Fallback: PullPush API (successor to Pushshift).
    Free, no authentication required.

    Endpoint: https://api.pullpush.io/reddit/search/submission/
    """
    url = "https://api.pullpush.io/reddit/search/submission/"
    params = {
        "q": query,
        "subreddit": subreddit,
        "size": min(limit, 100),
        "sort": "desc",
        "sort_type": "score"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        posts = []
        if "data" in data:
            for post in data["data"]:
                if post.get("num_comments", 0) < config.REDDIT_MIN_COMMENTS:
                    continue

                post_data = {
                    "id": f"reddit_{post['id']}",
                    "source": "reddit",
                    "subreddit": subreddit,
                    "query": query,
                    "title": post.get("title", ""),
                    "text": post.get("selftext", ""),
                    "author": post.get("author", "[deleted]"),
                    "created_utc": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat() if post.get("created_utc") else "",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "upvote_ratio": post.get("upvote_ratio", None),
                    "url": post.get("permalink", ""),
                    "is_self": post.get("is_self", False),
                    "flair": post.get("link_flair_text", None),
                    "type": "post"
                }
                posts.append(post_data)

        return posts

    except Exception as e:
        print(f"   ❌ PullPush API error: {e}")
        return []

def fetch_comments_json(post_id, subreddit, max_comments=15):
    """
    Fetch comments using Reddit JSON API.
    Endpoint: https://www.reddit.com/r/{subreddit}/comments/{post_id}.json
    """
    post_id_clean = post_id.replace("reddit_", "")
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id_clean}.json"

    try:
        response = requests.get(url, headers=HEADERS, params={"limit": max_comments}, timeout=30)

        if response.status_code in [429, 403]:
            return []  # Skip comments if blocked

        response.raise_for_status()
        data = response.json()

        comments = []
        if len(data) > 1 and "data" in data[1] and "children" in data[1]["data"]:
            for child in data[1]["data"]["children"]:
                if child["kind"] != "t1":  # Skip "more" comments
                    continue

                comment = child["data"]
                body = comment.get("body", "")

                if len(body) < config.MIN_TEXT_LENGTH:
                    continue

                comment_data = {
                    "id": f"reddit_comment_{comment['id']}",
                    "source": "reddit",
                    "subreddit": subreddit,
                    "query": "comment",
                    "title": f"Comment on post",
                    "text": body,
                    "author": comment.get("author", "[deleted]"),
                    "created_utc": datetime.fromtimestamp(comment.get("created_utc", 0)).isoformat() if comment.get("created_utc") else "",
                    "score": comment.get("score", 0),
                    "num_comments": 0,
                    "upvote_ratio": None,
                    "url": f"https://reddit.com{comment.get('permalink', '')}",
                    "is_self": True,
                    "flair": None,
                    "type": "comment",
                    "parent_post_id": post_id
                }
                comments.append(comment_data)

        return comments

    except Exception as e:
        return []

def main():
    print("🔴 Reddit Scraper - NO API KEY REQUIRED")
    print("Methods: Reddit JSON API → PullPush API fallback")
    print(f"Subreddits: {config.REDDIT_SUBREDDITS}")
    print(f"Queries: {len(config.REDDIT_SEARCH_QUERIES)}")
    print("="*60)

    all_posts = []
    all_comments = []
    total_queries = len(config.REDDIT_SUBREDDITS) * len(config.REDDIT_SEARCH_QUERIES)
    query_count = 0

    for subreddit in config.REDDIT_SUBREDDITS:
        for query in config.REDDIT_SEARCH_QUERIES:
            query_count += 1
            print(f"\n[{query_count}/{total_queries}] r/{subreddit} → '{query}'")

            posts = fetch_reddit_search_json(subreddit, query, config.REDDIT_POST_LIMIT)

            if posts:
                print(f"   ✅ {len(posts)} posts")
                all_posts.extend(posts)

                # Fetch comments for top 3 posts by score
                top_posts = sorted(posts, key=lambda x: x['score'], reverse=True)[:3]
                for post in top_posts:
                    time.sleep(1.5)
                    comments = fetch_comments_json(post["id"], subreddit, max_comments=config.REDDIT_COMMENTS_PER_POST)
                    all_comments.extend(comments)
                    if comments:
                        print(f"      💬 {len(comments)} comments")
            else:
                print(f"   ⚠️ No results")

            time.sleep(2)  # Be polite to Reddit

    all_data = all_posts + all_comments
    if not all_data:
        print("\n❌ No data collected. Check your internet connection.")
        print("   Try visiting https://www.reddit.com/r/spotify in your browser.")
        return

    df = pd.DataFrame(all_data)
    output_path = f"{config.RAW_DIR}/reddit_posts.csv"
    df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ Reddit complete: {len(all_posts)} posts + {len(all_comments)} comments = {len(all_data)} total")
    print(f"📁 Saved: {output_path}")

    print("\n📊 Top subreddits:")
    print(df['subreddit'].value_counts().head().to_string())
    print("\n📊 Top queries:")
    print(df['query'].value_counts().head().to_string())

    print("\n💡 TIP: If you got 0 results, Reddit may be blocking your IP.")
    print("   Try using a VPN or mobile hotspot, then re-run.")

if __name__ == "__main__":
    main()
