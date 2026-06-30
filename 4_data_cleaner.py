"""
Research-Grade Data Cleaning Pipeline for Spotify VoC Product Review Analysis
==============================================================================

Conservative cleaning pipeline optimized for downstream Product Management
research on music discovery, recommendation quality, and user behavior.

PHILOSOPHY: Never destroy evidence. Flag instead of delete. Preserve signals.

Run: python 4_data_cleaner.py
Input: data/raw/*.csv (all sources)
Output: data/clean/merged_reviews.csv + audit files

Compatible with: 5_gemini_analyzer.py (expects id, source, text_clean, date, rating/score)
"""

import pandas as pd
import numpy as np
import re
import os
import json
import logging
from datetime import datetime
from collections import defaultdict

from rapidfuzz import fuzz
from langdetect import detect, DetectorFactory
import emoji

import config_turbo as config

# Reproducible language detection
DetectorFactory.seed = 42

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{config.CLEAN_DIR}/cleaning.log", mode='w')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS & PRODUCT TERMS
# ============================================================

SPOTIFY_PRODUCT_TERMS = [
    "discover weekly", "daily mix", "smart shuffle", "ai dj", "release radar",
    "radio", "blend", "liked songs", "search", "queue", "premium", "free",
    "recommendations", "algorithm", "playlist", "artist", "album", "genre",
    "mood", "podcast", "on repeat", "repeat rewind", "time capsule",
    "wrapped", "daylist", "niche mix", "made for you", "enhanced",
    "autoplay", "crossfade", "collaborative playlist", "spotify connect",
    "car thing", "spotify kids", "duo", "family plan", "student plan"
]

PRODUCT_SIGNAL_KEYWORDS = [
    "frustration", "confusion", "discoverability", "recommendation",
    "playlist repetition", "same songs", "same artists", "new artists",
    "genre discovery", "algorithm", "music exploration", "hidden gems",
    "regional music", "search", "mood", "playlist generation",
    "bubble", "echo chamber", "filter bubble", "stuck", "bored",
    "repetitive", "stale", "fresh", "variety", "diversity"
]

SOURCE_NORMALIZATION = {
    "playstore": "Play Store", "play_store": "Play Store", "google_play": "Play Store",
    "appstore": "App Store", "app_store": "App Store", "apple_store": "App Store",
    "reddit": "Reddit", "r/spotify": "Reddit",
    "twitter": "Twitter/X", "x": "Twitter/X", "tweet": "Twitter/X",
    "youtube": "YouTube", "yt": "YouTube",
    "lemmy": "Lemmy", "mastodon": "Mastodon",
    "spotify_community": "Spotify Community",
    "forum": "Forum", "community": "Community",
    "social": "Social Media"
}


# Contractions expansion map
CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not",
    "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "wasn't": "was not", "aren't": "are not", "weren't": "were not",
    "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
    "i'm": "i am", "you're": "you are", "they're": "they are",
    "we're": "we are", "it's": "it is", "that's": "that is",
    "there's": "there is", "here's": "here is", "what's": "what is",
    "who's": "who is", "i've": "i have", "you've": "you have",
    "we've": "we have", "they've": "they have", "i'll": "i will",
    "you'll": "you will", "he'll": "he will", "she'll": "she will",
    "we'll": "we will", "they'll": "they will", "i'd": "i would",
    "you'd": "you would", "he'd": "he would", "she'd": "she would",
    "we'd": "we would", "they'd": "they would", "let's": "let us",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "ain't": "is not", "y'all": "you all"
}

# Relevance classification keywords
RELEVANT_KEYWORDS = [
    "discover", "recommendation", "playlist", "algorithm", "radio",
    "daily mix", "discover weekly", "release radar", "shuffle",
    "repeat", "same song", "new music", "music taste", "personali",
    "suggestion", "curate", "genre", "mood", "similar artist",
    "exploration", "variety", "diversity", "fresh", "stale",
    "bubble", "echo chamber", "ai dj", "blend", "autoplay",
    "queue", "mix", "liked songs", "on repeat", "wrapped"
]

NOT_RELEVANT_KEYWORDS = [
    "cannot login", "can't login", "payment failed", "charge my card",
    "refund", "cancel subscription", "app crash", "force close",
    "install", "update fail", "customer support", "account locked",
    "password reset", "verify email", "download fail", "storage",
    "offline mode broken", "cannot connect", "wifi", "bluetooth"
]


# ============================================================
# AUDIT TRAIL
# ============================================================

class AuditTrail:
    """Tracks every transformation for full traceability."""

    def __init__(self):
        self.actions = []
        self.stats = defaultdict(int)
        self.start_time = datetime.now()

    def log(self, record_id, action, details=""):
        self.actions.append({
            "timestamp": datetime.now().isoformat(),
            "record_id": record_id,
            "action": action,
            "details": details
        })
        self.stats[action] += 1

    def summary(self):
        return dict(self.stats)

    def to_dataframe(self):
        return pd.DataFrame(self.actions)

    def elapsed(self):
        return (datetime.now() - self.start_time).total_seconds()


audit = AuditTrail()


# ============================================================
# STEP 1: SCHEMA VALIDATION & INGESTION
# ============================================================

def infer_text_column(df):
    """Automatically detect the primary text column."""
    text_candidates = ['text', 'review', 'comment', 'body', 'content', 'message',
                       'review_text', 'comment_body', 'description']
    for col in text_candidates:
        if col in df.columns:
            return col
    # Fallback: longest average string column
    str_cols = df.select_dtypes(include='object').columns
    if len(str_cols) > 0:
        avg_lens = {c: df[c].astype(str).str.len().mean() for c in str_cols}
        return max(avg_lens, key=avg_lens.get)
    return None


def infer_columns(df):
    """Map source columns to our common schema."""
    mapping = {}
    col_lower = {c.lower(): c for c in df.columns}

    # ID
    for candidate in ['id', 'review_id', 'post_id', 'comment_id']:
        if candidate in col_lower:
            mapping['id'] = col_lower[candidate]
            break

    # Source
    for candidate in ['source', 'platform', 'origin']:
        if candidate in col_lower:
            mapping['source'] = col_lower[candidate]
            break

    # Text
    text_col = infer_text_column(df)
    if text_col:
        mapping['text'] = text_col

    # Rating
    for candidate in ['rating', 'star_rating', 'stars', 'score']:
        if candidate in col_lower:
            mapping['rating'] = col_lower[candidate]
            break

    # Date
    for candidate in ['date', 'created_utc', 'timestamp', 'created_at', 'review_date']:
        if candidate in col_lower:
            mapping['date'] = col_lower[candidate]
            break

    # Title
    for candidate in ['title', 'subject', 'heading']:
        if candidate in col_lower:
            mapping['title'] = col_lower[candidate]
            break

    # Author
    for candidate in ['author', 'username', 'user', 'reviewer']:
        if candidate in col_lower:
            mapping['author'] = col_lower[candidate]
            break

    return mapping


def load_and_validate(filepath, source_hint=None):
    """Load CSV with schema validation and column inference."""
    logger.info(f"Loading: {filepath}")
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        logger.warning(f"Failed to load {filepath}: {e}")
        return None

    if df.empty:
        logger.warning(f"Empty file: {filepath}")
        return None

    col_map = infer_columns(df)
    logger.info(f"  Columns detected: {list(col_map.keys())} from {list(df.columns)}")

    # Standardize to common schema, preserving all original columns
    if 'text' in col_map and col_map['text'] != 'text':
        df['text'] = df[col_map['text']]
    if 'id' not in df.columns:
        df['id'] = [f"{source_hint}_{i}" for i in range(len(df))]
    if 'source' not in df.columns:
        df['source'] = source_hint or os.path.basename(filepath).replace('.csv', '')
    if 'date' in col_map and col_map['date'] != 'date':
        df['date'] = df[col_map['date']]
    if 'rating' in col_map and col_map['rating'] != 'rating':
        df['rating'] = df[col_map['rating']]

    # Combine title + text for richer signal (if title exists separately)
    if 'title' in df.columns and 'text' in df.columns:
        df['text'] = df.apply(
            lambda r: f"{r['title']}. {r['text']}" if pd.notna(r.get('title'))
            and str(r.get('title', '')).strip()
            and str(r.get('title', '')).strip() != str(r.get('text', ''))[:len(str(r.get('title', '')))]
            else str(r.get('text', '')),
            axis=1
        )

    logger.info(f"  Records: {len(df)}")
    return df


# ============================================================
# STEP 2: EXACT DUPLICATE REMOVAL
# ============================================================

def remove_exact_duplicates(df):
    """Remove exact duplicates (same text + source). Keep first occurrence."""
    before = len(df)
    # Exact text + source duplicates
    dup_mask = df.duplicated(subset=['text', 'source'], keep='first')
    duplicates_df = df[dup_mask].copy()

    for idx in duplicates_df.index:
        audit.log(df.loc[idx, 'id'], "exact_duplicate_removed",
                  f"source={df.loc[idx, 'source']}")

    df_clean = df[~dup_mask].reset_index(drop=True)

    # Also check exact text-only duplicates (cross-source)
    text_dup_mask = df_clean.duplicated(subset=['text'], keep='first')
    text_dups = df_clean[text_dup_mask].copy()
    for idx in text_dups.index:
        audit.log(df_clean.loc[idx, 'id'], "cross_source_exact_duplicate_removed",
                  f"source={df_clean.loc[idx, 'source']}")
    df_clean = df_clean[~text_dup_mask].reset_index(drop=True)

    removed = before - len(df_clean)
    logger.info(f"  Exact duplicates removed: {removed}")
    return df_clean, duplicates_df


# ============================================================
# STEP 3: NEAR DUPLICATE DETECTION (FLAG ONLY)
# ============================================================

def detect_near_duplicates(df, threshold=92):
    """
    Flag near-duplicates using rapidfuzz ratio.
    Does NOT delete — only flags.
    Uses blocking by first 30 chars to keep it performant on large datasets.
    """
    logger.info(f"  Near-duplicate detection (threshold={threshold})...")
    df['near_duplicate'] = False
    df['near_duplicate_group'] = -1

    texts = df['text'].fillna('').tolist()
    n = len(texts)

    if n > 15000:
        # Block by first 30 chars prefix for performance
        logger.info(f"  Using prefix blocking for {n} records...")
        blocks = defaultdict(list)
        for i, t in enumerate(texts):
            prefix = t[:30].lower().strip()
            blocks[prefix].append(i)

        group_id = 0
        for prefix, indices in blocks.items():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, min(i + 10, len(indices))):
                    score = fuzz.ratio(texts[indices[i]], texts[indices[j]])
                    if score >= threshold:
                        df.loc[df.index[indices[i]], 'near_duplicate'] = True
                        df.loc[df.index[indices[j]], 'near_duplicate'] = True
                        df.loc[df.index[indices[i]], 'near_duplicate_group'] = group_id
                        df.loc[df.index[indices[j]], 'near_duplicate_group'] = group_id
                        group_id += 1
    else:
        # Full pairwise for smaller datasets
        group_id = 0
        for i in range(n):
            if df.loc[df.index[i], 'near_duplicate']:
                continue
            for j in range(i + 1, min(i + 50, n)):
                score = fuzz.ratio(texts[i], texts[j])
                if score >= threshold:
                    df.loc[df.index[i], 'near_duplicate'] = True
                    df.loc[df.index[j], 'near_duplicate'] = True
                    df.loc[df.index[i], 'near_duplicate_group'] = group_id
                    df.loc[df.index[j], 'near_duplicate_group'] = group_id
                    audit.log(df.loc[df.index[j], 'id'], "near_duplicate_flagged",
                              f"similar_to={df.loc[df.index[i], 'id']} score={score}")
                    group_id += 1

    flagged = df['near_duplicate'].sum()
    logger.info(f"  Near-duplicates flagged: {flagged}")
    return df


# ============================================================
# STEP 4: TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text while preserving product terms, artist names, and meaning.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    original = text

    # Fix unicode issues
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2014', ' - ').replace('\u2013', ' - ')
    text = text.replace('\xa0', ' ')

    # Remove excessive whitespace (but preserve paragraph breaks)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove repeated punctuation (but keep !! or ?? for sentiment)
    text = re.sub(r'([!?])\1{2,}', r'\1\1', text)  # cap at 2
    text = re.sub(r'\.{4,}', '...', text)

    # Lowercase (preserving original in separate column)
    text = text.lower()

    # Expand contractions
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(r'\b' + re.escape(contraction) + r'\b', expansion, text)

    # Clean up remaining whitespace
    text = text.strip()

    return text


# ============================================================
# STEP 5: EMOJI HANDLING
# ============================================================

def convert_emojis(text):
    """Convert emojis to text descriptors preserving sentiment signal."""
    if not isinstance(text, str):
        return ""
    # emoji.demojize converts emojis to :text_description:
    text = emoji.demojize(text, delimiters=(" [", "] "))
    # Clean up the format: [thumbs_up] -> [thumbs up]
    text = re.sub(r'\[([^\]]+)\]', lambda m: f"[{m.group(1).replace('_', ' ')}]", text)
    return text


# ============================================================
# STEP 6: URL HANDLING
# ============================================================

def remove_urls(text):
    """Replace URLs with [URL] marker, preserving surrounding text."""
    if not isinstance(text, str):
        return ""
    text = re.sub(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        '[URL]', text
    )
    text = re.sub(r'www\.\S+', '[URL]', text)
    return text


# ============================================================
# STEP 7: MENTION & HASHTAG HANDLING
# ============================================================

def normalize_mentions(text):
    """Convert @mentions to [MENTION:name] and #hashtags to readable text."""
    if not isinstance(text, str):
        return ""
    # @mentions -> [MENTION:name]
    text = re.sub(r'@(\w+)', r'[MENTION:\1]', text)
    # #hashtags -> readable text (CamelCase split)
    def hashtag_to_text(match):
        tag = match.group(1)
        # Split CamelCase: DiscoverWeekly -> Discover Weekly
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', tag)
        words = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', words)
        return words
    text = re.sub(r'#(\w+)', hashtag_to_text, text)
    return text


# ============================================================
# STEP 8: (Product terms preserved by design — no removal step)
# ============================================================


# ============================================================
# STEP 9: NOISE / LOW INFORMATION DETECTION
# ============================================================

def detect_low_information(text):
    """
    Flag low-information content. Returns (is_low_info, reason).
    Does NOT delete — only flags.
    """
    if not isinstance(text, str) or not text.strip():
        return True, "blank"

    clean = text.strip()

    # Blank or whitespace only
    if len(clean) == 0:
        return True, "blank"

    # Single character
    if len(clean) <= 2:
        return True, "single_char"

    # Only emojis (after conversion they'd be [emoji] tags)
    if re.match(r'^[\s\[\]a-z ]+$', clean) and '[' in clean and len(clean) < 20:
        return True, "emoji_only"

    # Repeated characters (keyboard spam)
    if re.match(r'^(.)\1{4,}$', clean.replace(' ', '')):
        return True, "keyboard_spam"

    # Very short generic responses (but NOT if they contain product terms)
    generic_short = ['lol', 'nice', 'good', 'ok', 'cool', 'yes', 'no', 'thanks',
                     'same', 'true', 'facts', 'this', 'agreed', 'mood', 'fr',
                     'ikr', 'yep', 'nope', 'haha', 'lmao', 'bruh']
    if clean.lower().strip('!?.') in generic_short:
        # Check if it contains any product terms
        if not any(term in clean.lower() for term in SPOTIFY_PRODUCT_TERMS):
            return True, "generic_short"

    # Very low word count without product signal
    words = clean.split()
    if len(words) <= 3 and not any(term in clean.lower() for term in SPOTIFY_PRODUCT_TERMS):
        if not any(kw in clean.lower() for kw in PRODUCT_SIGNAL_KEYWORDS):
            return True, "very_short_no_signal"

    # Copypasta detection (very long repeated phrases)
    if len(clean) > 500:
        first_half = clean[:len(clean)//2]
        second_half = clean[len(clean)//2:]
        if fuzz.ratio(first_half, second_half) > 90:
            return True, "copypasta"

    return False, ""


# ============================================================
# STEP 10: LANGUAGE DETECTION
# ============================================================

def detect_language(text):
    """Detect language. Returns language code."""
    try:
        if not isinstance(text, str) or len(text.strip()) < 20:
            return "unknown"
        return detect(text)
    except Exception:
        return "unknown"


# ============================================================
# STEP 11: RATING NORMALIZATION
# ============================================================

def normalize_rating(rating):
    """Normalize numeric ratings to Positive/Neutral/Negative."""
    try:
        r = float(rating)
        if r <= 2:
            return "Negative"
        elif r <= 3:
            return "Neutral"
        else:
            return "Positive"
    except (ValueError, TypeError):
        return "Unknown"


# ============================================================
# STEP 12: SOURCE NORMALIZATION
# ============================================================

def normalize_source(source):
    """Normalize source names to standard labels."""
    if not isinstance(source, str):
        return "Unknown"
    source_lower = source.lower().strip()
    for key, normalized in SOURCE_NORMALIZATION.items():
        if key in source_lower:
            return normalized
    return source.strip().title()


# ============================================================
# STEP 13: RELEVANCE CLASSIFICATION
# ============================================================

def classify_relevance(text):
    """
    Classify: Relevant, Partially Relevant, Not Relevant.
    Conservative — if mixed, always classify higher.
    """
    if not isinstance(text, str):
        return "Not Relevant"

    text_lower = text.lower()

    has_relevant = any(kw in text_lower for kw in RELEVANT_KEYWORDS)
    has_not_relevant = any(kw in text_lower for kw in NOT_RELEVANT_KEYWORDS)
    has_product_signal = any(kw in text_lower for kw in PRODUCT_SIGNAL_KEYWORDS)

    # If has product signals or relevant keywords -> Relevant
    if has_relevant or has_product_signal:
        return "Relevant"
    # If has BOTH not-relevant and some music/app context -> Partially Relevant
    if has_not_relevant and ('spotify' in text_lower or 'music' in text_lower or 'app' in text_lower):
        return "Partially Relevant"
    # If only not-relevant keywords
    if has_not_relevant:
        return "Not Relevant"
    # Default: if it mentions Spotify or music at all, keep as Partially Relevant
    if 'spotify' in text_lower or 'music' in text_lower or 'song' in text_lower:
        return "Partially Relevant"

    return "Not Relevant"


# ============================================================
# STEP 14: (Product signals preserved by design — never removed)
# ============================================================


# ============================================================
# STEP 15: QUALITY SCORE
# ============================================================

def compute_quality_score(row):
    """
    Score 0-100 based on information richness, specificity, and actionability.
    """
    text = str(row.get('text_clean', ''))
    score = 0

    # Length contribution (0-25)
    word_count = len(text.split())
    if word_count >= 50:
        score += 25
    elif word_count >= 20:
        score += 15
    elif word_count >= 10:
        score += 8
    else:
        score += 3

    # Specificity: mentions product features (0-25)
    product_mentions = sum(1 for term in SPOTIFY_PRODUCT_TERMS if term in text.lower())
    score += min(product_mentions * 5, 25)

    # Actionable feedback signals (0-25)
    actionable_phrases = ['should', 'would be better', 'wish', 'need', 'want',
                          'please', 'fix', 'improve', 'add', 'remove', 'change',
                          'why does', 'how come', 'used to', 'bring back']
    actionable_count = sum(1 for p in actionable_phrases if p in text.lower())
    score += min(actionable_count * 5, 25)

    # Emotion & engagement (0-15)
    emotion_markers = ['!', '?', 'frustrat', 'love', 'hate', 'amazing', 'terrible',
                       'disappoint', 'excit', 'annoy']
    emotion_count = sum(1 for e in emotion_markers if e in text.lower())
    score += min(emotion_count * 3, 15)

    # Detail indicators (0-10)
    if any(c.isdigit() for c in text):
        score += 3  # Contains numbers (specific data)
    if 'because' in text.lower() or 'since' in text.lower():
        score += 4  # Contains reasoning
    if 'example' in text.lower() or 'for instance' in text.lower():
        score += 3  # Contains examples

    return min(score, 100)


# ============================================================
# FULL CLEANING PIPELINE
# ============================================================

def clean_single_record(text):
    """Apply all text transformations in order."""
    if not isinstance(text, str) or not text.strip():
        return ""
    # Step 5: Emojis -> text
    text = convert_emojis(text)
    # Step 6: URLs
    text = remove_urls(text)
    # Step 7: Mentions & hashtags
    text = normalize_mentions(text)
    # Step 4: Text normalization (lowercase, contractions, whitespace)
    text = normalize_text(text)
    return text


def main():
    print("=" * 70)
    print("🔬 RESEARCH-GRADE DATA CLEANING PIPELINE")
    print("   Spotify VoC Engine — Conservative Cleaning for Product Research")
    print("=" * 70)

    # ----------------------------------------------------------
    # INGEST ALL RAW FILES
    # ----------------------------------------------------------
    raw_files = {
        'reddit': f"{config.RAW_DIR}/reddit_posts.csv",
        'app_store': f"{config.RAW_DIR}/appstore_reviews.csv",
        'play_store': f"{config.RAW_DIR}/playstore_reviews.csv",
        'twitter': f"{config.RAW_DIR}/twitter_posts.csv",
        'community': f"{config.RAW_DIR}/community_posts.csv",
        'social': f"{config.RAW_DIR}/social_posts.csv",
    }

    dfs = []
    for source_hint, filepath in raw_files.items():
        if os.path.exists(filepath):
            df = load_and_validate(filepath, source_hint=source_hint)
            if df is not None and len(df) > 0:
                dfs.append(df)
        else:
            logger.info(f"  Skipping (not found): {filepath}")

    # Also pick up any other CSVs in raw dir
    for f in os.listdir(config.RAW_DIR):
        if f.endswith('.csv'):
            full_path = os.path.join(config.RAW_DIR, f)
            if full_path not in raw_files.values():
                df = load_and_validate(full_path, source_hint=f.replace('.csv', ''))
                if df is not None and len(df) > 0:
                    dfs.append(df)

    if not dfs:
        logger.error("No data files found. Run scrapers first.")
        print("\n❌ No data files found in data/raw/. Run scrapers first.")
        return

    print(f"\n📦 Merging {len(dfs)} source files...")
    merged = pd.concat(dfs, ignore_index=True, sort=False)
    rows_loaded = len(merged)
    logger.info(f"Total records loaded: {rows_loaded}")
    print(f"   Total records: {rows_loaded}")

    # Ensure required columns exist
    for col in ['id', 'source', 'text']:
        if col not in merged.columns:
            merged[col] = ""

    # Preserve original text (NEVER overwrite)
    merged['text_original'] = merged['text'].copy()


    # ----------------------------------------------------------
    # STEP 2: EXACT DUPLICATES
    # ----------------------------------------------------------
    print("\n🔍 Step 2: Removing exact duplicates...")
    merged, duplicates_df = remove_exact_duplicates(merged)

    # ----------------------------------------------------------
    # STEP 4-7: TEXT CLEANING (applied to produce text_clean)
    # ----------------------------------------------------------
    print("\n✨ Steps 4-7: Text normalization, emojis, URLs, mentions...")
    merged['text_clean'] = merged['text'].apply(clean_single_record)

    # Remove records where cleaned text is completely empty
    empty_mask = merged['text_clean'].str.strip().str.len() == 0
    empty_count = empty_mask.sum()
    for idx in merged[empty_mask].index:
        audit.log(merged.loc[idx, 'id'], "removed_empty_after_clean", "")
    merged = merged[~empty_mask].reset_index(drop=True)
    logger.info(f"  Removed {empty_count} empty records after cleaning")

    # ----------------------------------------------------------
    # STEP 3: NEAR DUPLICATE DETECTION (flag only)
    # ----------------------------------------------------------
    print("\n🔗 Step 3: Near-duplicate detection...")
    merged = detect_near_duplicates(merged, threshold=92)

    # ----------------------------------------------------------
    # STEP 9: NOISE / LOW INFORMATION DETECTION
    # ----------------------------------------------------------
    print("\n🔇 Step 9: Low-information detection...")
    noise_results = merged['text_clean'].apply(detect_low_information)
    merged['low_information'] = noise_results.apply(lambda x: x[0])
    merged['low_info_reason'] = noise_results.apply(lambda x: x[1])
    low_info_count = merged['low_information'].sum()
    logger.info(f"  Low-information flagged: {low_info_count}")
    print(f"   Flagged: {low_info_count} records (NOT deleted)")

    # Only remove truly blank/meaningless (single char, blank)
    truly_empty = merged['low_info_reason'].isin(['blank', 'single_char'])
    removed_noise = truly_empty.sum()
    for idx in merged[truly_empty].index:
        audit.log(merged.loc[idx, 'id'], "removed_noise",
                  merged.loc[idx, 'low_info_reason'])
    merged = merged[~truly_empty].reset_index(drop=True)
    logger.info(f"  Removed {removed_noise} truly empty/single-char records")

    # ----------------------------------------------------------
    # STEP 10: LANGUAGE DETECTION
    # ----------------------------------------------------------
    print("\n🌍 Step 10: Language detection...")
    merged['language'] = merged['text_clean'].apply(detect_language)
    lang_dist = merged['language'].value_counts()
    logger.info(f"  Languages detected: {dict(lang_dist.head(10))}")
    print(f"   Top languages: {dict(lang_dist.head(5))}")

    # Flag non-English but do NOT delete (preserve for potential translation)
    merged['needs_translation'] = ~merged['language'].isin(['en', 'unknown'])
    non_en = merged['needs_translation'].sum()
    logger.info(f"  Non-English records (kept, flagged): {non_en}")

    # Create output directory early
    output_dir = f"{config.OUTPUT_DIR}/clean_v2"
    os.makedirs(output_dir, exist_ok=True)

    # For downstream compatibility: filter to English + unknown for main output
    # but save all records in a separate file
    if non_en > 0:
        non_en_df = merged[merged['needs_translation']].copy()
        non_en_df.to_csv(f"{output_dir}/non_english_reviews.csv", index=False)
        logger.info(f"  Saved non-English records to clean_v2/non_english_reviews.csv")


    # Keep English + unknown for main pipeline (conservative)
    merged = merged[merged['language'].isin(['en', 'unknown'])].reset_index(drop=True)

    # ----------------------------------------------------------
    # STEP 11: RATING NORMALIZATION
    # ----------------------------------------------------------
    print("\n⭐ Step 11: Rating normalization...")
    if 'rating' in merged.columns:
        merged['rating_original'] = merged['rating'].copy()
        merged['sentiment_from_rating'] = merged['rating'].apply(normalize_rating)
    else:
        merged['sentiment_from_rating'] = "Unknown"

    # Also use score (upvotes) if available
    if 'score' in merged.columns:
        merged['score'] = pd.to_numeric(merged['score'], errors='coerce').fillna(0)

    # ----------------------------------------------------------
    # STEP 12: SOURCE NORMALIZATION
    # ----------------------------------------------------------
    print("\n🏷️  Step 12: Source normalization...")
    merged['source_original'] = merged['source'].copy()
    merged['source'] = merged['source'].apply(normalize_source)
    print(f"   Sources: {merged['source'].value_counts().to_dict()}")

    # ----------------------------------------------------------
    # STEP 13: RELEVANCE CLASSIFICATION
    # ----------------------------------------------------------
    print("\n🎯 Step 13: Relevance classification...")
    merged['relevance'] = merged['text_clean'].apply(classify_relevance)
    rel_dist = merged['relevance'].value_counts()
    print(f"   Relevant: {rel_dist.get('Relevant', 0)}")
    print(f"   Partially Relevant: {rel_dist.get('Partially Relevant', 0)}")
    print(f"   Not Relevant: {rel_dist.get('Not Relevant', 0)}")

    # ----------------------------------------------------------
    # STEP 15: QUALITY SCORE
    # ----------------------------------------------------------
    print("\n💎 Step 15: Quality scoring...")
    merged['quality_score'] = merged.apply(compute_quality_score, axis=1)
    print(f"   Mean quality: {merged['quality_score'].mean():.1f}")
    print(f"   High quality (>70): {(merged['quality_score'] > 70).sum()}")
    print(f"   Low quality (<30): {(merged['quality_score'] < 30).sum()}")

    # ----------------------------------------------------------
    # ENRICHMENT (backward compatible with 5_gemini_analyzer.py)
    # ----------------------------------------------------------
    print("\n📊 Enrichment...")
    merged['text_length'] = merged['text_clean'].str.len()
    merged['word_count'] = merged['text_clean'].str.split().str.len()
    merged['has_product_term'] = merged['text_clean'].apply(
        lambda x: any(term in str(x).lower() for term in SPOTIFY_PRODUCT_TERMS)
    )


    # ----------------------------------------------------------
    # STEP 16: OUTPUT FILES
    # ----------------------------------------------------------
    print("\n" + "=" * 70)
    print("📁 GENERATING OUTPUT FILES")
    print("=" * 70)

    # Output to clean_v2 directory to keep separate from old runs
    os.makedirs(output_dir, exist_ok=True)

    # Also write to standard clean dir for downstream compatibility
    os.makedirs(config.CLEAN_DIR, exist_ok=True)

    # 1. Main cleaned file (compatible with 5_gemini_analyzer.py)
    output_path = f"{output_dir}/merged_reviews.csv"
    merged.to_csv(output_path, index=False)
    # Also save to standard location for pipeline compatibility
    merged.to_csv(f"{config.CLEAN_DIR}/merged_reviews.csv", index=False)
    print(f"   ✅ {output_path} ({len(merged)} records)")

    # 2. Audit log
    audit_df = audit.to_dataframe()
    audit_path = f"{output_dir}/review_audit_log.csv"
    if not audit_df.empty:
        audit_df.to_csv(audit_path, index=False)
    print(f"   ✅ {audit_path} ({len(audit_df)} actions)")

    # 3. Duplicate reviews
    dup_path = f"{output_dir}/duplicate_reviews.csv"
    if len(duplicates_df) > 0:
        duplicates_df.to_csv(dup_path, index=False)
    print(f"   ✅ {dup_path} ({len(duplicates_df)} duplicates)")

    # 4. Near duplicates
    near_dup_df = merged[merged['near_duplicate'] == True].copy()
    near_dup_path = f"{output_dir}/near_duplicates.csv"
    near_dup_df.to_csv(near_dup_path, index=False)
    print(f"   ✅ {near_dup_path} ({len(near_dup_df)} flagged)")

    # 5. Cleaning summary JSON
    summary = {
        "pipeline_version": "2.0.0",
        "run_timestamp": datetime.now().isoformat(),
        "elapsed_seconds": audit.elapsed(),
        "rows_loaded": rows_loaded,
        "rows_final": len(merged),
        "rows_removed_exact_duplicates": len(duplicates_df),
        "rows_removed_empty": empty_count,
        "rows_removed_noise": int(removed_noise),
        "rows_flagged_near_duplicate": int(near_dup_df['near_duplicate'].sum()),
        "rows_flagged_low_information": int(low_info_count),
        "rows_non_english": int(non_en),
        "languages_detected": dict(lang_dist.head(10)),
        "relevance_distribution": dict(rel_dist),
        "source_distribution": dict(merged['source'].value_counts()),
        "quality_score_mean": float(merged['quality_score'].mean()),
        "quality_score_median": float(merged['quality_score'].median()),
        "audit_actions": audit.summary()
    }
    summary_path = f"{output_dir}/cleaning_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"   ✅ {summary_path}")

    # ----------------------------------------------------------
    # FINAL REPORT
    # ----------------------------------------------------------
    print("\n" + "=" * 70)
    print("📋 CLEANING REPORT")
    print("=" * 70)
    print(f"   Rows loaded:              {rows_loaded}")
    print(f"   Exact duplicates removed: {len(duplicates_df)}")
    print(f"   Empty after clean:        {empty_count}")
    print(f"   Noise removed:            {removed_noise}")
    print(f"   Near-duplicates flagged:  {near_dup_df['near_duplicate'].sum()}")
    print(f"   Low-information flagged:  {low_info_count}")
    print(f"   Non-English (saved sep.): {non_en}")
    print(f"   ─────────────────────────────────────")
    print(f"   Final dataset size:       {len(merged)}")
    print(f"\n   📊 Source breakdown:")
    for src, count in merged['source'].value_counts().items():
        print(f"      {src}: {count}")
    print(f"\n   🎯 Relevance breakdown:")
    for rel, count in rel_dist.items():
        print(f"      {rel}: {count}")
    print(f"\n   💎 Quality score: mean={merged['quality_score'].mean():.1f}, "
          f"median={merged['quality_score'].median():.1f}")
    print(f"\n   ⏱️  Elapsed: {audit.elapsed():.1f}s")
    print("=" * 70)

    # Quick sample of high-quality relevant reviews
    high_quality = merged[
        (merged['relevance'] == 'Relevant') & (merged['quality_score'] > 60)
    ]
    if len(high_quality) > 0:
        print("\n📝 Sample high-quality relevant reviews:")
        samples = high_quality.sample(min(3, len(high_quality)))
        for _, row in samples.iterrows():
            print(f"\n   [{row['source']}] (Q={row['quality_score']}) "
                  f"{row['text_clean'][:200]}...")


if __name__ == "__main__":
    main()
