"""
Play Store Scraper - TURBO VERSION
Optimized for 2-day completion.

Run: python 3_playstore_scraper.py
Output: data/raw/playstore_reviews.csv
"""
from google_play_scraper import reviews, Sort
import pandas as pd
import time
import config_turbo as config

def fetch_playstore_reviews(app_id, country, count=300):
    try:
        result, _ = reviews(
            app_id,
            lang=config.PLAY_STORE_LANGUAGE,
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
        print(f"Error fetching Play Store reviews for {country}: {e}")
        return []

def main():
    print("🤖 TURBO Play Store Scraper")
    print(f"Countries: {config.PLAY_STORE_COUNTRIES}")
    print(f"Reviews per country: {config.PLAY_STORE_COUNT}")

    all_reviews = []

    for country in config.PLAY_STORE_COUNTRIES:
        print(f"\n📡 {country.upper()} Play Store...")
        reviews_data = fetch_playstore_reviews(config.PLAY_STORE_APP_ID, country, config.PLAY_STORE_COUNT)

        if reviews_data:
            print(f"   ✅ {len(reviews_data)} reviews")
            all_reviews.extend(reviews_data)
        else:
            print(f"   ❌ Failed")

        time.sleep(3)

    if not all_reviews:
        print("\n❌ No Play Store reviews collected.")
        return

    df = pd.DataFrame(all_reviews)
    output_path = f"{config.RAW_DIR}/playstore_reviews.csv"
    df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ Play Store complete: {len(all_reviews)} reviews")
    print(f"📁 Saved: {output_path}")
    print("\n📊 Rating distribution:")
    print(df["rating"].value_counts().sort_index().to_string())

if __name__ == "__main__":
    main()
