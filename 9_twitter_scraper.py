"""
Twitter/X Scraper for Spotify VoC Research - FREE (No API Key)
================================================================
Collects Twitter/X discussions about Spotify music discovery using
FREE methods that require NO API keys:

  1. Nitter Instances (public Twitter mirrors with RSS/search)
  2. Google Search (site:twitter.com OR site:x.com scraping)
  3. Wayback Machine / Common Crawl (archived tweets)
  4. Twscrape (lightweight Twitter scraping via guest tokens)

Research Questions Targeted:
  - Why do users struggle to discover new music?
  - What are the most common frustrations with recommendations?
  - What listening behaviors are users trying to achieve?
  - What causes users to repeatedly listen to the same content?
  - Which user segments experience different discovery challenges?
  - What unmet needs emerge consistently across reviews?

Run: pip install beautifulsoup4 lxml twscrape
     python 9_twitter_scraper.py
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
    print("⚠️  Install beautifulsoup4: pip install beautifulsoup4 lxml")

try:
    import twscrape
    import asyncio
    TWSCRAPE_AVAILABLE = True
except ImportError:
    TWSCRAPE_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

MIN_TEXT_LENGTH = 30
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

# Search queries mapped to our 6 research questions
TWITTER_QUERIES = [
    # Q1: Why do users struggle to discover new music?
    "spotify discover new music struggle",
    "spotify can't find new music",
    "spotify discovery is broken",
    "spotify won't show me new artists",
    # Q2: Common frustrations with recommendations
    "spotify recommendations terrible",
    "spotify algorithm sucks",
    "spotify recommend same songs",
    "spotify suggestions bad",
    "spotify recommendation frustrating",
    # Q3: Listening behaviors users want to achieve
    "spotify want to explore new genres",
    "spotify trying to find music like",
    "spotify mood playlist doesn't work",
    # Q4: Repeated content causes
    "spotify keeps playing same songs",
    "spotify stuck in loop",
    "spotify daily mix repetitive",
    "spotify on repeat same artist",
    "spotify shuffle not random",
    # Q5: User segment challenges
    "spotify free vs premium discovery",
    "spotify new user recommendations",
    "spotify indie music discovery",
    # Q6: Unmet needs
    "spotify needs better discovery",
    "spotify should add feature",
    "spotify missing feature discovery",
    "switching from spotify to",
]


# ============================================================
# METHOD 1: NITTER INSTANCES (Public Twitter Mirrors)
# ============================================================

def fetch_nitter():
    """
    Scrape Nitter instances for Twitter/X posts about Spotify.
    Nitter provides public access to tweets without authentication.
    Some instances may be down - we try multiple.
    """
    if not BS4_AVAILABLE:
        print("   ⚠️ beautifulsoup4 not installed, skipping Nitter")
        return []

    posts = []
    # Active Nitter instances (updated list - try multiple)
    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.woodland.cafe",
        "https://nitter.1d4.us",
        "https://nitter.kavin.rocks",
        "https://xcancel.com",
    ]

    queries = [
        "spotify algorithm",
        "spotify recommendations bad",
        "spotify discovery broken",
        "spotify same songs",
        "spotify shuffle terrible",
        "spotify daily mix repetitive",
        "spotify discover weekly disappointed",
        "spotify stuck same artists",
        "spotify music discovery",
        "spotify new music frustrating",
    ]

    working_instance = None

    for instance in nitter_instances:
        try:
            test_url = f"{instance}/search?q=spotify&f=tweets"
            resp = requests.get(test_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200 and "timeline" in resp.text.lower():
                working_instance = instance
                print(f"   ✅ Found working Nitter instance: {instance}")
                break
        except Exception:
            continue

    if not working_instance:
        print("   ⚠️ No working Nitter instances found")
        return []

    for query in tqdm(queries, desc="   Nitter search"):
        try:
            search_url = f"{working_instance}/search?q={quote_plus(query)}&f=tweets"
            response = requests.get(search_url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Nitter tweet containers
            tweet_elements = soup.select(".timeline-item, .tweet-body, .timeline .tweet")

            for tweet_el in tweet_elements:
                # Extract tweet text
                content_el = tweet_el.select_one(
                    ".tweet-content, .tweet-body .tweet-text, .content"
                )
                if not content_el:
                    continue

                text = content_el.get_text(strip=True)
                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue

                # Extract metadata
                username_el = tweet_el.select_one(
                    ".username, .tweet-header .username, a[href*='/']"
                )
                username = username_el.get_text(strip=True) if username_el else "unknown"
                username = username.lstrip("@")

                date_el = tweet_el.select_one(".tweet-date a, time, .tweet-published")
                date_str = ""
                if date_el:
                    date_str = date_el.get("title", "") or date_el.get_text(strip=True)

                stats_el = tweet_el.select(".icon-container, .tweet-stat")
                likes = 0
                replies = 0
                for stat in stats_el:
                    stat_text = stat.get_text(strip=True)
                    if "like" in stat_text.lower() or "♥" in stat_text:
                        likes = _extract_number(stat_text)
                    elif "repl" in stat_text.lower() or "💬" in stat_text:
                        replies = _extract_number(stat_text)

                # Build URL
                link_el = tweet_el.select_one("a[href*='/status/']")
                tweet_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    tweet_url = f"https://twitter.com{href}" if href.startswith("/") else href

                posts.append({
                    "id": f"twitter_nitter_{len(posts)}",
                    "source": "twitter_nitter",
                    "platform": "Twitter/X",
                    "query": query,
                    "title": f"Tweet by @{username}",
                    "text": text,
                    "author": username,
                    "created_utc": date_str,
                    "score": likes,
                    "num_comments": replies,
                    "url": tweet_url,
                    "type": "tweet",
                })

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            continue

    return posts


# ============================================================
# METHOD 2: GOOGLE SEARCH (site:twitter.com / site:x.com)
# ============================================================

def fetch_google_twitter():
    """
    Use Google search to find Twitter/X posts about Spotify.
    Searches for site:twitter.com OR site:x.com results.
    No API key needed - uses web scraping.
    """
    if not BS4_AVAILABLE:
        print("   ⚠️ beautifulsoup4 not installed, skipping Google search")
        return []

    posts = []
    queries = [
        'site:twitter.com OR site:x.com "spotify algorithm" frustrating',
        'site:twitter.com OR site:x.com "spotify recommendations" bad',
        'site:twitter.com OR site:x.com "spotify discovery" broken',
        'site:twitter.com OR site:x.com "spotify" "same songs" over and over',
        'site:twitter.com OR site:x.com "spotify shuffle" terrible',
        'site:twitter.com OR site:x.com "spotify daily mix" repetitive',
        'site:twitter.com OR site:x.com "spotify" "discover weekly" disappointed',
        'site:twitter.com OR site:x.com "spotify" "new music" struggle',
        'site:twitter.com OR site:x.com "spotify" keeps recommending same',
        'site:twitter.com OR site:x.com "switching from spotify" discovery',
    ]

    google_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for query in tqdm(queries, desc="   Google site:twitter.com"):
        try:
            url = f"https://www.google.com/search?q={quote_plus(query)}&num=20"
            response = requests.get(url, headers=google_headers, timeout=15)

            if response.status_code != 200:
                time.sleep(random.uniform(5, 10))
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Google search result containers
            result_divs = soup.select("div.g, div[data-sokoban-container]")

            for div in result_divs:
                link_el = div.select_one("a[href]")
                if not link_el:
                    continue

                href = link_el.get("href", "")
                if "twitter.com" not in href and "x.com" not in href:
                    continue
                if "/status/" not in href:
                    continue

                # Extract snippet text (Google's preview of the tweet)
                snippet_el = div.select_one(
                    "div.VwiC3b, span.aCOpRe, div[data-sncf], .IsZvec"
                )
                text = snippet_el.get_text(strip=True) if snippet_el else ""

                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue

                # Extract username from URL
                username = _extract_twitter_username(href)

                # Extract date if available
                date_el = div.select_one("span.MUxGbd, .f")
                date_str = date_el.get_text(strip=True) if date_el else ""

                posts.append({
                    "id": f"twitter_google_{len(posts)}",
                    "source": "twitter_google",
                    "platform": "Twitter/X",
                    "query": query.replace("site:twitter.com OR site:x.com ", ""),
                    "title": f"Tweet by @{username}",
                    "text": text,
                    "author": username,
                    "created_utc": date_str,
                    "score": 0,
                    "num_comments": 0,
                    "url": href,
                    "type": "tweet",
                })

            # Be respectful to Google
            time.sleep(random.uniform(8, 15))
        except Exception as e:
            continue

    return posts


# ============================================================
# METHOD 3: WAYBACK MACHINE / WEB ARCHIVE
# ============================================================

def fetch_wayback_twitter():
    """
    Search the Wayback Machine CDX API for archived Twitter pages
    about Spotify. Completely free, no auth needed.
    """
    posts = []
    # Search for archived Twitter URLs containing our keywords
    search_terms = [
        "spotify+algorithm",
        "spotify+recommendations",
        "spotify+discovery",
        "spotify+shuffle+terrible",
        "spotify+daily+mix",
        "spotify+same+songs",
    ]

    for term in tqdm(search_terms, desc="   Wayback Machine"):
        try:
            # CDX API - search for Twitter URLs with matching content
            cdx_url = (
                f"https://web.archive.org/cdx/search/cdx?"
                f"url=twitter.com/*/status/*&"
                f"matchType=prefix&"
                f"output=json&"
                f"limit=30&"
                f"fl=original,timestamp,statuscode&"
                f"filter=statuscode:200&"
                f"filter=original:.*{term}.*"
            )
            response = requests.get(cdx_url, headers=HEADERS, timeout=20)

            if response.status_code != 200:
                continue

            data = response.json()
            if len(data) < 2:  # First row is headers
                continue

            headers_row = data[0]
            for row in data[1:15]:  # Limit to 15 results per term
                if len(row) < 3:
                    continue

                original_url = row[0]
                timestamp = row[1]

                # Fetch the archived page
                archive_url = f"https://web.archive.org/web/{timestamp}/{original_url}"

                try:
                    page_resp = requests.get(archive_url, headers=HEADERS, timeout=15)
                    if page_resp.status_code != 200:
                        continue

                    if BS4_AVAILABLE:
                        soup = BeautifulSoup(page_resp.text, "lxml")
                        # Try to extract tweet text from archived page
                        tweet_text_el = soup.select_one(
                            '[data-testid="tweetText"], .tweet-text, '
                            ".js-tweet-text, .TweetTextSize"
                        )
                        if tweet_text_el:
                            text = tweet_text_el.get_text(strip=True)
                        else:
                            # Fallback: get meta description
                            meta = soup.select_one(
                                'meta[property="og:description"], '
                                'meta[name="description"]'
                            )
                            text = meta.get("content", "") if meta else ""
                    else:
                        # Regex fallback
                        match = re.search(
                            r'content="([^"]*spotify[^"]*)"',
                            page_resp.text,
                            re.IGNORECASE,
                        )
                        text = match.group(1) if match else ""

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    username = _extract_twitter_username(original_url)

                    # Parse timestamp
                    try:
                        dt = datetime.strptime(timestamp[:14], "%Y%m%d%H%M%S")
                        date_str = dt.isoformat()
                    except (ValueError, TypeError):
                        date_str = ""

                    posts.append({
                        "id": f"twitter_wayback_{len(posts)}",
                        "source": "twitter_wayback",
                        "platform": "Twitter/X",
                        "query": term.replace("+", " "),
                        "title": f"Tweet by @{username} (archived)",
                        "text": text,
                        "author": username,
                        "created_utc": date_str,
                        "score": 0,
                        "num_comments": 0,
                        "url": original_url,
                        "type": "tweet",
                    })

                except Exception:
                    continue

            time.sleep(2)
        except Exception as e:
            continue

    return posts


# ============================================================
# METHOD 4: TWSCRAPE (Guest Token Method - No Login)
# ============================================================

async def fetch_twscrape():
    """
    Use twscrape library with guest tokens to search Twitter.
    This uses Twitter's own search without requiring login credentials.
    Requires: pip install twscrape
    """
    if not TWSCRAPE_AVAILABLE:
        print("   ⚠️ twscrape not installed (pip install twscrape), skipping")
        return []

    posts = []
    queries = [
        "spotify algorithm frustrating",
        "spotify recommendations bad",
        "spotify discovery broken",
        "spotify same songs repeat",
        "spotify shuffle not random",
        "spotify daily mix boring",
        "spotify discover weekly terrible",
        "spotify stuck same music",
    ]

    try:
        api = twscrape.API()

        for query in tqdm(queries, desc="   Twscrape"):
            try:
                tweets = []
                async for tweet in api.search(query, limit=20):
                    tweets.append(tweet)

                for tweet in tweets:
                    text = tweet.rawContent if hasattr(tweet, "rawContent") else str(tweet)

                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    username = tweet.user.username if hasattr(tweet, "user") else "unknown"

                    posts.append({
                        "id": f"twitter_twscrape_{tweet.id}",
                        "source": "twitter_twscrape",
                        "platform": "Twitter/X",
                        "query": query,
                        "title": f"Tweet by @{username}",
                        "text": text,
                        "author": username,
                        "created_utc": tweet.date.isoformat() if hasattr(tweet, "date") else "",
                        "score": tweet.likeCount if hasattr(tweet, "likeCount") else 0,
                        "num_comments": tweet.replyCount if hasattr(tweet, "replyCount") else 0,
                        "url": f"https://twitter.com/{username}/status/{tweet.id}",
                        "type": "tweet",
                    })

                time.sleep(2)
            except Exception as e:
                continue

    except Exception as e:
        print(f"   ⚠️ Twscrape initialization failed: {e}")

    return posts


# ============================================================
# METHOD 5: SYNDICATION API (Twitter's Public Embed Endpoint)
# ============================================================

def fetch_twitter_syndication():
    """
    Use Twitter's public syndication/embed API to fetch tweet content.
    This endpoint is used by Twitter's embed widgets and doesn't need auth.
    We use it to fetch tweets from known viral threads about Spotify.
    """
    posts = []

    # Known viral tweet IDs about Spotify (curated list)
    # These are publicly shared tweets that discuss Spotify discovery issues
    # You can add more IDs from tweets you find in Google searches
    known_tweet_urls = [
        # These are example tweet patterns - the script will try to fetch them
        # Format: (username, tweet_id)
    ]

    # Search for tweets via Twitter's publish endpoint
    search_queries = [
        "spotify algorithm",
        "spotify recommendations",
        "spotify discovery",
        "spotify playlist repetitive",
        "spotify shuffle broken",
    ]

    for query in tqdm(search_queries, desc="   Twitter Syndication"):
        try:
            # Twitter's syndication search (used by embeds)
            url = "https://syndication.twitter.com/srv/timeline-profile/screen-name/SpotifyCares"
            params = {"showReplies": "true"}
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                continue

            if BS4_AVAILABLE:
                soup = BeautifulSoup(response.text, "lxml")
                tweet_articles = soup.select("article, .timeline-Tweet")

                for article in tweet_articles:
                    text_el = article.select_one(
                        ".timeline-Tweet-text, p, .tweet-text"
                    )
                    if not text_el:
                        continue

                    text = text_el.get_text(strip=True)
                    if len(text) < MIN_TEXT_LENGTH:
                        continue
                    if "spotify" not in text.lower():
                        continue

                    posts.append({
                        "id": f"twitter_syndication_{len(posts)}",
                        "source": "twitter_syndication",
                        "platform": "Twitter/X",
                        "query": query,
                        "title": "SpotifyCares reply",
                        "text": text,
                        "author": "SpotifyCares",
                        "created_utc": "",
                        "score": 0,
                        "num_comments": 0,
                        "url": "https://twitter.com/SpotifyCares",
                        "type": "tweet",
                    })

            time.sleep(2)
        except Exception:
            continue

    # Also try to fetch from Twitter's oembed (public endpoint)
    # This works for individual tweet URLs found via Google
    return posts


# ============================================================
# METHOD 6: BING SEARCH (Alternative to Google)
# ============================================================

def fetch_bing_twitter():
    """
    Use Bing search as fallback for finding Twitter/X posts.
    Bing is less aggressive with bot detection than Google.
    """
    if not BS4_AVAILABLE:
        return []

    posts = []
    queries = [
        'site:twitter.com "spotify" "algorithm" "terrible"',
        'site:twitter.com "spotify" "recommendations" "bad"',
        'site:twitter.com "spotify" "discover weekly" "same"',
        'site:twitter.com "spotify" "shuffle" broken',
        'site:x.com "spotify" "algorithm" frustrating',
        'site:x.com "spotify" "discovery" "new music"',
        'site:x.com "spotify" "daily mix" "repetitive"',
        'site:x.com "spotify" "keeps playing" same',
    ]

    bing_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    for query in tqdm(queries, desc="   Bing site:twitter.com"):
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count=15"
            response = requests.get(url, headers=bing_headers, timeout=15)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")
            results = soup.select("li.b_algo, .b_algo")

            for result in results:
                link_el = result.select_one("a[href]")
                if not link_el:
                    continue

                href = link_el.get("href", "")
                if "twitter.com" not in href and "x.com" not in href:
                    continue
                if "/status/" not in href:
                    continue

                snippet_el = result.select_one(".b_caption p, .b_lineclamp2")
                text = snippet_el.get_text(strip=True) if snippet_el else ""

                if len(text) < MIN_TEXT_LENGTH:
                    continue
                if "spotify" not in text.lower():
                    continue

                username = _extract_twitter_username(href)

                posts.append({
                    "id": f"twitter_bing_{len(posts)}",
                    "source": "twitter_bing",
                    "platform": "Twitter/X",
                    "query": query.replace("site:twitter.com ", "").replace(
                        "site:x.com ", ""
                    ),
                    "title": f"Tweet by @{username}",
                    "text": text,
                    "author": username,
                    "created_utc": "",
                    "score": 0,
                    "num_comments": 0,
                    "url": href,
                    "type": "tweet",
                })

            time.sleep(random.uniform(5, 10))
        except Exception:
            continue

    return posts


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _extract_number(text):
    """Extract first number from text."""
    match = re.search(r"(\d+[.,]?\d*)", text.replace(",", ""))
    if match:
        try:
            return int(float(match.group(1)))
        except ValueError:
            return 0
    return 0


def _extract_twitter_username(url):
    """Extract Twitter username from URL."""
    # Patterns: twitter.com/username/status/... or x.com/username/status/...
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status", url)
    if match:
        return match.group(1)
    return "unknown"


def _clean_text(text):
    """Clean tweet text."""
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove common artifacts
    text = re.sub(r"^\.\.\.", "", text)
    text = re.sub(r"\.\.\.$", "", text)
    return text.strip()


def _categorize_tweet(text):
    """
    Categorize tweet by research question for easier analysis later.
    Returns a tag indicating which research question the tweet maps to.
    """
    text_lower = text.lower()

    if any(w in text_lower for w in ["discover", "find new", "explore", "new music"]):
        return "discovery_struggle"
    elif any(w in text_lower for w in ["recommend", "algorithm", "suggestion"]):
        return "recommendation_frustration"
    elif any(w in text_lower for w in ["mood", "vibe", "want to listen", "trying to"]):
        return "listening_behavior"
    elif any(w in text_lower for w in ["same", "repeat", "loop", "stuck", "over and over"]):
        return "repetition_cause"
    elif any(w in text_lower for w in ["free", "premium", "new user", "indie", "niche"]):
        return "segment_challenge"
    elif any(w in text_lower for w in ["need", "should", "wish", "missing", "switch"]):
        return "unmet_need"
    else:
        return "general"


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    print("🐦 Twitter/X Scraper for Spotify VoC Research")
    print("=" * 60)
    print("Methods: Nitter → Google → Wayback → Twscrape → Syndication → Bing")
    print("All FREE - No API keys required")
    print("=" * 60)

    all_posts = []

    # Method 1: Nitter
    print("\n📡 Method 1: Nitter Instances (Twitter mirrors)...")
    nitter_posts = fetch_nitter()
    if nitter_posts:
        print(f"   ✅ {len(nitter_posts)} tweets from Nitter")
        all_posts.extend(nitter_posts)
    else:
        print("   ⚠️ No Nitter results (mirrors may be down)")

    # Method 2: Google Search
    print("\n📡 Method 2: Google Search (site:twitter.com)...")
    google_posts = fetch_google_twitter()
    if google_posts:
        print(f"   ✅ {len(google_posts)} tweets from Google")
        all_posts.extend(google_posts)
    else:
        print("   ⚠️ No Google results (may be rate limited)")

    # Method 3: Wayback Machine
    print("\n📡 Method 3: Wayback Machine (archived tweets)...")
    wayback_posts = fetch_wayback_twitter()
    if wayback_posts:
        print(f"   ✅ {len(wayback_posts)} tweets from Wayback Machine")
        all_posts.extend(wayback_posts)
    else:
        print("   ⚠️ No Wayback results")

    # Method 4: Twscrape
    print("\n📡 Method 4: Twscrape (guest token)...")
    if TWSCRAPE_AVAILABLE:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            twscrape_posts = loop.run_until_complete(fetch_twscrape())
            loop.close()
            if twscrape_posts:
                print(f"   ✅ {len(twscrape_posts)} tweets from Twscrape")
                all_posts.extend(twscrape_posts)
            else:
                print("   ⚠️ No Twscrape results")
        except Exception as e:
            print(f"   ⚠️ Twscrape failed: {e}")
    else:
        print("   ⚠️ Twscrape not installed (pip install twscrape)")

    # Method 5: Twitter Syndication
    print("\n📡 Method 5: Twitter Syndication API...")
    syndication_posts = fetch_twitter_syndication()
    if syndication_posts:
        print(f"   ✅ {len(syndication_posts)} tweets from Syndication")
        all_posts.extend(syndication_posts)
    else:
        print("   ⚠️ No Syndication results")

    # Method 6: Bing Search
    print("\n📡 Method 6: Bing Search (site:twitter.com)...")
    bing_posts = fetch_bing_twitter()
    if bing_posts:
        print(f"   ✅ {len(bing_posts)} tweets from Bing")
        all_posts.extend(bing_posts)
    else:
        print("   ⚠️ No Bing results")

    # ============================================================
    # POST-PROCESSING
    # ============================================================
    print(f"\n{'=' * 60}")
    print("🔄 Post-processing...")

    if not all_posts:
        print("\n❌ No Twitter data collected from any method.")
        print("   Possible reasons:")
        print("   - Network/firewall blocking requests")
        print("   - All Nitter instances are down")
        print("   - Search engines detected bot activity")
        print("\n💡 Tip: Try running again later, or use the manual guide:")
        print("   See data/final/manual_twitter_search_guide.txt")
        _generate_manual_guide()
        return

    # Clean text
    for post in all_posts:
        post["text"] = _clean_text(post["text"])

    # Deduplicate by text similarity
    seen_texts = set()
    unique_posts = []
    for post in all_posts:
        # Use first 80 chars as dedup key
        text_key = post["text"][:80].lower().strip()
        if text_key not in seen_texts and len(post["text"]) >= MIN_TEXT_LENGTH:
            seen_texts.add(text_key)
            unique_posts.append(post)

    # Add research category
    for post in unique_posts:
        post["research_category"] = _categorize_tweet(post["text"])

    # Save to CSV
    df = pd.DataFrame(unique_posts)
    output_path = f"{RAW_DIR}/twitter_posts.csv"
    df.to_csv(output_path, index=False)

    print(f"\n✅ Twitter scraping complete: {len(unique_posts)} unique tweets")
    print(f"   (Deduplicated from {len(all_posts)} raw)")
    print(f"📁 Saved: {output_path}")
    print(f"\n📊 Source distribution:")
    print(df["source"].value_counts().to_string())
    print(f"\n📊 Research category distribution:")
    print(df["research_category"].value_counts().to_string())

    # Also generate manual guide as backup
    _generate_manual_guide()
    print(f"\n📋 Manual search guide also saved to: data/final/manual_twitter_search_guide.txt")


# ============================================================
# MANUAL GUIDE (FALLBACK)
# ============================================================

def _generate_manual_guide():
    """
    Generate a manual search guide for Twitter in case automated methods fail.
    Users can manually copy-paste results into a CSV.
    """
    guide = """
============================================================
MANUAL TWITTER/X SEARCH GUIDE - Spotify VoC Research
============================================================

If the automated scraper couldn't collect enough data, use these
search queries directly on Twitter/X to find relevant discussions.

SEARCH URLS (open in browser):
============================================================

Q1: Why do users struggle to discover new music?
- https://x.com/search?q=spotify%20discover%20new%20music%20struggle&f=live
- https://x.com/search?q=spotify%20can%27t%20find%20new%20music&f=live
- https://x.com/search?q=%22spotify%20discovery%22%20broken&f=live

Q2: Common frustrations with recommendations?
- https://x.com/search?q=spotify%20recommendations%20terrible&f=live
- https://x.com/search?q=spotify%20algorithm%20sucks&f=live
- https://x.com/search?q=spotify%20suggestions%20bad&f=live

Q3: What listening behaviors are users trying to achieve?
- https://x.com/search?q=spotify%20want%20explore%20new%20genres&f=live
- https://x.com/search?q=spotify%20mood%20playlist%20doesn%27t%20work&f=live
- https://x.com/search?q=%22spotify%22%20%22trying%20to%20find%22%20music&f=live

Q4: What causes repeated listening to same content?
- https://x.com/search?q=spotify%20keeps%20playing%20same%20songs&f=live
- https://x.com/search?q=spotify%20stuck%20in%20loop&f=live
- https://x.com/search?q=spotify%20daily%20mix%20repetitive&f=live
- https://x.com/search?q=spotify%20shuffle%20not%20random&f=live

Q5: User segment discovery challenges?
- https://x.com/search?q=spotify%20free%20vs%20premium%20discovery&f=live
- https://x.com/search?q=spotify%20new%20user%20recommendations&f=live
- https://x.com/search?q=spotify%20indie%20music%20discovery&f=live

Q6: What unmet needs emerge?
- https://x.com/search?q=spotify%20needs%20better%20discovery&f=live
- https://x.com/search?q=switching%20from%20spotify&f=live
- https://x.com/search?q=spotify%20should%20add%20feature&f=live

============================================================
HOW TO MANUALLY COLLECT:
============================================================
1. Open URLs above in your browser (logged in to X)
2. Copy interesting tweets into a spreadsheet with columns:
   text, author, date, likes, url
3. Save as data/raw/twitter_posts_manual.csv
4. The analysis pipeline (5_gemini_analyzer.py) will pick it up

TIP: Sort by "Top" instead of "Latest" for most relevant tweets
============================================================
"""
    guide_path = "data/final/manual_twitter_search_guide.txt"
    with open(guide_path, "w") as f:
        f.write(guide)


if __name__ == "__main__":
    main()
