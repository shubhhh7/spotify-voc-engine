"""
TURBO PIPELINE - Spotify VoC Research
Single command: python turbo_pipeline.py
Runs: Collection → Cleaning → Analysis → Synthesis in sequence
Optimized for 2-day completion with Google Pro subscription.

This script orchestrates all steps. If any step fails, it prints
what to do and exits so you can fix it without losing progress.
"""
import subprocess
import sys
import time
import os

def run_step(script_name, description):
    """Run a pipeline step and handle errors."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")

    result = subprocess.run([sys.executable, script_name], capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ STEP FAILED: {script_name}")
        print(f"Fix the issue above, then re-run: python turbo_pipeline.py")
        sys.exit(1)

    print(f"\n✅ STEP COMPLETE: {description}")
    time.sleep(2)

def main():
    print("🚀 SPOTIFY VoC TURBO PIPELINE")
    print("Estimated total time: 4-6 hours (mostly API waiting)")
    print("You need: Reddit API key + Gemini API key (Google Pro helps)")
    print("="*60)

    steps = [
        ("1_reddit_scraper.py", "Reddit Data Collection (30-60 min)"),
        ("2_appstore_scraper.py", "App Store Reviews (15-20 min)"),
        ("3_playstore_scraper.py", "Play Store Reviews (15-20 min)"),
        ("4_data_cleaner.py", "Data Cleaning & Deduplication (10 min)"),
        ("5_gemini_analyzer.py", "AI Bulk Analysis (2-3 hours)"),
        ("6_insight_synthesizer.py", "Strategic Synthesis (20 min)"),
    ]

    for script, desc in steps:
        run_step(script, desc)

    print("\n" + "="*60)
    print("🎉 ALL STEPS COMPLETE!")
    print("="*60)
    print("\n📁 Your outputs are in data/final/:")
    print("   - executive_report.txt → Your narrative foundation")
    print("   - synthesis.json → Structured insights for slides")
    print("   - competitive.json → Competitive intelligence")
    print("   - pain_summary.csv → Evidence table")
    print("   - needs_summary.csv → Opportunity table")
    print("   - segment_summary.csv → Persona data")
    print("   - top_evidence.csv → Quotes for presentation")
    print("\n⏭️  NEXT: Run validation + manual refinement (2 hours)")
    print("   Then write your fellowship submission (4 hours)")

if __name__ == "__main__":
    main()
