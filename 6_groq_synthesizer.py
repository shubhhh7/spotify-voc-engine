"""
Groq Insight Synthesizer - Small Chunk Processing
Processes analyzed data through Groq in small batches per source,
then merges insights into final strategic output.

Strategy:
- Synthesize per-source summaries first (small payloads)
- Then combine summaries into final strategic insights
- Never sends more than ~2000 tokens of data per request

Run: python 6_groq_synthesizer.py
Input: data/analyzed/analyzed_reviews.csv
Output: data/final/ directory
"""

import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
import requests as req

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"

REQUESTS_PER_MINUTE = 28
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE

# Directories
OUTPUT_DIR = "data"
ANALYZED_DIR = f"{OUTPUT_DIR}/analyzed"
FINAL_DIR = f"{OUTPUT_DIR}/final"
os.makedirs(FINAL_DIR, exist_ok=True)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


# ============================================================
# GROQ CLIENT
# ============================================================

def call_groq(prompt, system_prompt=None, model=None, max_tokens=4096, temperature=0.3, max_retries=3):
    """Call Groq API with small payload safety."""
    if model is None:
        model = GROQ_MODEL
    if system_prompt is None:
        system_prompt = "You are a senior product insights analyst at Spotify. Always respond with valid JSON only."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            response = req.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return safe_json_parse(content)

            elif response.status_code == 413 or "payload too large" in response.text.lower():
                print(f"   ⚠️ Payload too large!")
                return None

            elif response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                print(f"   ⚠️ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)

            elif response.status_code == 400 and model != GROQ_FALLBACK_MODEL:
                print(f"   ⚠️ Trying fallback model...")
                return call_groq(prompt, system_prompt, GROQ_FALLBACK_MODEL,
                               max_tokens=2048, temperature=temperature, max_retries=2)
            else:
                print(f"   ❌ API error {response.status_code}: {response.text[:200]}")
                time.sleep(5)

        except Exception as e:
            print(f"   ❌ Error (attempt {attempt+1}): {e}")
            time.sleep(5)

    return None


def safe_json_parse(text):
    """Parse JSON from response."""
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
    except:
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
        return None


# ============================================================
# PER-SOURCE SUMMARY (Small Payloads)
# ============================================================

def summarize_source(df, source_name, max_items=30):
    """Generate a compact summary for one source to keep payload small."""
    source_df = df[df['source'].str.lower().str.contains(source_name.lower())]
    if len(source_df) == 0:
        return None

    # Build a concise data summary (not full text - just stats + key quotes)
    summary_parts = []
    summary_parts.append(f"Source: {source_name} ({len(source_df)} reviews)")

    # Sentiment distribution
    if 'sentiment' in source_df.columns:
        sent = source_df['sentiment'].value_counts().head(5).to_dict()
        summary_parts.append(f"Sentiment: {sent}")

    # Pain categories
    if 'pain_category' in source_df.columns:
        cats = source_df['pain_category'].dropna()
        cats = cats[cats != "None"]
        if len(cats) > 0:
            summary_parts.append(f"Pain categories: {cats.value_counts().head(5).to_dict()}")

    # Top pain severity items with key quotes
    if 'pain_severity' in source_df.columns and 'key_quote' in source_df.columns:
        severe = source_df.nlargest(min(10, len(source_df)), 'pain_severity')
        quotes = severe['key_quote'].dropna().head(8).tolist()
        if quotes:
            summary_parts.append(f"Key quotes: {quotes}")

    # JTBD statements
    if 'jtbd_statement' in source_df.columns:
        jtbds = source_df['jtbd_statement'].dropna()
        jtbds = jtbds[jtbds != "Unclear"]
        if len(jtbds) > 0:
            summary_parts.append(f"JTBDs: {jtbds.head(5).tolist()}")

    # Unmet needs
    if 'unmet_need' in source_df.columns:
        needs = source_df['unmet_need'].dropna()
        if len(needs) > 0:
            summary_parts.append(f"Top unmet needs: {needs.value_counts().head(5).to_dict()}")

    data_text = "\n".join(summary_parts)

    # Keep prompt concise
    prompt = f"""Summarize the key insights from this {source_name} data about Spotify user experience.

DATA:
{data_text}

Return JSON with:
- "source": "{source_name}"
- "total_reviews": number
- "top_3_pain_points": array of strings (concise)
- "dominant_sentiment": string
- "key_jtbd": most important job-to-be-done
- "biggest_unmet_need": string
- "churn_signals": array of strings (max 3)
- "notable_quotes": array of 3 most impactful quotes"""

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return call_groq(prompt, max_tokens=1024)


# ============================================================
# STRATEGIC SYNTHESIS (Combines per-source summaries)
# ============================================================

def run_strategic_synthesis(source_summaries):
    """Combine per-source summaries into strategic insights. Sends only summaries, not raw data."""
    print("\n🧠 Strategic Synthesis (combining source summaries)...")

    # Build concise input from summaries
    summaries_text = ""
    for s in source_summaries:
        if s:
            summaries_text += json.dumps(s, indent=1)[:800] + "\n---\n"

    # Keep under payload limit by truncating
    if len(summaries_text) > 6000:
        summaries_text = summaries_text[:6000] + "\n[truncated]"

    prompt = f"""You are VP of Product Insights at Spotify. Based on these cross-source summaries, provide strategic insights.

SOURCE SUMMARIES:
{summaries_text}

Return JSON with:
- "executive_summary": array of 3 bullet strings (max 30 words each)
- "strategic_insights": array of 5 objects, each with: "insight", "evidence", "business_impact", "severity" (1-10), "recommendation"
- "discovery_problems": array of 3 objects with "problem", "root_cause", "frequency"
- "recommendation_frustrations": array of 3 objects with "frustration", "scenario", "emotional_tone"
- "unmet_needs": array of 5 objects with "need", "frequency", "opportunity_size"
- "opportunity_scoring": array of 3 objects with "opportunity", "impact" (1-10), "effort" (1-10), "rationale"
"""

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return call_groq(prompt, max_tokens=4096, temperature=0.3)


def run_competitive_analysis(df, max_complaints=15):
    """Run competitive analysis with a small subset of complaints."""
    print("\n⚔️ Competitive Analysis...")

    # Get top severe complaints - only send a small number
    severe = df[(df.get('pain_point', pd.Series([False]*len(df))) == True)]
    if 'pain_severity' in severe.columns:
        severe = severe.nlargest(max_complaints, 'pain_severity')
    else:
        severe = severe.head(max_complaints)

    complaints = []
    for _, row in severe.iterrows():
        text = str(row.get('text_clean', row.get('text', '')))[:200]
        complaints.append(f"[{row.get('source', '?')}] {text}")

    complaints_text = "\n".join(complaints[:max_complaints])

    prompt = f"""As a competitive intelligence analyst, analyze these Spotify user complaints and infer competitive threats.

TOP USER COMPLAINTS:
{complaints_text}

Return JSON with:
- "competitive_threats": array of 3-4 objects with "competitor", "advantage", "severity"
- "switching_signals": array of 3 strings
- "defensible_advantages": array of 3 things Spotify still does well
- "vulnerable_areas": array of 3 objects with "area", "severity" (1-10), "recommended_response"
"""

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return call_groq(prompt, max_tokens=2048)


def run_final_report(df, insights, competitive):
    """Generate executive report from pre-computed insights (no raw data sent)."""
    print("\n📄 Executive Report Generation...")

    # Build concise context from insights
    context = f"Total reviews analyzed: {len(df)}\nSources: {df['source'].nunique()}\n"

    if insights:
        context += f"Key insights: {json.dumps(insights.get('executive_summary', []))}\n"
        context += f"Top opportunities: {json.dumps(insights.get('opportunity_scoring', [])[:3])}\n"

    if competitive:
        context += f"Competitive threats: {json.dumps(competitive.get('competitive_threats', [])[:3])}\n"

    # Truncate context to stay safe
    context = context[:4000]

    prompt = f"""Write a concise executive report for Spotify leadership on VoC research findings.

CONTEXT:
{context}

Return JSON with:
- "bottom_line": 3-sentence summary of the most critical finding
- "what_we_heard": 200-word narrative of user reality with specific quotes
- "key_stats": array of 5 bullet-point statistics
- "user_archetypes": array of 3 objects with "name", "description", "key_pain", "quote"
- "top_5_opportunities": array of 5 objects with "opportunity", "impact", "effort", "rationale"
- "risks_of_inaction": array of 3 strings
- "next_steps": array of 3 time-bound actions
"""

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return call_groq(prompt, max_tokens=4096, temperature=0.4)


# ============================================================
# MAIN
# ============================================================

def main():
    print("🔮 Groq Insight Synthesizer - Small Chunk Processing")
    print(f"Model: {GROQ_MODEL}")
    print("=" * 60)

    if GROQ_API_KEY == "your_groq_api_key_here" or not GROQ_API_KEY:
        print("❌ Please set GROQ_API_KEY in your .env file!")
        return

    input_path = f"{ANALYZED_DIR}/analyzed_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ Analyzed data not found: {input_path}")
        print("   Run 5_groq_analyzer.py first!")
        return

    df = pd.read_csv(input_path)
    print(f"📊 Loaded {len(df)} analyzed records")

    # Identify sources
    sources = df['source'].dropna().unique()
    print(f"📂 Sources: {list(sources)}")

    # ========================================
    # Step 1: Per-source summaries (small payloads)
    # ========================================
    print(f"\n{'='*60}")
    print("📊 Step 1: Per-Source Summaries")

    source_summaries = []
    for source in sources:
        print(f"   Processing: {source}")
        summary = summarize_source(df, source)
        if summary:
            source_summaries.append(summary)
            print(f"   ✅ {source} summarized")
        else:
            print(f"   ⚠️ {source} - no summary generated")

    # Save per-source summaries
    with open(f"{FINAL_DIR}/source_summaries.json", "w") as f:
        json.dump(source_summaries, f, indent=2)
    print(f"   💾 Saved: source_summaries.json")

    # ========================================
    # Step 2: Strategic synthesis
    # ========================================
    print(f"\n{'='*60}")
    print("🧠 Step 2: Strategic Synthesis")

    insights = run_strategic_synthesis(source_summaries)
    if insights:
        with open(f"{FINAL_DIR}/synthesis.json", "w") as f:
            json.dump(insights, f, indent=2)
        print(f"   ✅ synthesis.json saved")
    else:
        print(f"   ⚠️ Synthesis failed - check API key/limits")

    # ========================================
    # Step 3: Competitive analysis
    # ========================================
    print(f"\n{'='*60}")
    print("⚔️ Step 3: Competitive Analysis")

    competitive = run_competitive_analysis(df)
    if competitive:
        with open(f"{FINAL_DIR}/competitive.json", "w") as f:
            json.dump(competitive, f, indent=2)
        print(f"   ✅ competitive.json saved")

    # ========================================
    # Step 4: Executive report
    # ========================================
    print(f"\n{'='*60}")
    print("📄 Step 4: Executive Report")

    report = run_final_report(df, insights, competitive)
    if report:
        with open(f"{FINAL_DIR}/executive_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"   ✅ executive_report.json saved")

    # ========================================
    # Step 5: Summary tables
    # ========================================
    print(f"\n{'='*60}")
    print("📊 Step 5: Summary Tables")

    if 'pain_category' in df.columns:
        pain_summary = df['pain_category'].value_counts().head(10).reset_index()
        pain_summary.columns = ['Pain Category', 'Count']
        pain_summary.to_csv(f"{FINAL_DIR}/pain_summary.csv", index=False)
        print(f"   ✅ pain_summary.csv")

    if 'unmet_need' in df.columns:
        needs = df['unmet_need'].dropna()
        needs = needs[needs != "Unclear"]
        if len(needs) > 0:
            need_summary = needs.value_counts().head(15).reset_index()
            need_summary.columns = ['Unmet Need', 'Count']
            need_summary.to_csv(f"{FINAL_DIR}/needs_summary.csv", index=False)
            print(f"   ✅ needs_summary.csv")

    if 'user_segment_hint' in df.columns:
        seg_summary = df['user_segment_hint'].value_counts().head(10).reset_index()
        seg_summary.columns = ['Segment', 'Count']
        seg_summary.to_csv(f"{FINAL_DIR}/segment_summary.csv", index=False)
        print(f"   ✅ segment_summary.csv")

    if 'sentiment' in df.columns:
        sent_summary = df['sentiment'].value_counts().reset_index()
        sent_summary.columns = ['Sentiment', 'Count']
        sent_summary.to_csv(f"{FINAL_DIR}/sentiment_summary.csv", index=False)
        print(f"   ✅ sentiment_summary.csv")

    # ========================================
    # Done!
    # ========================================
    print(f"\n{'='*60}")
    print(f"✅ SYNTHESIS COMPLETE!")
    print(f"   All outputs in: {FINAL_DIR}/")
    for f_name in sorted(os.listdir(FINAL_DIR)):
        fpath = os.path.join(FINAL_DIR, f_name)
        if os.path.isfile(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            print(f"   - {f_name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
