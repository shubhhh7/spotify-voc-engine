"""
Quick Validation Script - 30-minute audit
Run this after AI analysis to spot-check quality.

Usage: python quick_validate.py
Input: data/analyzed/analyzed_reviews.csv
Output: Console report + validation_log.txt
"""
import pandas as pd
import os
import config_turbo as config

def validate_quotes(df, n=20):
    """Check if key_quote exists in source text."""
    print("\n🔍 Validating key quotes...")
    issues = []
    checked = 0

    sample = df[df['key_quote'].notna()].sample(min(n, len(df)))
    for _, row in sample.iterrows():
        quote = str(row['key_quote']).strip().lower()
        text = str(row['text_clean']).lower()
        checked += 1

        if quote and quote not in text and quote[:20] not in text:
            issues.append({
                'id': row['id'],
                'quote': row['key_quote'],
                'text_preview': row['text_clean'][:100]
            })

    accuracy = (checked - len(issues)) / checked * 100 if checked > 0 else 0
    print(f"   Checked: {checked} | Issues: {len(issues)} | Accuracy: {accuracy:.1f}%")

    if issues:
        print("   ⚠️ Sample issues:")
        for issue in issues[:3]:
            print(f"      ID {issue['id']}: Quote not found in text")

    return accuracy, issues

def validate_categories(df):
    """Check category distribution for anomalies."""
    print("\n📊 Validating categories...")

    if 'pain_category' not in df.columns:
        print("   ⚠️ No pain_category column")
        return None

    cats = df['pain_category'].value_counts()
    print(f"   Categories: {len(cats)}")
    print(cats.head(8).to_string())

    # Check for "None" overload
    none_pct = (df['pain_category'] == 'None').mean() * 100
    print(f"\n   'None' category: {none_pct:.1f}%")
    if none_pct > 40:
        print("   ⚠️ WARNING: >40% categorized as 'None' — prompt may be too strict")

    return cats

def validate_severity(df):
    """Check severity distribution."""
    print("\n📈 Validating severity...")

    if 'pain_severity' not in df.columns:
        print("   ⚠️ No pain_severity column")
        return None

    sev = pd.to_numeric(df['pain_severity'], errors='coerce').dropna()
    print(f"   Mean severity: {sev.mean():.2f}")
    print(f"   Distribution:")
    print(sev.value_counts().sort_index().to_string())

    if sev.mean() < 2.5:
        print("   ⚠️ WARNING: Mean severity < 2.5 — AI may be under-scoring")
    if sev.mean() > 4.0:
        print("   ⚠️ WARNING: Mean severity > 4.0 — AI may be over-scoring")

    return sev

def validate_confidence(df):
    """Check confidence scores."""
    print("\n🎯 Validating confidence...")

    if 'confidence' not in df.columns:
        print("   ⚠️ No confidence column")
        return None

    conf = pd.to_numeric(df['confidence'], errors='coerce').dropna()
    low_conf = (conf <= 2).mean() * 100
    print(f"   Low confidence (≤2): {low_conf:.1f}%")

    if low_conf > 30:
        print("   ⚠️ WARNING: >30% low confidence — consider re-running with better prompts")

    return conf

def generate_validation_report(df):
    """Generate full validation report."""
    print("\n" + "="*60)
    print("VALIDATION REPORT")
    print("="*60)

    report_lines = ["VALIDATION REPORT\n", "="*60 + "\n"]

    # 1. Data volume
    print(f"\n📊 Total records: {len(df)}")
    report_lines.append(f"Total records: {len(df)}\n")

    # 2. Quote validation
    quote_acc, quote_issues = validate_quotes(df, 20)
    report_lines.append(f"Quote accuracy: {quote_acc:.1f}%\n")
    report_lines.append(f"Quote issues: {len(quote_issues)}\n")

    # 3. Categories
    cats = validate_categories(df)
    if cats is not None:
        report_lines.append(f"Categories: {len(cats)}\n")

    # 4. Severity
    sev = validate_severity(df)
    if sev is not None:
        report_lines.append(f"Mean severity: {sev.mean():.2f}\n")

    # 5. Confidence
    conf = validate_confidence(df)
    if conf is not None:
        report_lines.append(f"Low confidence rate: {(conf <= 2).mean()*100:.1f}%\n")

    # 6. Source balance
    print("\n📊 Source balance:")
    source_dist = df['source'].value_counts()
    print(source_dist.to_string())
    report_lines.append(f"Source distribution: {dict(source_dist)}\n")

    # 7. Pain point rate
    if 'pain_point' in df.columns:
        pain_rate = (df['pain_point'] == True).mean() * 100
        print(f"\n📊 Pain point rate: {pain_rate:.1f}%")
        report_lines.append(f"Pain point rate: {pain_rate:.1f}%\n")
        if pain_rate < 20:
            print("   ⚠️ WARNING: <20% pain points — data may be too positive or prompt too strict")
        if pain_rate > 80:
            print("   ⚠️ WARNING: >80% pain points — data may be biased or prompt too loose")

    # 8. Top evidence check
    print("\n📊 Top 5 evidence quotes:")
    if 'pain_severity' in df.columns:
        top = df[df['pain_point'] == True].nlargest(5, 'pain_severity')[['source', 'pain_category', 'pain_severity', 'key_quote']]
        print(top.to_string())

    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)

    # Save report
    with open(f"{config.FINAL_DIR}/validation_log.txt", "w") as f:
        f.writelines(report_lines)
    print(f"\n📁 Report saved: {config.FINAL_DIR}/validation_log.txt")

def main():
    print("⚡ Quick Validation - 30-minute audit")

    input_path = f"{config.ANALYZED_DIR}/analyzed_reviews.csv"
    if not os.path.exists(input_path):
        print(f"❌ Analyzed data not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    generate_validation_report(df)

    print("\n✅ Validation complete. Review the report above.")
    print("If accuracy < 80% or warnings appear, consider re-running analysis.")

if __name__ == "__main__":
    main()
