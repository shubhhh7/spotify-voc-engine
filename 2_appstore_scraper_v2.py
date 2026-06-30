"""
App Store Scraper V2 - ITUNES RSS + SCRAPING FALLBACK
Uses iTunes RSS feed (most reliable) + direct Apple API attempts.

The original app-store-scraper library often hits ConnectionResetError.
This version uses Apple's public RSS feeds which are more reliable.

Run: python 2_appstore_scraper_v2.py
Output: data/raw/appstore_reviews.csv
"""
import requests
import pandas as pd
import json
import time
from datetime import datetime
import config_turbo as config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_itunes_rss_reviews(app_id, country, page=1):
    """
    Fetch reviews using iTunes RSS feed.
    This is the MOST RELIABLE method - no auth needed.
    Returns up to 50 reviews per page (max 10 pages = 500 reviews).
    
    Endpoint: https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json
    """
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:
            print(f"      RSS page {page}: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        reviews = []
        entries = data.get("feed", {}).get("entry", [])
        
        # First entry is sometimes the app metadata, skip it
        for entry in entries:
            # Skip if it's app metadata (no rating)
            if "im:rating" not in entry:
                continue
            
            review_id = entry.get("id", {}).get("label", "")
            title = entry.get("title", {}).get("label", "")
            text = entry.get("content", {}).get("label", "")
            rating = int(entry.get("im:rating", {}).get("label", "0"))
            author = entry.get("author", {}).get("name", {}).get("label", "anonymous")
            version = entry.get("im:version", {}).get("label", "")
            vote_count = int(entry.get("im:voteCount", {}).get("label", "0"))
            
            # Parse date
            date_str = entry.get("updated", {}).get("label", "")
            
            reviews.append({
                "id": f"appstore_{country}_{review_id}",
                "source": "app_store",
                "country": country,
                "date": date_str,
                "rating": rating,
                "title": title,
                "text": text,
                "author": author,
                "version": version,
                "helpful_votes": vote_count,
                "type": "review"
            })
        
        return reviews
    
    except Exception as e:
        print(f"      RSS page {page} error: {e}")
        return []


def fetch_all_reviews_for_country(app_id, country, target_count=300):
    """Fetch multiple pages of RSS reviews for a country."""
    all_reviews = []
    max_pages = 10  # iTunes RSS supports up to 10 pages
    
    for page in range(1, max_pages + 1):
        reviews = fetch_itunes_rss_reviews(app_id, country, page)
        
        if not reviews:
            print(f"      Page {page}: No more reviews")
            break
        
        all_reviews.extend(reviews)
        print(f"      Page {page}: {len(reviews)} reviews (total: {len(all_reviews)})")
        
        if len(all_reviews) >= target_count:
            break
        
        time.sleep(1)  # Be polite
    
    return all_reviews[:target_count]


def main():
    print("🍎 App Store Scraper V2 (iTunes RSS Feed)")
    print(f"Countries: {config.APP_STORE_COUNTRIES}")
    print(f"Target reviews per country: {config.APP_STORE_COUNT}")
    print("=" * 60)
    
    all_reviews = []
    
    for country in config.APP_STORE_COUNTRIES:
        print(f"\n📡 {country.upper()} App Store (RSS feed)...")
        reviews = fetch_all_reviews_for_country(
            config.APP_STORE_APP_ID, country, config.APP_STORE_COUNT
        )
        
        if reviews:
            print(f"   ✅ {len(reviews)} reviews collected")
            all_reviews.extend(reviews)
        else:
            print(f"   ❌ No reviews from {country}")
        
        time.sleep(2)
    
    # Also try additional countries for more data
    extra_countries = ["au", "ca", "in"]
    for country in extra_countries:
        if len(all_reviews) >= 500:
            break
        print(f"\n📡 {country.upper()} App Store (bonus)...")
        reviews = fetch_all_reviews_for_country(
            config.APP_STORE_APP_ID, country, 100
        )
        if reviews:
            print(f"   ✅ {len(reviews)} reviews collected")
            all_reviews.extend(reviews)
        time.sleep(2)
    
    if not all_reviews:
        print("\n❌ No App Store reviews collected.")
        print("   Apple may be blocking requests from your network.")
        print("   Try again later or use a VPN.")
        return
    
    df = pd.DataFrame(all_reviews)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["id"], keep="first")
    
    output_path = f"{config.RAW_DIR}/appstore_reviews.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"✅ App Store complete: {len(df)} reviews")
    print(f"📁 Saved: {output_path}")
    print("\n📊 Rating distribution:")
    print(df["rating"].value_counts().sort_index().to_string())
    print("\n📊 Country distribution:")
    print(df["country"].value_counts().to_string())


if __name__ == "__main__":
    main()
