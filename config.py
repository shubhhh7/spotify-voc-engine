"""
Spotify VoC Engine - Configuration
Adjust these settings before running the pipeline.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. DATA COLLECTION SETTINGS
# ============================================================

# Reddit Settings (FREE - requires Reddit API app: https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SpotifyVoCResearch/1.0")

# Target subreddits for music discovery pain points
REDDIT_SUBREDDITS = [
    "spotify",
    "truespotify", 
    "spotifywrapped",
    "WeAreTheMusicMakers",
    "music",
    "AppleMusic",  # For comparison/complaints about Spotify
    "musicsuggestions"
]

# Search queries that map to our 6 research questions
# These find threads where users discuss discovery struggles
REDDIT_SEARCH_QUERIES = [
    "discover new music",
    "recommendation algorithm",
    "playlist stuck same songs",
    "bored with spotify",
    "discovery weekly bad",
    "radio repetitive",
    "shuffle algorithm",
    "can't find new music",
    "recommendations terrible",
    "daily mix same",
    "on repeat stuck",
    "algorithm broken",
    "new music discovery",
    "song repetition",
    "playlist rotation"
]

# How many posts to fetch per query (keep low to respect rate limits)
REDDIT_POST_LIMIT = 50  # Max 100 recommended per query
REDDIT_COMMENT_DEPTH = 3  # How many comment levels to fetch
REDDIT_MIN_COMMENTS = 10  # Only fetch threads with meaningful discussion

# App Store Settings (FREE - uses app-store-scraper)
APP_STORE_APP_ID = "324684580"  # Spotify iOS app ID
APP_STORE_COUNTRIES = ["us", "gb", "ca", "au"]  # English-speaking markets
APP_STORE_COUNT = 250  # Per country

# Play Store Settings (FREE - uses google-play-scraper)
PLAY_STORE_APP_ID = "com.spotify.music"
PLAY_STORE_COUNTRIES = ["us", "gb", "ca", "au"]
PLAY_STORE_COUNT = 250  # Per country
PLAY_STORE_LANGUAGE = "en"

# ============================================================
# 2. DATA PROCESSING SETTINGS
# ============================================================

# Minimum text length to keep (filter out "great app" noise)
MIN_TEXT_LENGTH = 30  # Characters
MAX_TEXT_LENGTH = 3000  # Truncate very long posts

# Language filter (zero-budget: focus on English for accuracy)
TARGET_LANGUAGE = "en"

# Deduplication
DEDUP_THRESHOLD = 0.85  # Cosine similarity threshold (0-1)

# ============================================================
# 3. AI ANALYSIS SETTINGS (GEMINI FREE TIER)
# ============================================================

# Get free API key: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# Gemini Free Tier Limits (as of 2024):
# - Flash: 1,500 requests/day, 1M tokens/minute
# - Pro: 50 requests/day, 32K tokens/minute
# 
# Strategy: Use Flash for bulk extraction, Pro for deep synthesis

GEMINI_FLASH_MODEL = "gemini-1.5-flash"
GEMINI_PRO_MODEL = "gemini-1.5-pro"

# Batch size: How many reviews per API call
# 40 reviews × ~200 words = ~8K tokens input. Well within limits.
BATCH_SIZE = 40

# Rate limiting (requests per minute)
FLASH_RPM = 15  # Conservative (limit is 1,500/day = ~62/hour)
PRO_RPM = 2     # Conservative (limit is 50/day)

# ============================================================
# 4. OUTPUT SETTINGS
# ============================================================

OUTPUT_DIR = "data"
RAW_DIR = f"{OUTPUT_DIR}/raw"
CLEAN_DIR = f"{OUTPUT_DIR}/clean"
ANALYZED_DIR = f"{OUTPUT_DIR}/analyzed"
FINAL_DIR = f"{OUTPUT_DIR}/final"

# Create directories
for d in [RAW_DIR, CLEAN_DIR, ANALYZED_DIR, FINAL_DIR]:
    os.makedirs(d, exist_ok=True)
