"""
Spotify VoC Engine - TURBO CONFIG
Optimized for 2-day completion with Google Pro subscription
NO REDDIT API REQUIRED - uses public JSON API

Adjust these settings before running the pipeline.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. DATA COLLECTION SETTINGS
# ============================================================

# NO REDDIT API NEEDED - uses public JSON API (reddit.com/search.json)
# If Reddit blocks your IP, the script auto-falls back to PullPush API

REDDIT_SUBREDDITS = [
    "spotify",
    "truespotify", 
    "spotifywrapped",
    "WeAreTheMusicMakers",
    "music",
    "AppleMusic",
    "musicsuggestions",
    "spotifycommunity"
]

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

REDDIT_POST_LIMIT = 75
REDDIT_COMMENT_DEPTH = 2
REDDIT_MIN_COMMENTS = 5
REDDIT_COMMENTS_PER_POST = 15

APP_STORE_APP_ID = "324684580"
APP_STORE_COUNTRIES = ["us", "gb"]
APP_STORE_COUNT = 300

PLAY_STORE_APP_ID = "com.spotify.music"
PLAY_STORE_COUNTRIES = ["us", "gb"]
PLAY_STORE_COUNT = 300
PLAY_STORE_LANGUAGE = "en"

# ============================================================
# 2. DATA PROCESSING SETTINGS
# ============================================================

MIN_TEXT_LENGTH = 25
MAX_TEXT_LENGTH = 2500
TARGET_LANGUAGE = "en"
DEDUP_THRESHOLD = 0.88

# ============================================================
# 3. AI ANALYSIS SETTINGS (GEMINI FREE/PRO TIER)
# ============================================================

# Get free API key: https://aistudio.google.com/app/apikey
# Google Pro subscription gives higher limits

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_FLASH_MODEL = "gemini-1.5-flash"
GEMINI_PRO_MODEL = "gemini-1.5-pro"

BATCH_SIZE = 60
FLASH_RPM = 30
PRO_RPM = 10

# ============================================================
# 4. OUTPUT SETTINGS
# ============================================================

OUTPUT_DIR = "data"
RAW_DIR = f"{OUTPUT_DIR}/raw"
CLEAN_DIR = f"{OUTPUT_DIR}/clean"
ANALYZED_DIR = f"{OUTPUT_DIR}/analyzed"
FINAL_DIR = f"{OUTPUT_DIR}/final"

for d in [RAW_DIR, CLEAN_DIR, ANALYZED_DIR, FINAL_DIR]:
    os.makedirs(d, exist_ok=True)
