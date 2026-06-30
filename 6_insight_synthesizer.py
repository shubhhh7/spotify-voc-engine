"""
Insight Synthesizer - TURBO VERSION
Uses Gemini 1.5 Pro with higher rate limits.

Run: python 6_insight_synthesizer.py
Input: data/analyzed/analyzed_reviews.csv
Output: data/final/ directory
"""
import google.generativeai as genai
import pandas as pd
import json
import os
from collections import Counter
import config_turbo as config
import prompts

genai.configure(api_key=config.GEMINI_API_KEY)
pro_model = genai.GenerativeModel(config.GEMINI_PRO_MODEL)

def safe_json_parse(text):
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
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        return None

def generate_data_summary(df):
    summary = {
        "total_records": len(df),
        "sources": df['source'].value_counts().to_dict(),
    }
    if 'date' in df.columns:
        summary["date_range"] = f"{df['date'].min()} to {df['date'].max()}"
    if 'pain_point' in df.columns:
        summary["pain_point_rate"] = f"{(df['pain_point'] == True).mean():.1%}"
    if 'sentiment' in df.columns:
        summary["sentiment_dist"] = df['sentiment'].value_counts().to_dict()
    if 'rating' in df.columns:
        summary["avg_rating"] = f"{df['rating'].mean():.2f}"
    return json.dumps(summary, indent=2)

def generate_themes(df):
    themes = []
    if 'pain_category' in df.columns:
        cat_counts = df['pain_category'].value_counts().head(10)
        for cat, count in cat_counts.items():
            if cat and cat != "None":
                themes.append(f"{cat}: {count} mentions")
    if 'unmet_need' in df.columns:
        needs = df['unmet_need'].dropna()
        needs = needs[needs != "Unclear"]
        top_needs = needs.value_counts().head(10)
        for need, count in top_needs.items():
            themes.append(f"Need: {need}: {count}")
    return "\n".join(themes[:30])

def generate_jtbd_list(df):
    jtbd_list = []
    if 'jtbd_statement' in df.columns:
        jtbds = df['jtbd_statement'].dropna()
        jtbds = jtbds[jtbds != "Unclear"]
        for jtbd in jtbds.head(20):
            jtbd_list.append(jtbd)
    return "\n".join(jtbd_list)

def generate_segment_signals(df):
    signals = []
    if 'user_segment_hint' in df.columns:
        segments = df['user_segment_hint'].value_counts().head(10)
        for seg, count in segments.items():
            if seg and seg != "None":
                signals.append(f"{seg}: {count}")
    if 'listening_context' in df.columns:
        contexts = df['listening_context'].value_counts().head(5)
        for ctx, count in contexts.items():
            if ctx:
                signals.append(f"Context {ctx}: {count}")
    return "\n".join(signals)

def generate_complaints(df):
    complaints = []
    severe = df[(df['pain_point'] == True) & (df['text_clean'].str.len() > 50)].head(30)
    for _, row in severe.iterrows():
        complaints.append(f"[{row['source']}] {row['text_clean'][:300]}")
    return "\n\n".join(complaints)

def run_synthesis(df):
    print("\n🧠 Cross-Source Theme Synthesis...")

    data_summary = generate_data_summary(df)
    themes = generate_themes(df)
    jtbd_list = generate_jtbd_list(df)
    segment_signals = generate_segment_signals(df)

    prompt = prompts.SYNTHESIS_PROMPT.format(
        data_summary=data_summary,
        themes=themes,
        jtbd_list=jtbd_list,
        segment_signals=segment_signals
    )

    try:
        response = pro_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=8192
            )
        )
        result = safe_json_parse(response.text)
        if result:
            return result
        else:
            return {"raw_text": response.text, "parse_error": True}
    except Exception as e:
        print(f"   ❌ Synthesis error: {e}")
        return None

def run_competitive_analysis(df):
    print("\n⚔️ Competitive Analysis...")

    complaints = generate_complaints(df)
    prompt = prompts.COMPETITIVE_PROMPT.format(complaints=complaints)

    try:
        response = pro_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096
            )
        )
        result = safe_json_parse(response.text)
        return result if result else {"raw_text": response.text}
    except Exception as e:
        print(f"   ❌ Competitive analysis error: {e}")
        return None

def run_final_report(df, insights, competitive):
    print("\n📄 Final Report...")

    insights_text = json.dumps(insights, indent=2) if insights else "No insights generated"

    prompt = prompts.REPORT_PROMPT.format(
        volume=len(df),
        sources=df['source'].nunique(),
        insights=insights_text
    )

    try:
        response = pro_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=8192
            )
        )
        return response.text
    except Exception as e:
        print(f"   ❌ Report generation error: {e}")
        return None

def main():
    print("🔮 TURBO Insight Synthesis")

    input_path = f"{config.ANALYZED_DIR}/analyzed_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ Analyzed data not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    print(f"📊 Loaded {len(df)} analyzed records")

    insights = run_synthesis(df)
    competitive = run_competitive_analysis(df)
    report = run_final_report(df, insights, competitive)

    if insights:
        with open(f"{config.FINAL_DIR}/synthesis.json", "w") as f:
            json.dump(insights, f, indent=2)
        print(f"   ✅ synthesis.json")

    if competitive:
        with open(f"{config.FINAL_DIR}/competitive.json", "w") as f:
            json.dump(competitive, f, indent=2)
        print(f"   ✅ competitive.json")

    if report:
        with open(f"{config.FINAL_DIR}/executive_report.txt", "w") as f:
            f.write(report)
        print(f"   ✅ executive_report.txt")

    # Generate summary tables
    print("\n📊 Summary tables...")

    if 'pain_category' in df.columns:
        pain_summary = df['pain_category'].value_counts().head(10).reset_index()
        pain_summary.columns = ['Pain Category', 'Count']
        pain_summary.to_csv(f"{config.FINAL_DIR}/pain_summary.csv", index=False)
        print(f"   ✅ pain_summary.csv")

    if 'unmet_need' in df.columns:
        needs = df['unmet_need'].dropna()
        needs = needs[needs != "Unclear"]
        need_summary = needs.value_counts().head(15).reset_index()
        need_summary.columns = ['Unmet Need', 'Count']
        need_summary.to_csv(f"{config.FINAL_DIR}/needs_summary.csv", index=False)
        print(f"   ✅ needs_summary.csv")

    if 'user_segment_hint' in df.columns:
        seg_summary = df['user_segment_hint'].value_counts().head(10).reset_index()
        seg_summary.columns = ['Segment', 'Count']
        seg_summary.to_csv(f"{config.FINAL_DIR}/segment_summary.csv", index=False)
        print(f"   ✅ segment_summary.csv")

    if 'pain_severity' in df.columns and 'key_quote' in df.columns:
        severe_quotes = df[df['pain_point'] == True].nlargest(20, 'pain_severity')[['id', 'source', 'pain_category', 'pain_severity', 'key_quote', 'text_clean']]
        severe_quotes.to_csv(f"{config.FINAL_DIR}/top_evidence.csv", index=False)
        print(f"   ✅ top_evidence.csv")

    print(f"\n{'='*60}")
    print(f"✅ Synthesis complete! All outputs in {config.FINAL_DIR}/")
    for f in os.listdir(config.FINAL_DIR):
        print(f"   - {f}")

if __name__ == "__main__":
    main()
