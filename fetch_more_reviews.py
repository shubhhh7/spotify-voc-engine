"""
Fetch Additional Reviews - App Store + Play Store
Fetches 700-800 NEW reviews from English-speaking countries,
avoiding duplicates with already-collected data.

Countries: gb, au, ca, nz, ie, za, in, sg, ph
(UK, Australia, Canada, New Zealand, Ireland, South Africa, India, Singapore, Philippines)

Run: python fetch_more_reviews.py
Output: Appends to data/raw/appstore_reviews.csv and data/raw/playstore_reviews.csv
"""
import requests
import pandas as pd
import time
from google_play_scraper import reviews, Sort
import config_turbo as config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# English-speaking countries (excluding US which we already have fully)
# gb is included since we want MORE from it beyond what we already fetched
EXTRA_COUNTRIES = ["au", "ca", "nz", "ie", "za", "in", "sg", "ph"]


# ============================================================
# APP STORE - iTunes RSS Feed
# ============================================================

def fetch_itunes_rss_reviews(app_id, country, page=1):
    """Fetch reviews using iTunes RSS feed (50 per page, max 10 pages)."""
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return []
        
        data = response.json()
        entries = data.get("feed", {}).get("entry", [])
        
        reviews_list = []
        for entry in entries:
            if "im:rating" not in entry:
                continue
            
            review_id = entry.get("id", {}).get("label", "")
            title = entry.get("title", {}).get("label", "")
            text = entry.get("content", {}).get("label", "")
            rating = int(entry.get("im:rating", {}).get("label", "0"))
            author = entry.get("author", {}).get("name", {}).get("label", "anonymous")
            version = entry.get("im:version", {}).get("label", "")
            vote_count = int(entry.get("im:voteCount", {}).get("label", "0"))
            date_str = entry.get("updated", {}).get("label", "")
            
            reviews_list.append({
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
        
        return reviews_list
    except Exception as e:
        print(f"      Error page {page}: {e}")
        return []


def fetch_appstore_country(app_id, country, target=150):
    """Fetch up to target reviews from a country."""
    all_reviews = []
    for page in range(1, 11):  # Max 10 pages
        batch = fetch_itunes_rss_reviews(app_id, country, page)
        if not batch:
            break
        all_reviews.extend(batch)
        if len(all_reviews) >= target:
            break
        time.sleep(0.8)
    return all_reviews[:target]


# ============================================================
# PLAY STORE
# ============================================================

def fetch_playstore_country(app_id, country, count=150):
    """Fetch Play Store reviews for a country."""
    try:
        result, _ = reviews(
            app_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=count,
            filter_score_with=None
        )
        
        review_list = []
        for review in result:
            review_list.append({
                "id": f"playstore_{country}_{review['reviewId']}",
                "source": "play_store",
                "country": country,
                "date": review.get("at", "").isoformat() if review.get("at") else "",
                "rating": review.get("score", 0),
                "title": "",
                "text": review.get("content", ""),
                "author": review.get("userName", "anonymous"),
                "version": review.get("reviewCreatedVersion", ""),
                "helpful_votes": review.get("thumbsUpCount", 0),
                "type": "review"
            })
        return review_list
    except Exception as e:
        print(f"   Error: {e}")
        return []


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("📥 FETCHING ADDITIONAL REVIEWS (700-800 each)")
    print("   Countries:", EXTRA_COUNTRIES)
    print("   Deduplicating against existing data")
    print("=" * 60)
    
    # Load existing data to deduplicate
    appstore_path = f"{config.RAW_DIR}/appstore_reviews.csv"
    playstore_path = f"{config.RAW_DIR}/playstore_reviews.csv"
    
    existing_appstore_ids = set()
    existing_playstore_ids = set()
    
    try:
        df_app = pd.read_csv(appstore_path)
        existing_appstore_ids = set(df_app["id"].tolist())
        print(f"\n📊 Existing App Store reviews: {len(df_app)}")
    except FileNotFoundError:
        df_app = pd.DataFrame()
        print("\n📊 No existing App Store file — starting fresh")
    
    try:
        df_play = pd.read_csv(playstore_path)
        existing_playstore_ids = set(df_play["id"].tolist())
        print(f"📊 Existing Play Store reviews: {len(df_play)}")
    except FileNotFoundError:
        df_play = pd.DataFrame()
        print("📊 No existing Play Store file — starting fresh")
    
    # ---- APP STORE ----
    print("\n" + "=" * 60)
    print("🍎 APP STORE - Fetching from new countries")
    print("=" * 60)
    
    new_appstore = []
    target_per_country_app = 800 // len(EXTRA_COUNTRIES) + 1  # ~100 per country
    
    for country in EXTRA_COUNTRIES:
        print(f"\n📡 {country.upper()} App Store...")
        batch = fetch_appstore_country(config.APP_STORE_APP_ID, country, target_per_country_app)
        
        # Deduplicate
        fresh = [r for r in batch if r["id"] not in existing_appstore_ids]
        
        if fresh:
            new_appstore.extend(fresh)
            print(f"   ✅ {len(fresh)} new reviews (skipped {len(batch) - len(fresh)} dupes)")
        else:
            print(f"   ⚠️ No new reviews")
        
        time.sleep(1.5)
        
        if len(new_appstore) >= 800:
            print(f"\n   🎯 Hit 800 target, stopping early")
            break
    
    # Save App Store
    if new_appstore:
        df_new_app = pd.DataFrame(new_appstore)
        df_combined_app = pd.concat([df_app, df_new_app], ignore_index=True)
        df_combined_app = df_combined_app.drop_duplicates(subset=["id"], keep="first")
        df_combined_app.to_csv(appstore_path, index=False)
        print(f"\n✅ App Store: Added {len(df_new_app)} new → Total {len(df_combined_app)} reviews")
        print(f"📁 Saved: {appstore_path}")
        print("\n📊 Country distribution:")
        print(df_combined_app["country"].value_counts().to_string())
    else:
        print("\n❌ No new App Store reviews collected")
    
    # ---- PLAY STORE ----
    print("\n" + "=" * 60)
    print("🤖 PLAY STORE - Fetching from new countries")
    print("=" * 60)
    
    new_playstore = []
    target_per_country_play = 800 // len(EXTRA_COUNTRIES) + 1
    
    for country in EXTRA_COUNTRIES:
        print(f"\n📡 {country.upper()} Play Store...")
        batch = fetch_playstore_country(config.PLAY_STORE_APP_ID, country, target_per_country_play)
        
        # Deduplicate
        fresh = [r for r in batch if r["id"] not in existing_playstore_ids]
        
        if fresh:
            new_playstore.extend(fresh)
            print(f"   ✅ {len(fresh)} new reviews (skipped {len(batch) - len(fresh)} dupes)")
        else:
            print(f"   ⚠️ No new reviews")
        
        time.sleep(2)
        
        if len(new_playstore) >= 800:
            print(f"\n   🎯 Hit 800 target, stopping early")
            break
    
    # Save Play Store
    if new_playstore:
        df_new_play = pd.DataFrame(new_playstore)
        df_combined_play = pd.concat([df_play, df_new_play], ignore_index=True)
        df_combined_play = df_combined_play.drop_duplicates(subset=["id"], keep="first")
        df_combined_play.to_csv(playstore_path, index=False)
        print(f"\n✅ Play Store: Added {len(df_new_play)} new → Total {len(df_combined_play)} reviews")
        print(f"📁 Saved: {playstore_path}")
        print("\n📊 Country distribution:")
        print(df_combined_play["country"].value_counts().to_string())
    else:
        print("\n❌ No new Play Store reviews collected")
    
    # ---- SUMMARY ----
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    print(f"   App Store new reviews:  {len(new_appstore)}")
    print(f"   Play Store new reviews: {len(new_playstore)}")
    print(f"   Total new reviews:      {len(new_appstore) + len(new_playstore)}")


if __name__ == "__main__":
    main()
