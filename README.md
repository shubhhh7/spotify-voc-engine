# ⚡ Spotify VoC Engine: 2-Day Turbo Edition

> **Zero budget. No Reddit API needed. Google Pro subscription. 48 hours. Fellowship-worthy submission.**

---

## 🚀 What's New in This Version

| Feature | Previous | This Version |
|---------|----------|--------------|
| **Reddit access** | Required Reddit API app | **No API needed** — uses public JSON API |
| **Fallback** | Manual only | **Automatic** — PullPush API + manual guide |
| **Setup time** | 30 min (API registration) | **15 min** (just Gemini key) |
| **Step-by-step guide** | Technical README | **PROMPTS_GUIDE.md** — no coding assumed |

---

## 📦 Quick Start (15 minutes)

```bash
# 1. Create project directory
mkdir spotify_voc && cd spotify_voc

# 2. Unzip this toolkit
# (unzip the downloaded file here)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.template .env
# Edit .env with your Gemini API key ONLY
```

**Get your free API key:**
- Gemini: https://aistudio.google.com/app/apikey

**You do NOT need a Reddit API key.** The scraper uses Reddit's public JSON API.

---

## ⚡ The 2-Day Battle Plan

**Read the full hour-by-hour schedule:** [2DAY_BATTLE_PLAN.md](2DAY_BATTLE_PLAN.md)

**Read the step-by-step execution guide:** [PROMPTS_GUIDE.md](PROMPTS_GUIDE.md)

### Day 1: Data → AI → Validation (10 hours)

```bash
# Open 3 terminals and run simultaneously:
# Terminal 1:
python 1_reddit_scraper.py

# Terminal 2:
python 2_appstore_scraper.py

# Terminal 3:
python 3_playstore_scraper.py

# After all finish (1-2 hours):
python 4_data_cleaner.py

# Then start AI analysis (2-3 hours, mostly waiting):
python 5_gemini_analyzer.py

# Then synthesis (30 min):
python 6_insight_synthesizer.py

# Then validation (30 min):
python quick_validate.py
```

**Or run everything with one command:**
```bash
python turbo_pipeline.py
```

### Day 2: Writing → Presentation (10 hours)

**Read the presentation guide:** [PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md)

---

## 🛡️ Google Pro Subscription Advantage

Your Google Pro subscription unlocks:

1. **Gemini Advanced web interface** (gemini.google.com)
   - No rate limits in chat mode
   - Can paste 100K+ tokens at once
   - Use as backup if API fails: `python gemini_web_backup.py`

2. **Higher API quotas** (if using AI Studio API)
   - Flash: ~3,000 requests/day (vs 1,500 free)
   - Pro: ~1,000 requests/day (vs 50 free)

3. **1M token context window**
   - Can analyze larger batches
   - Better synthesis quality

---

## 📁 File Structure

```
spotify_voc_engine_2day/
├── 1_reddit_scraper.py          # Reddit collection (NO API KEY)
├── 2_appstore_scraper.py        # App Store reviews
├── 3_playstore_scraper.py       # Play Store reviews
├── 4_data_cleaner.py            # Cleaning + dedup
├── 5_gemini_analyzer.py         # AI analysis
├── 6_insight_synthesizer.py     # Synthesis
├── turbo_pipeline.py            # One-command pipeline
├── quick_validate.py            # 30-min validation
├── gemini_web_backup.py        # Manual backup prompts
├── prompts.py                   # All AI prompts
├── config_turbo.py              # Settings
├── requirements.txt             # Dependencies
├── .env.template                # API key template (Gemini only)
├── 2DAY_BATTLE_PLAN.md          # Hour-by-hour schedule
├── PRESENTATION_GUIDE.md        # 10-slide template
├── PROMPTS_GUIDE.md             # Step-by-step execution manual
├── MANUAL_REDDIT_GUIDE.md       # Manual fallback for Reddit
└── data/
    ├── raw/                     # Scraped data
    ├── clean/                   # Cleaned dataset
    ├── analyzed/                # AI-analyzed dataset
    └── final/                   # Reports + summaries
```

---

## 🎯 Expected Outputs

After running the pipeline, `data/final/` contains:

| File | Purpose | Use For |
|------|---------|---------|
| `executive_report.txt` | Narrative foundation | Fellowship write-up |
| `synthesis.json` | Structured insights | Slides, evidence tables |
| `competitive.json` | Competitive intelligence | Slide 9 |
| `pain_summary.csv` | Top pain points | Slide 6, evidence |
| `needs_summary.csv` | Unmet needs | Slide 6, JTBD map |
| `segment_summary.csv` | User segments | Slide 5 |
| `top_evidence.csv` | Powerful quotes | Every slide |
| `validation_log.txt` | Quality audit | Methodology section |
| `web_prompts/` | Backup prompts | If API fails |

---

## 🚨 Emergency Protocols

**If Reddit scraper fails:**
1. The script automatically tries PullPush API (no auth needed)
2. If still failing, follow `MANUAL_REDDIT_GUIDE.md` for browser copy-paste
3. Or use `MANUAL_REDDIT_GUIDE.md` → Method 2: JSON API in browser

**If App/Play Store scraper fails:**
- Reduce count in `config_turbo.py` and re-run
- Or manually copy-paste 200 reviews from store pages

**If Gemini API rate-limits:**
- The script auto-throttles (waits and retries)
- Or use web backup: `python gemini_web_backup.py` then paste into gemini.google.com

**If you only have 24 hours left:**
- Skip Play Store (use Reddit + App Store only)
- Skip deep JTBD analysis
- Focus on: 1 strong insight + 2 segments + 3 opportunities

---

## ⚠️ Critical Warnings

1. **Do not skip validation.** Run `quick_validate.py`. Read the output.
2. **Do not trust AI scores blindly.** Override ICE scores with your PM judgment.
3. **Name your segments.** "Power User" is generic. "The Playlist Prisoner" is memorable.
4. **Every claim needs evidence.** A slide without a quote or number is a hypothesis.
5. **Acknowledge limitations.** English-only, snapshot, selection bias — say this upfront.

---

## 💪 Mindset

**This is a sprint, not a marathon.**

- The AI does grunt work. **You do the thinking.**
- **Perfection is the enemy.** A 9/10 submission that exists beats a 10/10 idea that doesn't.
- **Sleep is non-negotiable.** 6 hours minimum each night.
- **If stuck for >30 minutes, move on.** Momentum matters more than any single slide.

---

## 📞 Next Steps

1. **Right now:** Read `PROMPTS_GUIDE.md` (the step-by-step manual)
2. **Get API key:** https://aistudio.google.com/app/apikey (15 min)
3. **Install dependencies:** `pip install -r requirements.txt` (5 min)
4. **Run scrapers:** Open 3 terminals, run in parallel (1-2 hours)
5. **Let AI analyze:** Run `python 5_gemini_analyzer.py` (2-3 hours)

**Execute ruthlessly. Good luck.** 🚀
