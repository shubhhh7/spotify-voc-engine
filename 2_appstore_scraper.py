"""
App Store Scraper - TURBO VERSION
Optimized for 2-day completion.

Run: python 2_appstore_scraper.py
Output: data/raw/appstore_reviews.csv
"""
from app_store_scraper import AppStore
import pandas as pd
import time
import config_turbo as config

def fetch_appstore_reviews(app_id, country, count=300):
    app = AppStore(country=country, app_id=app_id, app_name="spotify")

    try:
        app.review(how_many=count)

        reviews = []
        for review in app.reviews:
            reviews.append({
                "id": f"appstore_{country}_{review['reviewId']}",
                "source": "app_store",
                "country": country,
                "date": review.get("date", ""),
                "rating": review.get("rating", 0),
                "title": review.get("title", ""),
                "text": review.get("review", ""),
                "author": review.get("userName", "anonymous"),
                "version": review.get("version", ""),
                "helpful_votes": review.get("helpful", 0),
                "type": "review"
            })
        return reviews

    except Exception as e:
        print(f"Error fetching App Store reviews for {country}: {e}")
        return []

def main():
    print("🍎 TURBO App Store Scraper")
    print(f"Countries: {config.APP_STORE_COUNTRIES}")
    print(f"Reviews per country: {config.APP_STORE_COUNT}")

    all_reviews = []

    for country in config.APP_STORE_COUNTRIES:
        print(f"\n📡 {country.upper()} App Store...")
        reviews = fetch_appstore_reviews(config.APP_STORE_APP_ID, country, config.APP_STORE_COUNT)

        if reviews:
            print(f"   ✅ {len(reviews)} reviews")
            all_reviews.extend(reviews)
        else:
            print(f"   ❌ Failed")

        time.sleep(3)

    if not all_reviews:
        print("\n❌ No App Store reviews collected.")
        return

    df = pd.DataFrame(all_reviews)
    output_path = f"{config.RAW_DIR}/appstore_reviews.csv"
    df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ App Store complete: {len(all_reviews)} reviews")
    print(f"📁 Saved: {output_path}")
    print("\n📊 Rating distribution:")
    print(df["rating"].value_counts().sort_index().to_string())

if __name__ == "__main__":
    main()
