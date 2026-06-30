"""
GEMINI WEB BACKUP - Manual Synthesis Mode
If you hit API rate limits, use this script to generate formatted prompts
that you can paste into Gemini Advanced (web interface) for free.

Your Google Pro subscription includes Gemini Advanced web access.
This has NO rate limits for chat - you can paste massive prompts.

Usage: python gemini_web_backup.py
Input: data/analyzed/analyzed_reviews.csv
Output: data/final/web_prompts/ → Formatted text files ready to paste
"""
import pandas as pd
import os
import json
import config

def generate_web_prompts(df):
    """Generate prompts formatted for Gemini Advanced web interface."""

    os.makedirs(f"{config.FINAL_DIR}/web_prompts", exist_ok=True)

    # Prompt 1: Theme Extraction (paste into Gemini Advanced)
    print("\n📝 Generating Web Prompt 1: Theme Extraction...")

    # Get top 100 most severe pain points for manual analysis
    severe = df[df['pain_point'] == True].nlargest(100, 'pain_severity') if 'pain_severity' in df.columns else df.head(100)

    evidence_text = []
    for i, (_, row) in enumerate(severe.iterrows(), 1):
        evidence_text.append(f"""[{i}] Source: {row['source']} | Rating: {row.get('rating', 'N/A')}
Text: {row['text_clean'][:400]}
---""")

    theme_prompt = f"""You are a Senior Product Insights Analyst at Spotify. I have collected user feedback about music discovery and recommendations. 

Below are 100 user feedback entries. Your task is to:
1. Read all entries and identify recurring themes about music discovery struggles
2. Group them into 8-10 clear categories (e.g., "Algorithm Repetition", "Discovery UI Confusion", "Playlist Stagnation")
3. For each theme, provide: 
   - Theme name
   - Frequency (how many of the 100 entries mention this)
   - Severity (1-10)
   - 2-3 exact user quotes as evidence
   - The root cause you infer
   - The user segment most affected

USER FEEDBACK ENTRIES:
{"\n\n".join(evidence_text)}

OUTPUT FORMAT:
Return a structured list. Be specific. Do not generalize. Every claim must be anchored to a specific quote above.
"""

    with open(f"{config.FINAL_DIR}/web_prompts/01_theme_extraction.txt", "w", encoding="utf-8") as f:
        f.write(theme_prompt)

    # Prompt 2: JTBD Deep Dive
    print("📝 Generating Web Prompt 2: JTBD Analysis...")

    long_posts = df[df['text_clean'].str.len() > 200].head(30)
    jtbd_text = []
    for i, (_, row) in enumerate(long_posts.iterrows(), 1):
        jtbd_text.append(f"""[{i}] Source: {row['source']}
Text: {row['text_clean'][:600]}
---""")

    jtbd_prompt = f"""You are a Jobs-to-be-Done researcher specializing in music consumption.

Below are 30 detailed user posts about Spotify. For each post, extract:
1. The primary JTBD: "When I [situation], I want to [motivation], so I can [outcome]"
2. The emotional trigger that drove the post
3. The "struggle moment" - when did Spotify fail them?
4. What workaround are they using instead?
5. What would make them switch to Apple Music/YouTube Music?

Then synthesize across all 30:
- 4 distinct user segments with names, behaviors, and unmet needs
- 5 consistent unmet needs across the dataset
- 3 "contrarian" insights that go against obvious assumptions

USER POSTS:
{"\n\n".join(jtbd_text)}

OUTPUT: Structured analysis. Be specific and evidence-based.
"""

    with open(f"{config.FINAL_DIR}/web_prompts/02_jtbd_analysis.txt", "w", encoding="utf-8") as f:
        f.write(jtbd_prompt)

    # Prompt 3: Opportunity Scoring
    print("📝 Generating Web Prompt 3: Opportunity Scoring...")

    # Use synthesis data if available, otherwise use top themes
    opp_prompt = f"""You are a Growth PM at Spotify. Based on the following user pain points, score opportunities using ICE framework.

PAIN POINTS (from previous analysis):
{generate_pain_summary(df)}

For each opportunity:
- Impact (1-10): User + business value
- Confidence (1-10): Evidence strength  
- Ease (1-10): Technical + organizational feasibility
- ICE Score = (Impact × Confidence) / Ease

Rank top 8 opportunities. For each, provide:
- Opportunity name
- ICE score
- User evidence (specific quotes)
- Why this beats the status quo
- Risk of NOT doing this

OUTPUT: Ranked table with rationale.
"""

    with open(f"{config.FINAL_DIR}/web_prompts/03_opportunity_scoring.txt", "w", encoding="utf-8") as f:
        f.write(opp_prompt)

    # Prompt 4: Executive Narrative
    print("📝 Generating Web Prompt 4: Executive Report...")

    exec_prompt = f"""You are a Senior PM presenting a VoC research readout to Spotify leadership.

CONTEXT:
- Analyzed {len(df)} user feedback entries from Reddit, App Store, Play Store
- Focus: Music discovery, recommendations, listening behavior
- Time: Recent 12 months

Write a 2-page executive report with:
1. Bottom line up front (3 sentences max)
2. What we heard (narrative, 300 words, use visceral language, specific quotes)
3. The data (5 bullet points with numbers)
4. 3 user archetypes (names, quotes, behaviors)
5. 5 ranked opportunities (1 sentence each + ICE score)
6. 3 risks of inaction (business impact, specific)
7. 3 recommended next steps (time-bound, specific)

WRITING STYLE: McKinsey precision + product intuition. No buzzwords. Every claim anchored to evidence.

SUPPORTING DATA:
{generate_data_summary(df)}

OUTPUT: Plain text with clear headers.
"""

    with open(f"{config.FINAL_DIR}/web_prompts/04_executive_report.txt", "w", encoding="utf-8") as f:
        f.write(exec_prompt)

    print(f"\n✅ Web prompts saved to {config.FINAL_DIR}/web_prompts/")
    print("\n📋 INSTRUCTIONS:")
    print("   1. Open Gemini Advanced (gemini.google.com)")
    print("   2. Copy-paste each .txt file into a new chat")
    print("   3. Let Gemini process (it handles 1M tokens)")
    print("   4. Save outputs and use them if API pipeline fails")

def generate_pain_summary(df):
    """Generate pain point summary for opportunity prompt."""
    lines = []
    if 'pain_category' in df.columns:
        cats = df['pain_category'].value_counts().head(8)
        for cat, count in cats.items():
            if cat and cat != "None":
                lines.append(f"- {cat}: {count} mentions")
    return "\n".join(lines) if lines else "Pain point data not yet analyzed."

def generate_data_summary(df):
    """Generate data summary for executive prompt."""
    summary = []
    summary.append(f"Total records: {len(df)}")
    if 'source' in df.columns:
        summary.append(f"Sources: {dict(df['source'].value_counts())}")
    if 'pain_point' in df.columns:
        summary.append(f"Pain points: {(df['pain_point'] == True).sum()}")
    return "\n".join(summary)

def main():
    print("🌐 Gemini Web Backup Mode")
    print("Generating manual prompts for Gemini Advanced web interface...")

    input_path = f"{config.ANALYZED_DIR}/analyzed_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ Analyzed data not found. Run turbo_pipeline.py first.")
        return

    df = pd.read_csv(input_path)
    generate_web_prompts(df)

if __name__ == "__main__":
    main()
