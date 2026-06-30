"""
Gemini AI Analyzer - TURBO VERSION
Optimized for Google Pro subscription with larger batches and faster rate limits.

Run: python 5_gemini_analyzer.py
Input: data/clean/merged_reviews.csv
Output: data/analyzed/analyzed_reviews.csv
"""
import google.generativeai as genai
import pandas as pd
import json
import time
from tqdm import tqdm
import config_turbo as config
import prompts
import os

genai.configure(api_key=config.GEMINI_API_KEY)
flash_model = genai.GenerativeModel(config.GEMINI_FLASH_MODEL)
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
    except json.JSONDecodeError:
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

def analyze_batch(batch_df, model, prompt_template, max_retries=3):
    entries = []
    for _, row in batch_df.iterrows():
        entry = f"""--- ENTRY ID: {row['id']} ---
Source: {row['source']}
Date: {row.get('date', 'unknown')}
Rating/Score: {row.get('rating', row.get('score', 'N/A'))}
Text: {row['text_clean']}
"""
        entries.append(entry)

    entries_text = "\n\n".join(entries)
    prompt = prompt_template.format(entries=entries_text)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192
                )
            )
            result = safe_json_parse(response.text)
            if result is not None:
                return result
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"   ⚠️ Rate limit hit. Waiting 60s...")
                time.sleep(60)
            else:
                print(f"   ⚠️ API error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)

    return None

def analyze_deep(text, source, rating, date, model, max_retries=3):
    prompt = prompts.JTBD_DEEP_PROMPT.format(
        text=text, source=source, rating=rating, date=date
    )

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096
                )
            )
            result = safe_json_parse(response.text)
            if result is not None:
                return result
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"   ⚠️ Pro rate limit. Waiting 120s...")
                time.sleep(120)
            else:
                print(f"   ⚠️ Deep analysis error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)

    return None

def main():
    print("🤖 TURBO Gemini AI Analyzer")
    print(f"Flash: {config.GEMINI_FLASH_MODEL} | Pro: {config.GEMINI_PRO_MODEL}")
    print(f"Batch size: {config.BATCH_SIZE} | Flash RPM: {config.FLASH_RPM} | Pro RPM: {config.PRO_RPM}")
    print("="*60)

    input_path = f"{config.CLEAN_DIR}/merged_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ Cleaned data not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    print(f"📊 Loaded {len(df)} records for analysis")

    # PHASE 1: Bulk Extraction (Flash)
    print(f"\n📦 PHASE 1: Bulk Extraction with Flash")
    total_batches = (len(df) + config.BATCH_SIZE - 1) // config.BATCH_SIZE
    print(f"   Batches to process: {total_batches}")
    print(f"   Estimated time: {total_batches * (60/config.FLASH_RPM) / 60:.1f} hours")

    all_extractions = []

    for i in tqdm(range(0, len(df), config.BATCH_SIZE), total=total_batches, desc="Flash batches"):
        batch = df.iloc[i:i+config.BATCH_SIZE]

        # Rate limiting with auto-throttle
        if i > 0:
            time.sleep(60 / config.FLASH_RPM)

        result = analyze_batch(batch, flash_model, prompts.EXTRACTION_PROMPT)

        if result and isinstance(result, list):
            for j, (_, row) in enumerate(batch.iterrows()):
                if j < len(result):
                    extraction = result[j]
                    extraction['original_id'] = row['id']
                    extraction['source'] = row['source']
                    all_extractions.append(extraction)
        else:
            for _, row in batch.iterrows():
                all_extractions.append({
                    'original_id': row['id'],
                    'source': row['source'],
                    'pain_point': None,
                    'error': 'analysis_failed'
                })

    print(f"\n✅ Bulk extraction: {len(all_extractions)} records")
    extraction_df = pd.DataFrame(all_extractions)
    extraction_df.to_csv(f"{config.ANALYZED_DIR}/extractions.csv", index=False)

    # PHASE 2: Deep JTBD (Pro) - Top 40 most severe
    print(f"\n🔬 PHASE 2: Deep JTBD Analysis with Pro")

    severe_mask = extraction_df['pain_point'] == True
    severe_df = extraction_df[severe_mask].copy() if severe_mask.any() else extraction_df.head(80)
    severe_df['severity_score'] = pd.to_numeric(severe_df.get('pain_severity', 0), errors='coerce').fillna(0)
    top_texts = severe_df.nlargest(40, 'severity_score')

    print(f"   Analyzing top {len(top_texts)} severe items...")

    deep_results = []
    for idx, row in tqdm(top_texts.iterrows(), total=len(top_texts), desc="Pro deep analysis"):
        original = df[df['id'] == row['original_id']]
        if len(original) == 0:
            continue
        original = original.iloc[0]

        if len(str(original['text_clean'])) > 80:
            time.sleep(60 / config.PRO_RPM)

            result = analyze_deep(
                original['text_clean'],
                original['source'],
                original.get('rating', original.get('score', 'N/A')),
                original.get('date', 'unknown'),
                pro_model
            )

            if result:
                result['original_id'] = row['original_id']
                deep_results.append(result)

    print(f"\n✅ Deep analysis: {len(deep_results)} records")

    if deep_results:
        deep_df = pd.DataFrame(deep_results)
        deep_df.to_csv(f"{config.ANALYZED_DIR}/deep_jtbd.csv", index=False)

    # PHASE 3: Merge
    print(f"\n🔗 PHASE 3: Merging analysis layers")
    final_df = df.merge(
        extraction_df,
        left_on='id',
        right_on='original_id',
        how='left',
        suffixes=('', '_extracted')
    )

    if deep_results:
        deep_lookup = {r['original_id']: r for r in deep_results}
        final_df['deep_jtbd'] = final_df['id'].map(lambda x: json.dumps(deep_lookup.get(x, {})))

    output_path = f"{config.ANALYZED_DIR}/analyzed_reviews.csv"
    final_df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ Analysis complete!")
    print(f"   Total: {len(final_df)} | With extractions: {extraction_df['pain_point'].notna().sum()}")
    print(f"   With deep JTBD: {len(deep_results)}")
    print(f"   Saved: {output_path}")

    if 'pain_category' in final_df.columns:
        print("\n📊 Top pain categories:")
        print(final_df['pain_category'].value_counts().head(5).to_string())

    if 'sentiment' in final_df.columns:
        print("\n📊 Sentiment:")
        print(final_df['sentiment'].value_counts().to_string())

    # Auto-generate web backup prompts as insurance
    print("\n🌐 Generating web backup prompts...")
    try:
        import gemini_web_backup
        gemini_web_backup.generate_web_prompts(final_df)
    except Exception as e:
        print(f"   ⚠️ Web backup generation failed: {e}")

if __name__ == "__main__":
    main()
