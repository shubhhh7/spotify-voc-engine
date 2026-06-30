"""Phase 2 verification script."""
import sys

print("=" * 60)
print("PHASE 2 — FULL VERIFICATION")
print("=" * 60)

errors = []

# 1. All scraper modules import
print("\n[1/6] Scraper imports...")
try:
    from scrapers.base import BaseScraper, ScraperResult
    from scrapers.reddit_scraper import RedditScraper
    from scrapers.appstore_scraper import AppStoreScraper
    from scrapers.playstore_scraper import PlayStoreScraper
    from scrapers.community_scraper import CommunityScraper
    from scrapers.social_scraper import SocialScraper
    print("  ✅ All 5 scraper modules import")
except Exception as e:
    errors.append(f"Scraper import: {e}")
    print(f"  ❌ {e}")

# 2. Service layer imports
print("\n[2/6] Service layer imports...")
try:
    from services.scraper_service import SCRAPER_REGISTRY, scrape_state, execute_scrapers
    from services.cleaning_service import (
        clean_text, classify_sentiment_simple,
        compute_quality_score, classify_relevance
    )
    assert len(SCRAPER_REGISTRY) == 5
    print(f"  ✅ scraper_service ({len(SCRAPER_REGISTRY)} scrapers)")
    print("  ✅ cleaning_service")
except Exception as e:
    errors.append(f"Service import: {e}")
    print(f"  ❌ {e}")

# 3. Config validation
print("\n[3/6] Scraper config validation...")
try:
    for name, cls in SCRAPER_REGISTRY.items():
        s = cls()
        valid, msg = s.validate_config()
        status = "✅" if valid else "❌"
        print(f"  {status} {name}: {msg}")
        if not valid:
            errors.append(f"{name} validation failed: {msg}")
except Exception as e:
    errors.append(f"Validation: {e}")
    print(f"  ❌ {e}")

# 4. Cleaning functions
print("\n[4/6] Cleaning functions...")
try:
    t = clean_text("I can't believe it's broken!! https://test.com")
    assert "cannot" in t, f"Contraction failed: {t}"
    assert "[url]" in t, f"URL removal failed: {t}"

    assert classify_sentiment_simple("", 1.0) == "negative"
    assert classify_sentiment_simple("", 5.0) == "positive"
    assert classify_sentiment_simple("", 3.0) == "neutral"

    assert classify_relevance("the algorithm keeps playing same songs") == "relevant"
    assert classify_relevance("random text about cats and dogs") == "not_relevant"

    score = compute_quality_score(
        "I wish Spotify would fix the discover weekly algorithm "
        "because it keeps recommending the same artists over and over"
    )
    assert score > 0

    print("  ✅ clean_text works")
    print("  ✅ classify_sentiment works")
    print("  ✅ classify_relevance works")
    print(f"  ✅ compute_quality_score works (score={score})")
except Exception as e:
    errors.append(f"Cleaning: {e}")
    print(f"  ❌ {e}")

# 5. FastAPI app
print("\n[5/6] FastAPI app & routes...")
try:
    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200

    r = client.get("/api/v1/scrapers/status")
    assert r.status_code == 200
    assert r.json()["status"] == "idle"

    r = client.get("/api/v1/scrapers/logs")
    assert r.status_code == 200

    r = client.post("/api/v1/scrapers/stop")
    assert r.status_code == 200

    r = client.get("/api/v1/insights/status")
    assert r.status_code == 200

    print(f"  ✅ App loads ({len(app.routes)} routes)")
    print("  ✅ All API endpoints respond correctly")
except Exception as e:
    errors.append(f"FastAPI: {e}")
    print(f"  ❌ {e}")

# 6. Live scraper test
print("\n[6/6] Live scraper test (Hacker News)...")
try:
    from scrapers.social_scraper import _fetch_hackernews
    posts = _fetch_hackernews()
    assert len(posts) > 0, "No posts returned"
    assert posts[0]["source"] == "hackernews"
    assert len(posts[0]["text"]) > 25
    print(f"  ✅ Hacker News returned {len(posts)} posts")
except Exception as e:
    errors.append(f"Live test: {e}")
    print(f"  ❌ {e}")

# SUMMARY
print("\n" + "=" * 60)
if errors:
    print(f"❌ PHASE 2 HAS {len(errors)} ERROR(S):")
    for e in errors:
        print(f"   • {e}")
    sys.exit(1)
else:
    print("✅ PHASE 2 COMPLETED WITHOUT ANY ERRORS")
    print("   • 5 scraper adapters working")
    print("   • Scraper service with background execution")
    print("   • Cleaning service fully functional")
    print("   • All API endpoints respond correctly")
    print("   • Live data fetching confirmed")
print("=" * 60)
