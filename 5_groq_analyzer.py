"""
Groq AI Analyzer - Per-Source Processing with Small Chunks
Uses Groq's fast inference (Llama 3) to avoid payload-too-large errors.

Strategy:
- Process each source type separately (reddit, community, social, app_store, play_store, twitter)
- Use VERY small chunks (5 reviews per batch) to stay under payload limits
- Reddit/community/social get even smaller chunks (3 reviews) since posts are longer

Run: python 5_groq_analyzer.py
Input: data/clean_v2/merged_reviews.csv (or data/clean/merged_reviews.csv)
Output: data/analyzed/analyzed_reviews.csv + per-source files
"""

import os
import json
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast + capable
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"  # Ultra-fast fallback if 70b fails

# Chunk sizes per source type - KEEP SMALL to avoid payload errors
# Reddit/community/social posts are much longer than app reviews
CHUNK_SIZES = {
    "reddit": 3,          # Reddit posts are long (300-2000 chars)
    "spotify_community": 3,  # Community posts can be lengthy
    "hackernews": 3,      # HN posts are verbose
    "lemmy": 3,           # Same as reddit-like
    "social": 3,          # Social media posts vary
    "twitter": 5,         # Tweets are short
    "app_store": 5,       # App reviews are medium
    "play_store": 5,      # Play reviews are medium
}

DEFAULT_CHUNK_SIZE = 3  # Default for unknown sources

# Rate limiting for Groq free tier
REQUESTS_PER_MINUTE = 28  # Groq free tier: 30 RPM, keep buffer
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE

# Max text length per review to send (truncate longer ones)
MAX_TEXT_PER_REVIEW = 500  # Characters - keeps payload small

# Directories
OUTPUT_DIR = "data"
CLEAN_DIR = f"{OUTPUT_DIR}/clean_v2"
CLEAN_DIR_FALLBACK = f"{OUTPUT_DIR}/clean"
ANALYZED_DIR = f"{OUTPUT_DIR}/analyzed"
os.makedirs(ANALYZED_DIR, exist_ok=True)

# ============================================================
# GROQ CLIENT
# ============================================================

import requests as req

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq(prompt, model=None, max_tokens=4096, temperature=0.1, max_retries=3):
    """Call Groq API with retry logic and payload safety."""
    if model is None:
        model = GROQ_MODEL

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior product insights analyst. Always respond with valid JSON only, no markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            response = req.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return safe_json_parse(content)

            elif response.status_code == 413 or "payload too large" in response.text.lower():
                print(f"   ⚠️ Payload too large! Reducing chunk further...")
                return "PAYLOAD_TOO_LARGE"

            elif response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                print(f"   ⚠️ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)

            elif response.status_code == 400:
                # Try fallback model with smaller output
                if model != GROQ_FALLBACK_MODEL:
                    print(f"   ⚠️ Error with {model}, trying fallback model...")
                    return call_groq(prompt, model=GROQ_FALLBACK_MODEL, 
                                    max_tokens=2048, temperature=temperature, 
                                    max_retries=max_retries - 1)
                else:
                    print(f"   ❌ API error 400: {response.text[:200]}")
                    time.sleep(5)

            else:
                print(f"   ❌ API error {response.status_code}: {response.text[:200]}")
                time.sleep(5)

        except req.exceptions.Timeout:
            print(f"   ⚠️ Timeout (attempt {attempt+1}/{max_retries})")
            time.sleep(10)
        except Exception as e:
            print(f"   ❌ Error (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(5)

    return None


def safe_json_parse(text):
    """Parse JSON from API response, handling common issues."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        return None


# ============================================================
# EXTRACTION PROMPT (kept concise to reduce token usage)
# ============================================================

EXTRACTION_PROMPT_TEMPLATE = """Analyze these {count} user feedback entries about Spotify and return a JSON object with key "results" containing an array of analysis objects.

For EACH entry, extract:
- "id": the entry ID provided
- "pain_point": boolean (true if user has frustration/unmet need)
- "pain_category": one of [Discovery, Recommendations, UI/UX, Performance, Pricing, Social, Content, Other, None]
- "pain_severity": 1-5 (1=mild, 5=dealbreaker)
- "sentiment": one of [Very Negative, Negative, Neutral, Positive, Very Positive]
- "emotion": one of [Frustration, Confusion, Anger, Disappointment, Indifference, Satisfaction, Excitement, Anxiety, Boredom, None]
- "jtbd_statement": "When I [situation], I want to [motivation], so I can [outcome]" or "Unclear"
- "discovery_issue": boolean
- "recommendation_issue": boolean
- "repetition_issue": boolean
- "unmet_need": max 15 words
- "user_segment_hint": one of [Casual Listener, Power User, Curator, Social Listener, New User, Long-term User, Mobile-only, Desktop-heavy, Commuter, Student, None]
- "key_quote": exact quote max 20 words
- "confidence": 1-5

ENTRIES:
{entries}

Return ONLY valid JSON: {{"results": [...]}}"""


# ============================================================
# DEEP JTBD PROMPT (for high-severity items)
# ============================================================

DEEP_JTBD_PROMPT = """Analyze this detailed Spotify user feedback for Jobs-to-be-Done insights.

TEXT: {text}
SOURCE: {source} | RATING: {rating} | DATE: {date}

Return JSON with:
- "main_jtbd": "When I [situation], I want to [motivation], so I can [outcome]"
- "emotional_trigger": what emotion drove them to write this
- "struggle_moment": specific moment Spotify failed them
- "workarounds": array of what they do instead
- "switching_triggers": array of what would make them leave
- "churn_risk": "Low", "Medium", "High", or "Very High"
- "pain_intensity": 1-10
- "evidence_quote": most powerful quote (max 30 words)

Return ONLY valid JSON."""


# ============================================================
# MAIN PROCESSING LOGIC
# ============================================================

def get_chunk_size(source):
    """Get appropriate chunk size for a source type."""
    source_lower = source.lower().replace(" ", "_")
    for key, size in CHUNK_SIZES.items():
        if key in source_lower:
            return size
    return DEFAULT_CHUNK_SIZE


def truncate_text(text, max_len=MAX_TEXT_PER_REVIEW):
    """Safely truncate text to avoid oversized payloads."""
    if pd.isna(text):
        return ""
    text = str(text).strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def process_chunk(chunk_df, source_name):
    """Process a single chunk of reviews through Groq."""
    entries = []
    for _, row in chunk_df.iterrows():
        text = truncate_text(row.get('text_clean', row.get('text', '')))
        if not text:
            continue
        entry = f"--- ID: {row['id']} ---\nSource: {source_name}\nRating: {row.get('rating', row.get('score', 'N/A'))}\nText: {text}\n"
        entries.append(entry)

    if not entries:
        return None

    entries_text = "\n".join(entries)
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(count=len(entries), entries=entries_text)

    # Check prompt size - if still too big, split further
    if len(prompt) > 12000:  # ~3000 tokens rough estimate
        print(f"   ⚠️ Chunk still large ({len(prompt)} chars), will process individually")
        return "SPLIT_FURTHER"

    result = call_groq(prompt)

    if result == "PAYLOAD_TOO_LARGE":
        return "SPLIT_FURTHER"

    if result and isinstance(result, dict) and "results" in result:
        return result["results"]
    elif result and isinstance(result, list):
        return result
    elif result and isinstance(result, dict):
        # Single result wrapped in object
        return [result]

    return None


def process_single_review(row, source_name):
    """Process a single review when chunks are too large."""
    text = truncate_text(row.get('text_clean', row.get('text', '')), max_len=300)
    if not text:
        return None

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        count=1,
        entries=f"--- ID: {row['id']} ---\nSource: {source_name}\nRating: {row.get('rating', row.get('score', 'N/A'))}\nText: {text}\n"
    )

    result = call_groq(prompt, max_tokens=1024)

    if result and isinstance(result, dict) and "results" in result:
        return result["results"]
    elif result and isinstance(result, list):
        return result
    elif result and isinstance(result, dict):
        return [result]
    return None


def process_source(df, source_name):
    """Process all reviews from a single source with appropriate chunking."""
    source_df = df[df['source'].str.lower().str.contains(source_name.lower())].copy()

    if len(source_df) == 0:
        print(f"   ℹ️ No data for source: {source_name}")
        return []

    chunk_size = get_chunk_size(source_name)
    total_chunks = (len(source_df) + chunk_size - 1) // chunk_size

    print(f"\n📂 Processing {source_name}: {len(source_df)} reviews in {total_chunks} chunks (size={chunk_size})")

    all_results = []
    failed_count = 0

    for i in tqdm(range(0, len(source_df), chunk_size), total=total_chunks, desc=f"  {source_name}"):
        chunk = source_df.iloc[i:i+chunk_size]

        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)

        result = process_chunk(chunk, source_name)

        if result == "SPLIT_FURTHER":
            # Process one by one
            for _, row in chunk.iterrows():
                time.sleep(DELAY_BETWEEN_REQUESTS)
                single_result = process_single_review(row, source_name)
                if single_result:
                    for r in single_result:
                        r['source'] = source_name
                    all_results.extend(single_result)
                else:
                    failed_count += 1
                    all_results.append({
                        'id': row['id'],
                        'source': source_name,
                        'pain_point': None,
                        'error': 'analysis_failed'
                    })
        elif result:
            for r in result:
                r['source'] = source_name
            all_results.extend(result)
        else:
            failed_count += 1
            # Add placeholder for failed batch
            for _, row in chunk.iterrows():
                all_results.append({
                    'id': row['id'],
                    'source': source_name,
                    'pain_point': None,
                    'error': 'analysis_failed'
                })

    success_count = sum(1 for r in all_results if r.get('error') is None)
    print(f"   ✅ {source_name}: {success_count}/{len(source_df)} processed | {failed_count} failures")

    return all_results


def run_deep_analysis(df, extractions_df, max_deep=30):
    """Run deep JTBD analysis on top severe items."""
    print(f"\n🔬 PHASE 2: Deep JTBD Analysis (top {max_deep} severe items)")

    # Find high-severity items
    severity_col = 'pain_severity'
    if severity_col in extractions_df.columns:
        extractions_df[severity_col] = pd.to_numeric(extractions_df[severity_col], errors='coerce').fillna(0)
        severe = extractions_df[extractions_df['pain_point'] == True].nlargest(max_deep, severity_col)
    else:
        severe = extractions_df[extractions_df['pain_point'] == True].head(max_deep)

    if len(severe) == 0:
        print("   ℹ️ No severe pain points found for deep analysis")
        return []

    print(f"   Analyzing {len(severe)} high-severity items...")

    deep_results = []
    for _, row in tqdm(severe.iterrows(), total=len(severe), desc="  Deep JTBD"):
        review_id = row.get('id', row.get('original_id'))
        original = df[df['id'] == review_id]

        if len(original) == 0:
            continue

        original = original.iloc[0]
        text = truncate_text(str(original.get('text_clean', original.get('text', ''))), max_len=600)

        if len(text) < 50:
            continue

        time.sleep(DELAY_BETWEEN_REQUESTS)

        prompt = DEEP_JTBD_PROMPT.format(
            text=text,
            source=original.get('source', 'unknown'),
            rating=original.get('rating', original.get('score', 'N/A')),
            date=original.get('date', 'unknown')
        )

        result = call_groq(prompt, max_tokens=1024, temperature=0.2)

        if result and isinstance(result, dict):
            result['original_id'] = review_id
            deep_results.append(result)

    print(f"   ✅ Deep analysis: {len(deep_results)} records completed")
    return deep_results


def main():
    print("🤖 Groq AI Analyzer - Per-Source Small Chunk Processing")
    print(f"Model: {GROQ_MODEL} | Fallback: {GROQ_FALLBACK_MODEL}")
    print(f"Max text/review: {MAX_TEXT_PER_REVIEW} chars")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} RPM")
    print("=" * 60)

    # Validate API key
    if GROQ_API_KEY == "your_groq_api_key_here" or not GROQ_API_KEY:
        print("❌ Please set GROQ_API_KEY in your .env file!")
        print("   Get your key at: https://console.groq.com/keys")
        return

    # Load data
    input_path = f"{CLEAN_DIR}/merged_reviews.csv"
    if not os.path.exists(input_path):
        input_path = f"{CLEAN_DIR_FALLBACK}/merged_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ No cleaned data found!")
        print(f"   Checked: {CLEAN_DIR}/merged_reviews.csv")
        print(f"   Checked: {CLEAN_DIR_FALLBACK}/merged_reviews.csv")
        return

    df = pd.read_csv(input_path)
    print(f"📊 Loaded {len(df)} total records from {input_path}")

    # Identify sources
    sources = df['source'].unique()
    print(f"📂 Sources found: {list(sources)}")
    for src in sources:
        count = len(df[df['source'] == src])
        chunk_sz = get_chunk_size(src)
        print(f"   - {src}: {count} reviews (chunk size: {chunk_sz})")

    # ========================================
    # PHASE 1: Per-Source Extraction
    # ========================================
    print(f"\n{'='*60}")
    print("📦 PHASE 1: Per-Source Extraction via Groq")
    print(f"{'='*60}")

    all_extractions = []

    for source in sources:
        results = process_source(df, source)
        all_extractions.extend(results)

        # Save intermediate per-source results
        if results:
            source_safe = source.lower().replace(" ", "_").replace("/", "_")
            source_df = pd.DataFrame(results)
            source_output = f"{ANALYZED_DIR}/extractions_{source_safe}.csv"
            source_df.to_csv(source_output, index=False)
            print(f"   💾 Saved: {source_output}")

    # Save all extractions
    extraction_df = pd.DataFrame(all_extractions)
    extraction_df.to_csv(f"{ANALYZED_DIR}/extractions.csv", index=False)

    total_success = sum(1 for r in all_extractions if r.get('error') is None)
    total_failed = len(all_extractions) - total_success
    print(f"\n{'='*60}")
    print(f"📊 Phase 1 Summary:")
    print(f"   Total processed: {len(all_extractions)}")
    print(f"   Successful: {total_success}")
    print(f"   Failed: {total_failed}")
    print(f"   Success rate: {total_success/max(len(all_extractions),1)*100:.1f}%")

    # ========================================
    # PHASE 2: Deep JTBD Analysis
    # ========================================
    deep_results = run_deep_analysis(df, extraction_df)

    if deep_results:
        deep_df = pd.DataFrame(deep_results)
        deep_df.to_csv(f"{ANALYZED_DIR}/deep_jtbd.csv", index=False)
        print(f"   💾 Saved: {ANALYZED_DIR}/deep_jtbd.csv")

    # ========================================
    # PHASE 3: Merge Everything
    # ========================================
    print(f"\n{'='*60}")
    print("🔗 PHASE 3: Merging analysis layers")

    final_df = df.merge(
        extraction_df,
        left_on='id',
        right_on='id',
        how='left',
        suffixes=('', '_extracted')
    )

    if deep_results:
        deep_lookup = {r['original_id']: r for r in deep_results}
        final_df['deep_jtbd'] = final_df['id'].map(lambda x: json.dumps(deep_lookup.get(x, {})))

    output_path = f"{ANALYZED_DIR}/analyzed_reviews.csv"
    final_df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE!")
    print(f"   Total records: {len(final_df)}")
    print(f"   With extractions: {extraction_df['pain_point'].notna().sum()}")
    print(f"   With deep JTBD: {len(deep_results)}")
    print(f"   Output: {output_path}")

    # Quick stats
    if 'pain_category' in final_df.columns:
        print(f"\n📊 Top pain categories:")
        print(final_df['pain_category'].value_counts().head(5).to_string())

    if 'sentiment' in final_df.columns:
        print(f"\n📊 Sentiment distribution:")
        print(final_df['sentiment'].value_counts().to_string())

    print(f"\n📁 All output files:")
    for f in sorted(os.listdir(ANALYZED_DIR)):
        fpath = os.path.join(ANALYZED_DIR, f)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"   - {f} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
