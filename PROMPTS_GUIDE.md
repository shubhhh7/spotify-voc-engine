# 📖 PROMPTS GUIDE: Step-by-Step Execution Manual

> **No coding experience assumed. Every step explained.**
> Follow this exactly. Do not skip steps.

---

## BEFORE YOU START

### What You Need

| Item | Why | How to Get |
|------|-----|------------|
| **Computer** (Windows/Mac/Linux) | To run scripts | Your laptop |
| **Python 3.8+** | Programming language | https://python.org/downloads |
| **Internet** | To scrape data and call AI | Your WiFi |
| **Gemini API Key** | To analyze data with AI | https://aistudio.google.com/app/apikey |
| **Google Pro subscription** | Higher API limits | You already have this |
| **2 days** | Time to execute | Block your calendar |

**You do NOT need:**
- ❌ Reddit API key (we use public JSON API)
- ❌ Credit card (everything is free)
- ❌ Coding knowledge (copy-paste only)
- ❌ Cloud servers (runs on your laptop)

---

## PHASE 0: SETUP (30 minutes)

### Step 1: Install Python

**Windows:**
1. Go to https://python.org/downloads
2. Click "Download Python 3.12"
3. Run the installer
4. **IMPORTANT:** Check "Add Python to PATH" during installation
5. Click "Install Now"

**Mac:**
1. Open Terminal (Cmd+Space, type "Terminal")
2. Run: `brew install python` (if you have Homebrew)
3. Or download from https://python.org/downloads

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Verify installation:**
```bash
python --version
# Should show: Python 3.12.x or higher
```

---

### Step 2: Download the Toolkit

1. Download the zip file from the provided link
2. Unzip it to your Desktop (or any folder)
3. You should see a folder named `spotify_voc_engine_2day`

**Verify:** Open the folder. You should see files like:
- `1_reddit_scraper.py`
- `2_appstore_scraper.py`
- `README.md`
- etc.

---

### Step 3: Install Dependencies

**Open Terminal/Command Prompt:**

**Windows:**
- Press `Win + R`, type `cmd`, press Enter

**Mac:**
- Press `Cmd + Space`, type `Terminal`, press Enter

**Navigate to the toolkit folder:**
```bash
# Windows:
cd Desktop\spotify_voc_engine_2day

# Mac/Linux:
cd ~/Desktop/spotify_voc_engine_2day
```

**Install required packages:**
```bash
pip install -r requirements.txt
```

This will take 2-3 minutes. You will see many lines of text scrolling. Wait until it finishes.

**If you get errors:**
- Try: `pip3 install -r requirements.txt` (instead of `pip`)
- Try: `python -m pip install -r requirements.txt`
- If still failing, run each package individually:
  ```bash
  pip install pandas numpy requests
  pip install google-generativeai
  pip install langdetect scikit-learn tqdm
  pip install app-store-scraper google-play-scraper
  ```

---

### Step 4: Get Your Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account (same as your Pro subscription)
3. Click "Create API Key"
4. Copy the key (it looks like: `AIzaSy...`)
5. **Keep this secret. Do not share it.**

---

### Step 5: Configure API Key

In the toolkit folder, find the file `.env.template`

**Create a copy named `.env`:**

**Windows:**
```cmd
copy .env.template .env
```

**Mac/Linux:**
```bash
cp .env.template .env
```

**Edit the `.env` file:**

**Windows:**
- Right-click `.env` → Open with Notepad
- Find the line: `GEMINI_API_KEY=your_gemini_api_key_here`
- Replace with your actual key: `GEMINI_API_KEY=AIzaSyYourActualKeyHere`
- Save and close

**Mac:**
```bash
open -e .env
```
- Edit the file, save and close

**Linux:**
```bash
nano .env
```
- Edit, press Ctrl+O to save, Ctrl+X to exit

**Verify:**
```bash
python -c "import config_turbo; print('Config loaded successfully')"
```
If you see "Config loaded successfully", you're ready.

---

## PHASE 1: DATA COLLECTION (1.5 hours)

### Step 6: Open Multiple Terminal Windows

**This is the #1 time-saver.**

**Windows:**
- Open Command Prompt 3 times (3 separate windows)

**Mac:**
- Open Terminal, then press `Cmd + N` twice (3 total windows)

**Linux:**
- Open 3 terminal windows

---

### Step 7: Run Scrapers in Parallel

**In Terminal 1 (Reddit):**
```bash
cd Desktop\spotify_voc_engine_2day  # Windows
cd ~/Desktop/spotify_voc_engine_2day  # Mac/Linux
python 1_reddit_scraper.py
```

**In Terminal 2 (App Store):**
```bash
cd Desktop\spotify_voc_engine_2day  # Windows
cd ~/Desktop/spotify_voc_engine_2day  # Mac/Linux
python 2_appstore_scraper.py
```

**In Terminal 3 (Play Store):**
```bash
cd Desktop\spotify_voc_engine_2day  # Windows
cd ~/Desktop/spotify_voc_engine_2day  # Mac/Linux
python 3_playstore_scraper.py
```

**What happens:**
- Reddit scraper: Fetches posts from 8 subreddits using 15 search queries. Takes 30-60 minutes.
- App Store scraper: Fetches 600 iOS reviews. Takes 15-20 minutes.
- Play Store scraper: Fetches 600 Android reviews. Takes 15-20 minutes.

**While waiting:** Read the `PRESENTATION_GUIDE.md` file to plan your slides.

---

### Step 8: Troubleshoot Reddit Scraper

**If Reddit scraper shows 0 results or errors:**

**Option A: Check your internet**
```bash
ping reddit.com
```
If it fails, check your WiFi.

**Option B: Reddit is blocking your IP**
- Try using a VPN
- Or switch to mobile hotspot
- Or wait 10 minutes and re-run

**Option C: Use PullPush fallback (automatic)**
The script already tries PullPush API automatically if Reddit blocks. You should see:
```
🔄 Trying PullPush fallback...
```

**Option D: Manual collection (guaranteed)**
If ALL automated methods fail, follow `MANUAL_REDDIT_GUIDE.md` to copy-paste posts from Reddit in your browser. Takes 45-60 minutes but works 100%.

---

### Step 9: Verify Data Collection

After all 3 scrapers finish, check:
```bash
# Windows:
dir data\raw

# Mac/Linux:
ls data/raw
```

You should see 3 files:
- `reddit_posts.csv`
- `appstore_reviews.csv`
- `playstore_reviews.csv`

**Check sizes:**
```bash
# Windows:
wc -l data\raw\*.csv

# Mac/Linux:
wc -l data/raw/*.csv
```

**Minimum viable:**
- Reddit: 500+ rows
- App Store: 300+ rows
- Play Store: 300+ rows

If any file is missing or has <100 rows, re-run that scraper.

---

## PHASE 2: DATA CLEANING (15 minutes)

### Step 10: Run Data Cleaner

```bash
python 4_data_cleaner.py
```

**What happens:**
- Merges all 3 sources into one file
- Removes spam, duplicates, non-English text
- Adds emotional signals (exclamation marks, caps, etc.)
- Output: `data/clean/merged_reviews.csv`

**Verify:**
```bash
wc -l data/clean/merged_reviews.csv
```
Should show 2,000+ rows.

---

## PHASE 3: AI ANALYSIS (3 hours)

### Step 11: Run AI Analyzer

```bash
python 5_gemini_analyzer.py
```

**What happens:**
- Phase 1 (Flash): Analyzes 2,000+ reviews in batches of 60
- Phase 2 (Pro): Deep analysis on top 40 most severe posts
- This takes 2-3 hours (mostly waiting for API responses)

**You will see:**
```
📦 PHASE 1: Bulk Extraction with Flash
   Batches to process: 45
   Estimated time: 1.5 hours
```

**Do NOT close the terminal.** Let it run.

**While waiting:**
- Draft your problem statement (see Phase 5)
- Sketch your slide outline (see PRESENTATION_GUIDE.md)
- Read 20 random rows from `data/clean/merged_reviews.csv` to build intuition

---

### Step 12: Handle API Errors

**If you see "Rate limit hit":**
- The script automatically waits and retries
- This is normal. Let it continue.

**If you see "API error" repeatedly:**
1. Check your API key in `.env`
2. Verify your Google Pro subscription is active
3. Try generating a new API key at https://aistudio.google.com/app/apikey

**If API completely fails:**
```bash
python gemini_web_backup.py
```
This creates 4 text files in `data/final/web_prompts/`. 

**Then:**
1. Open https://gemini.google.com in your browser
2. Copy-paste each file into a new chat
3. Save Gemini's responses
4. Use these responses instead of API outputs

---

### Step 13: Verify AI Analysis

After the analyzer finishes:
```bash
ls data/analyzed
```

You should see:
- `analyzed_reviews.csv` (main output)
- `extractions.csv` (bulk analysis)
- `deep_jtbd.csv` (deep analysis)

---

## PHASE 4: SYNTHESIS (30 minutes)

### Step 14: Run Insight Synthesizer

```bash
python 6_insight_synthesizer.py
```

**What happens:**
- Cross-source theme synthesis
- Competitive analysis
- Executive report generation

**Output:** `data/final/` directory with:
- `executive_report.txt` (your narrative foundation)
- `synthesis.json` (structured insights)
- `competitive.json` (competitive intelligence)
- `pain_summary.csv` (top pain points)
- `needs_summary.csv` (unmet needs)
- `segment_summary.csv` (user segments)
- `top_evidence.csv` (powerful quotes)

---

### Step 15: Run Quick Validation

```bash
python quick_validate.py
```

**What happens:**
- Checks if AI quotes match source text
- Validates category distributions
- Flags anomalies

**Read the output carefully.** If accuracy < 80%, consider re-running analysis.

---

## PHASE 5: WRITING & PRESENTATION (Day 2)

### Step 16: Read the Executive Report

```bash
# Windows:
type data\final\executive_report.txt

# Mac/Linux:
cat data/final/executive_report.txt
```

This is your starting point. **Rewrite it in your own voice.** The AI gives you raw material. You add the PM judgment.

---

### Step 17: Answer the 6 Research Questions

Open a new document. Answer each question with:
1. **1-sentence bottom line**
2. **2-3 specific user quotes** (from `top_evidence.csv`)
3. **1 "so what" implication** (what Spotify should do)

| Question | Where to Find Evidence |
|----------|----------------------|
| Why do users struggle to discover new music? | `synthesis.json` → discovery_problems |
| What are the most common frustrations with recommendations? | `synthesis.json` → recommendation_frustrations |
| What listening behaviors are users trying to achieve? | `synthesis.json` → behavioral_patterns |
| What causes users to repeatedly listen to the same content? | `synthesis.json` → repetition_causes |
| Which user segments experience different discovery challenges? | `segment_summary.csv` + `synthesis.json` → segment_profiles |
| What unmet needs emerge consistently across reviews? | `needs_summary.csv` + `synthesis.json` → unmet_needs |

---

### Step 18: Name Your Segments

Don't use generic labels. Use memorable names:

| Generic AI Label | Your Memorable Name | Why |
|------------------|-------------------|-----|
| Power User | The Playlist Prisoner | Stuck in algorithmic loops |
| Casual Listener | The Background Settler | Wants zero-friction, not discovery |
| Social Listener | The Musical Explorer | Actively seeks novelty |
| Curator | The DJ Wannabe | Wants to build, not consume |

**For each segment, write:**
- Name
- 1-sentence description
- Key pain point
- Exact quote from data
- JTBD statement

---

### Step 19: Score Opportunities

From `synthesis.json` → opportunity_scoring, create a table:

| Opportunity | Impact | Confidence | Ease | ICE | Rationale |
|-------------|--------|------------|------|-----|-----------|
| | 1-10 | 1-10 | 1-10 | calc | 1 sentence |

**Override AI scores with your PM judgment.** The AI scores by frequency. You score by strategic value.

**Example override:**
- AI says: "Shuffle complaints" = Impact 8 (high frequency)
- You say: "Shuffle complaints" = Impact 4 (easy to fix, not strategic)
- AI says: "Local music discovery" = Impact 3 (low frequency)
- You say: "Local music discovery" = Impact 8 (untapped market, differentiation)

---

### Step 20: Build the 10-Slide Deck

Follow `PRESENTATION_GUIDE.md` exactly.

**Slide-by-slide content sources:**

| Slide | Content Source |
|-------|---------------|
| 1: Title | Your name + project name |
| 2: Problem | `executive_report.txt` → bottom line + `top_evidence.csv` → best quote |
| 3: Methodology | `README.md` → data sources + your validation notes |
| 4: Key Insight | `synthesis.json` → most contrarian strategic_insight |
| 5: Segments | Your named segments from Step 18 |
| 6: Data | `pain_summary.csv` + `needs_summary.csv` → charts |
| 7: JTBD Map | `deep_jtbd.csv` + your synthesis |
| 8: Opportunities | Your ICE table from Step 19 |
| 9: Competitive | `competitive.json` |
| 10: Recommendation | Your 3 time-bound actions |

**Tools:**
- Google Slides (free, easiest)
- Figma (free tier, better design)
- Canva (free tier, templates)

**Design rules:**
- Use Spotify green (#1DB954) as accent
- One insight per slide
- Every claim has a quote or number
- Max 6 bullets per slide

---

### Step 21: Final Review Checklist

Before submitting, verify:

- [ ] Every slide has a "so what" — not just observations
- [ ] Every claim is anchored to evidence (quote or number)
- [ ] Segments have memorable names, not generic labels
- [ ] ICE scores are defensible (you can explain each)
- [ ] Limitations are acknowledged (shows intellectual honesty)
- [ ] No typos, no placeholder text
- [ ] Slides flow logically
- [ ] PDF backup saved
- [ ] 3 expected Q&A answers prepared
- [ ] Read aloud once to catch awkward phrasing

---

## TROUBLESHOOTING FAQ

### "pip install fails"
**Try:**
```bash
pip3 install -r requirements.txt
# or
python -m pip install -r requirements.txt
# or install one by one:
pip install pandas
pip install numpy
pip install requests
pip install google-generativeai
```

### "Reddit scraper returns 0 results"
**Try:**
1. Check internet: `ping reddit.com`
2. Use VPN or mobile hotspot
3. Follow `MANUAL_REDDIT_GUIDE.md` for manual copy-paste

### "App Store scraper returns empty"
**Try:**
1. Reduce count in `config_turbo.py`: `APP_STORE_COUNT = 100`
2. Re-run: `python 2_appstore_scraper.py`

### "Gemini API says 'quota exceeded'"
**Try:**
1. Wait 24 hours (free tier resets daily)
2. Use Gemini Advanced web interface: `python gemini_web_backup.py`
3. Paste prompts into gemini.google.com

### "Analysis takes too long"
**This is normal.** The AI needs time to process thousands of reviews.
- 2,000 reviews ÷ 60 per batch = ~35 API calls
- Each call takes 10-30 seconds
- Total: 30-60 minutes of API time
- Plus rate limiting: 2-3 hours total

**Do not cancel.** Let it run overnight if needed.

### "I only have 1 day left"
**Nuclear option:**
1. Skip Play Store (use Reddit + App Store only)
2. Skip deep JTBD analysis
3. Skip competitive analysis
4. Focus on: 1 strong insight + 2 segments + 3 opportunities + 1 recommendation
5. A focused 10-slide deck with depth beats a scattered 20-slide deck

---

## EXPECTED Q&A PREPARATION

Prepare answers to these questions in advance:

**Q1: "How do you know the AI didn't make this up?"**
> "Three layers. First, every extraction has a confidence score — I discarded anything below 3/5. Second, I verified 20 random quotes with Ctrl+F against source data. Third, I red-teamed the top insight by actively searching for counter-evidence."

**Q2: "Why these data sources?"**
> "Reddit captures unfiltered, long-form discussions from power users — the canaries in the coal mine. App/Play Store reviews capture the extreme experience from casual users. Triangulating across sources gives me confidence the insight is real, not just a loud minority."

**Q3: "What's the most contrarian insight?"**
> [Prepare this in advance. It should go against common wisdom.]
> Example: "Everyone assumes users want 'better recommendations.' But the data shows the real problem is 'recommendation fatigue' — users are overwhelmed by too many algorithmic options and actually want LESS choice, not more."

**Q4: "What are you missing?"**
> "Three things. One, non-English markets — this is English-only. Two, behavioral data — I have what users say, not what they do. Three, longitudinal trends — this is a snapshot. Phase 2 would add these."

**Q5: "If you had $100K, what would you do differently?"**
> "Three investments. First, $30K on Claude 3.5 for qualitative depth. Second, $40K on a panel survey to validate segments quantitatively. Third, $30K on longitudinal scraping to track complaint evolution."

---

## FINAL CHECKLIST

Before you start Day 1:
- [ ] Python installed
- [ ] Toolkit downloaded and unzipped
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Gemini API key obtained
- [ ] `.env` file created with API key
- [ ] Config verified (`python -c "import config_turbo"`)
- [ ] Calendar blocked for 2 days
- [ ] PRESENTATION_GUIDE.md read
- [ ] MANUAL_REDDIT_GUIDE.md bookmarked (in case automated scraper fails)

Before you submit:
- [ ] 6 research questions answered with evidence
- [ ] 3 user segments named and described
- [ ] JTBD map complete
- [ ] Top 5 opportunities scored with ICE
- [ ] 10-slide deck complete
- [ ] PDF backup saved
- [ ] 3 expected Q&A answers written
- [ ] Read submission aloud once
- [ ] Submitted 30 minutes before deadline

---

**You now have everything you need. Execute ruthlessly. Good luck.** 🚀
