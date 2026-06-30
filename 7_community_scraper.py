"""
Community Forum Scraper for Spotify VoC Research
Scrapes Spotify Community forums and Reddit extras.
NO API keys required. Uses requests + BeautifulSoup.
"""
import requests
import pandas as pd
import time
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

MIN_TEXT_LENGTH = 25
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

QUERIES = [
    "discover new music", "recommendation algorithm", "playlist stuck same songs",
    "bored with spotify", "discovery weekly bad", "radio repetitive",
    "shuffle algorithm", "can't find new music", "recommendations terrible",
    "daily mix same", "on repeat stuck", "algorithm broken"
]

SUBREDDITS = ["spotify", "truespotify", "spotifywrapped", "WeAreTheMusicMakers", "music", "AppleMusic", "musicsuggestions"]


def fetch_spotify_community_search(query, max_pages=2):
    """Search Spotify Community forum via public pages."""
    posts = []
    base_url = "https://community.spotify.com/t5/forums/searchpage/tab/message"
    
    for page in range(1, max_pages + 1):
        params = {"q": query, "page": page, "scope": "community", "search_type": "thread"}
        try:
            response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
            if response.status_code != 200:
                break
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors since Spotify changes classes
            containers = soup.find_all('div', class_=re.compile('lia-message')) \
                        or soup.find_all('div', class_=re.compile('MessageView')) \
                        or soup.find_all('tr', class_=re.compile('lia-data-row'))
            
            for container in containers:
                try:
                    title_elem = container.find('a', class_=re.compile('lia-message-subject')) \
                              or container.find('a', class_=re.compile('subject'))
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    
                    text_elem = container.find('div', class_=re.compile('lia-message-body')) \
                             or container.find('div', class_=re.compile('body'))
                    text = text_elem.get_text(strip=True) if text_elem else ""
                    
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    
                    url = ""
                    if title_elem and title_elem.get('href'):
                        href = title_elem.get('href')
                        url = href if href.startswith('http') else f"https://community.spotify.com{href}"
                    
                    author_elem = container.find('a', class_=re.compile('lia-user-name'))
                    author = author_elem.get_text(strip=True) if author_elem else "anonymous"
                    
                    date_elem = container.find('span', class_=re.compile('local-date'))
                    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
                    
                    replies_elem = container.find('span', class_=re.compile('reply-count'))
                    replies = int(re.search(r'\d+', replies_elem.get_text(strip=True)).group()) if replies_elem else 0
                    
                    posts.append({
                        "id": f"spotify_community_{len(posts)}",
                        "source": "spotify_community",
                        "forum": "Spotify Community",
                        "query": query,
                        "title": title,
                        "text": text,
                        "author": author,
                        "created_utc": date_str,
                        "score": replies,
                        "num_comments": replies,
                        "url": url,
                        "type": "post"
                    })
                except Exception:
                    continue
            
            print(f"   Page {page}: {len(containers)} found, {len([p for p in posts if p['query']==query])} extracted")
            if not containers:
                break
            time.sleep(2)
        except Exception as e:
            print(f"   Error page {page}: {e}")
            break
    return posts


def fetch_reddit_extra():
    """Fetch additional Reddit subreddits not covered by main scraper."""
    extra_subreddits = ["spotifytweaks", "spotifyplaylist", "musicproduction", "headphones", "audiophile"]
    extra_queries = ["spotify discovery", "spotify recommendations", "spotify algorithm", "spotify playlist"]
    posts = []
    
    for subreddit in extra_subreddits:
        for query in extra_queries:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "sort": "relevance", "t": "year", "limit": 25, "restrict_sr": "on"}
            try:
                response = requests.get(url, headers=HEADERS, params=params, timeout=15)
                if response.status_code == 429:
                    time.sleep(30)
                    continue
                if response.status_code != 200:
                    continue
                data = response.json()
                if "data" in data and "children" in data["data"]:
                    for child in data["data"]["children"]:
                        post = child["data"]
                        if post.get("num_comments", 0) < 3:
                            continue
                        posts.append({
                            "id": f"reddit_extra_{post['id']}",
                            "source": "reddit_extra",
                            "forum": f"r/{subreddit}",
                            "query": query,
                            "title": post.get("title", ""),
                            "text": post.get("selftext", ""),
                            "author": post.get("author", "[deleted]"),
                            "created_utc": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat() if post.get("created_utc") else "",
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "type": "post"
                        })
                time.sleep(1.5)
            except Exception:
                continue
    return posts


def main():
    print("🏛️ Community Forum Scraper")
    print("Sources: Spotify Community + Reddit extras")
    print("=" * 60)
    
    all_posts = []
    
    # 1. Spotify Community
    print("\n📡 Spotify Community Forum...")
    for query in QUERIES[:5]:
        print(f"   Searching: '{query}'")
        posts = fetch_spotify_community_search(query, max_pages=2)
        if posts:
            print(f"   ✅ {len(posts)} posts")
            all_posts.extend(posts)
        time.sleep(3)
    
    # 2. Reddit extras
    print("\n📡 Additional Reddit subreddits...")
    extra_posts = fetch_reddit_extra()
    if extra_posts:
        print(f"   ✅ {len(extra_posts)} posts from extra subreddits")
        all_posts.extend(extra_posts)
    
    if not all_posts:
        print("\n⚠️ No community forum data collected. This is supplementary — move on.")
        return
    
    df = pd.DataFrame(all_posts)
    output_path = f"{RAW_DIR}/community_posts.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Community complete: {len(all_posts)} posts")
    print(f"📁 Saved: {output_path}")
    print("\n📊 Source distribution:")
    print(df['source'].value_counts().to_string())


if __name__ == "__main__":
    main()