# ⚡ 2-DAY BATTLE PLAN: Spotify VoC Engine

> **Constraint:** 48 hours total. Google Pro subscription active. 
> **Goal:** Fellowship-worthy submission with zero dollars spent.

---

## 🎯 THE STRATEGY: Parallelize Everything

**Standard plan:** Sequential 6 days  
**Turbo plan:** Parallel 2 days

| Day | Morning (4h) | Afternoon (4h) | Evening (2h) |
|-----|-------------|----------------|-------------|
| **Day 1** | Data collection (all 3 sources in parallel) | AI analysis (bulk + deep) | Validation + spot fixes |
| **Day 2** | Synthesis + insight refinement | Writing + slide creation | Final review + practice |

**Key acceleration tactics:**
1. **Parallel scraping:** Run Reddit, App Store, Play Store simultaneously in 3 terminal windows
2. **Google Pro advantage:** Larger batch sizes (60 vs 40), faster rate limits (30 RPM vs 15)
3. **Web backup:** If API fails, use Gemini Advanced web interface (unlimited, included in Pro)
4. **Pre-built prompts:** No prompt engineering during execution — everything is ready
5. **Validation lite:** Audit 30 items instead of 50. Trust the pipeline, spot-check outliers.

---

## 📅 DAY 1: DATA → AI → VALIDATION (10 hours)

### **Hour 0: Setup (15 minutes)**

```bash
# 1. Unzip toolkit
mkdir spotify_voc && cd spotify_voc
# (unzip the downloaded toolkit here)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.template .env
# Edit .env with Reddit + Gemini keys
```

**Required accounts (all free):**
- Reddit API: https://www.reddit.com/prefs/apps (type: script)
- Gemini API: https://aistudio.google.com/app/apikey

**Test your setup:**
```bash
python -c "import config_turbo; print('Config loaded')"
```

---

### **Hour 0.25–1.5: Parallel Data Collection (1.25 hours)**

**Open 3 terminal windows and run simultaneously:**

```bash
# Terminal 1: Reddit (longest, ~45 min)
python 1_reddit_scraper.py

# Terminal 2: App Store (~15 min)
python 2_appstore_scraper.py

# Terminal 3: Play Store (~15 min)
python 3_playstore_scraper.py
```

**Why parallel:** These are independent I/O operations. No conflicts. Reddit takes longest due to rate limiting.

**While waiting:** Read the `prompts.py` file to understand what the AI will extract. This saves time later.

**Quality gate (5 min):** After all finish, check:
```bash
wc -l data/raw/*.csv
```
- Reddit: Should be 1,500+ rows
- App Store: Should be 500+ rows
- Play Store: Should be 500+ rows

If any source is <100 rows, re-run that scraper with lower `MIN_COMMENTS` in config.

---

### **Hour 1.5–2: Data Cleaning (30 minutes)**

```bash
python 4_data_cleaner.py
```

**What happens:** Merges, cleans, deduplicates, enriches. Takes ~10 minutes.

**Quality gate (5 min):**
```bash
wc -l data/clean/merged_reviews.csv
```
- Should be 2,000–4,000 rows after deduplication
- If <1,500, check if language filter is too aggressive

**Quick validation:**
```bash
head -20 data/clean/merged_reviews.csv
```
- Are texts readable? Any encoding issues?
- Are sources balanced? (Should see reddit, app_store, play_store)

---

### **Hour 2–5: AI Bulk Analysis (3 hours)**

```bash
python 5_gemini_analyzer.py
```

**What happens:** 
- Phase 1 (Flash): 2,000–4,000 reviews in batches of 60
- Phase 2 (Pro): Deep JTBD on top 50 severe items

**With Google Pro:**
- Flash limit: ~3,000/day (you're safe)
- Pro limit: ~1,000/day (you're safe)
- Processing time: ~2.5 hours (mostly waiting for API)

**While waiting (do NOT sit idle):**
1. **Start drafting your problem statement** (see template below)
2. **Sketch your slide outline** (10 slides, see template below)
3. **Read 20 random Reddit posts** from `data/clean/merged_reviews.csv` to build intuition

**If API fails / rate limited:**
```bash
# Switch to web backup mode
python gemini_web_backup.py
# Then use Gemini Advanced (gemini.google.com) to paste prompts manually
```

---

### **Hour 5–5.5: AI Synthesis (30 minutes)**

```bash
python 6_insight_synthesizer.py
```

**What happens:** 
- Cross-source theme synthesis (Pro)
- Competitive analysis (Pro)
- Executive report generation (Pro)

**Output:** `data/final/` directory with all reports.

---

### **Hour 5.5–7: Validation & Red Teaming (1.5 hours)**

**This is where your PM judgment earns points. The AI did the grunt work. You do the thinking.**

**Validation checklist (30 min):**
- [ ] Open `data/final/top_evidence.csv`. Read all 20 quotes. Do they feel real? (Ctrl+F in source CSV to verify 5 random ones)
- [ ] Open `data/final/pain_summary.csv`. Are the top 5 categories intuitively correct?
- [ ] Open `data/final/segment_summary.csv`. Do the segments make sense? Can you name them better?

**Red teaming (30 min):**
- Pick the AI's #1 insight. Now try to kill it:
  - Can you find 3 counter-examples in the raw data?
  - Would this insight apply to Apple Music users too? (If yes, it's not Spotify-specific)
  - Is this a real problem or just loud users complaining? (Check frequency vs severity)

**Insight refinement (30 min):**
- Rewrite segment names (e.g., "Power User" → "The Playlist Prisoner")
- Adjust ICE scores based on strategic fit, not just frequency
- Write 3 "so what" statements that connect insights to product actions

---

### **Hour 7–8: Backup / Recovery (1 hour)**

**If everything worked:** Skip this. Use the hour for sleep.

**If API failed or outputs are weak:**
```bash
python gemini_web_backup.py
```
This generates 4 formatted prompts in `data/final/web_prompts/`. 

**Use Gemini Advanced web interface (free with your Pro subscription):**
1. Open gemini.google.com
2. Paste `01_theme_extraction.txt` → Save output
3. Paste `02_jtbd_analysis.txt` → Save output
4. Paste `03_opportunity_scoring.txt` → Save output
5. Paste `04_executive_report.txt` → Save output

**Why this works:** Gemini Advanced has no rate limits in chat mode. You can paste 100,000 tokens at once. The only downside: manual copy-paste.

---

### **Hour 8–10: Evening Buffer / Early Writing (2 hours)**

**Option A (if pipeline succeeded):** Start writing your problem statement and user segments.

**Option B (if using web backup):** Finish all 4 web prompts and organize outputs.

**Sleep early.** Day 2 is mentally intensive.

---

## 📅 DAY 2: SYNTHESIS → WRITING → PRESENTATION (10 hours)

### **Hour 10–12: Deep Insight Work (2 hours)**

**This is the most important part of your fellowship submission.**

**Task 1: Write the 6 research question answers (1 hour)**

Use this template. Every answer must have:
- A 1-sentence bottom line
- 2-3 specific user quotes as evidence
- A "so what" implication

```
Q1: Why do users struggle to discover new music?
Bottom line: [Your insight here]
Evidence: 
  - "[Exact quote from data]" (Source: Reddit, Score: 245)
  - "[Exact quote]" (Source: App Store, Rating: 1★)
So what: Spotify should [specific action]

Q2: What are the most common frustrations with recommendations?
[Same format]

Q3: What listening behaviors are users trying to achieve?
[Same format]

Q4: What causes users to repeatedly listen to the same content?
[Same format]

Q5: Which user segments experience different discovery challenges?
[Same format - include your named segments]

Q6: What unmet needs emerge consistently across reviews?
[Same format]
```

**Task 2: Build the JTBD map (30 min)**

From `data/final/needs_summary.csv` and `deep_jtbd.csv`, create:

| Segment | When I... | I want to... | So I can... | But Spotify... |
|---------|-----------|--------------|-------------|----------------|
| [Name] | [Situation] | [Motivation] | [Outcome] | [Barrier] |

**Task 3: Score opportunities (30 min)**

From `data/final/synthesis.json` → opportunity_scoring, create:

| Opportunity | Impact | Confidence | Ease | ICE | Rationale |
|-------------|--------|------------|------|-----|-----------|
| | 1-10 | 1-10 | 1-10 | calc | 1 sentence |

**Override AI scores with your PM judgment.** The AI scores by frequency. You score by strategic value.

---

### **Hour 12–14: Fellowship Narrative Writing (2 hours)**

**Write these sections:**

**Section 1: Problem Statement (20 min)**
```
[1 paragraph, 4-5 sentences]

Spotify users across [X] feedback sources consistently report 
struggling with [specific discovery problem]. Despite [Spotify's 
current capability], [Y]% of analyzed feedback indicates [specific 
frustration]. This is particularly acute for [segment], who [behavior].
The business impact is [retention/churn/engagement risk], as evidenced 
by [specific quote or metric].
```

**Section 2: Evidence & Methodology (20 min)**
```
Data Sources: [List with volumes and bias acknowledgments]
Analysis Method: [AI-assisted thematic extraction + human validation]
Limitations: [English-only, snapshot, selection bias, etc.]
Validation: [Red team process, quote verification, cross-source triangulation]
```

**Section 3: User Segments (30 min)**
```
Segment 1: "The [Name]" (X% of pain points)
- Behavior: [What they do]
- Pain: [What hurts]
- Quote: "[Exact quote]"
- JTBD: [When I..., I want to..., so I can...]

Segment 2: "The [Name]" (Y% of pain points)
[Same format]

Segment 3: "The [Name]" (Z% of pain points)
[Same format]
```

**Section 4: Opportunities (30 min)**
```
Top 5 opportunities with ICE scores and 1-paragraph rationale each.
Include: user evidence, competitive context, risk of inaction.
```

---

### **Hour 14–17: Slide Deck Creation (3 hours)**

**10-Slide Structure (use Google Slides or Figma — both free):**

| Slide | Title | Content | Time |
|-------|-------|---------|------|
| 1 | **Title** | Project name, your name, date | 5 min |
| 2 | **The Problem** | 1 sentence + 1 powerful quote | 15 min |
| 3 | **Methodology** | Data sources, volume, AI + human validation | 20 min |
| 4 | **Key Insight** | The single most surprising finding | 20 min |
| 5 | **User Segments** | 3 personas with names, quotes, behaviors | 30 min |
| 6 | **The Data** | 3-4 charts (pain distribution, sentiment, source comparison) | 30 min |
| 7 | **JTBD Map** | Table or diagram showing jobs + barriers | 20 min |
| 8 | **Opportunities** | Top 5 with ICE scores, visual matrix | 30 min |
| 9 | **Competitive Context** | What competitors are doing + Spotify's vulnerability | 20 min |
| 10 | **Recommendation** | 3 specific, time-bound next steps | 15 min |

**Chart ideas (use Google Sheets → export as PNG):**
- Pain category distribution (bar chart)
- Sentiment by source (stacked bar)
- Rating distribution over time (line chart)
- Segment size pie chart
- ICE score scatter plot (Impact vs Ease)

**Visual design tips:**
- Use Spotify green (#1DB954) as accent color
- One insight per slide. No walls of text.
- Every claim has a quote or number next to it.
- Use the actual quotes from `top_evidence.csv` — real user voice is powerful.

---

### **Hour 17–18: Final Review & Practice (1 hour)**

**Review checklist:**
- [ ] Every slide has a "so what" — not just observations
- [ ] Every claim is anchored to evidence (quote or number)
- [ ] Segments have memorable names, not generic labels
- [ ] ICE scores are defensible (you can explain why each score)
- [ ] Limitations are acknowledged (shows intellectual honesty)
- [ ] No typos, no placeholder text, no "Lorem ipsum"
- [ ] Slides flow logically (problem → insight → segments → data → opportunities → action)

**Practice presenting:**
- Time yourself: 10 slides × 2 minutes = 20-minute presentation
- Record yourself on your phone
- Watch it once. Fix anything that sounds awkward.

**Backup plan:**
- Save PDF version of slides (in case tech fails)
- Prepare 3 "expected questions" answers (see below)

---

### **Hour 18–20: Buffer (2 hours)**

**Use this for:**
- Sleep (if you stayed up late Day 1)
- Final polish based on fresh eyes
- Reading your submission aloud to catch awkward phrasing
- Preparing for Q&A

---

## 🎯 EXPECTED INTERVIEW QUESTIONS & ANSWERS

Prepare these in advance. Write them down.

### Q1: "How do you know the AI didn't make this up?"
**Your answer:**
"Three validation layers. First, every AI extraction includes a confidence score — I discarded anything below 3/5. Second, I manually verified 30 random quotes using Ctrl+F against source data. Third, I red-teamed the top 3 insights by actively searching for counter-evidence. The insight about [X] survived because I found consistent evidence across Reddit, App Store, and Play Store — not just one source."

### Q2: "Why should I trust Reddit users over our actual user data?"
**Your answer:**
"I don't — this is a directional signal, not a census. Reddit overrepresents power users and early adopters, which is actually valuable for discovery problems because they're the canaries in the coal mine. App Store reviews capture the 'extreme' experience (lovers and haters). The triangulation across sources gives me confidence that [specific insight] is real, but I'd validate with behavioral data before building."

### Q3: "What's the most contrarian insight you found?"
**Your answer:**
[Prepare this in advance. It should be something that goes against common wisdom.]
Example: "Everyone assumes users want 'better recommendations.' But the data shows the real problem is 'recommendation fatigue' — users are overwhelmed by too many algorithmic options and actually want LESS choice, not more. They want curation, not optimization."

### Q4: "What did you miss?"
**Your answer:**
"Three things. One, non-English markets — this is English-only, so I missed India, Brazil, Indonesia. Two, behavioral data — I have what users say, not what they do. Three, longitudinal trends — this is a snapshot, so I can't tell if [problem] is getting worse. Phase 2 would add these."

### Q5: "If you had $100K, what would you do differently?"
**Your answer:**
"Three investments. First, $30K on Claude 3.5 Sonnet for qualitative analysis — it's better at sarcasm and nuance than Gemini. Second, $40K on a panel survey to validate segments with quantitative data. Third, $30K on longitudinal scraping to track how complaints evolve after product releases."

---

## 🚨 EMERGENCY PROTOCOLS

### If Reddit scraper fails:
```bash
# Manual fallback: Use Reddit JSON API (no auth needed for read)
# Example: https://www.reddit.com/r/spotify/search.json?q=discover+new+music&sort=relevance&t=year&limit=100
# Save JSON, convert to CSV using Python
```

### If App Store scraper fails:
```bash
# Use appfigures.com free trial (14 days) or
# Manual: https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580 → scroll to reviews
# Copy-paste into CSV (tedious but works for 200-300 reviews)
```

### If Play Store scraper fails:
```bash
# Same as App Store — manual copy-paste from:
# https://play.google.com/store/apps/details?id=com.spotify.music&hl=en
```

### If Gemini API fails completely:
**Use Gemini Advanced web interface (your Pro subscription):**
1. Export clean data as chunks of 50 reviews
2. Paste into Gemini Advanced with the prompts from `web_prompts/`
3. This is slower but unlimited and free with your subscription

### If you only have 24 hours left:
**Nuclear option:**
1. Skip Play Store (use only Reddit + App Store)
2. Skip deep JTBD analysis (use only bulk extraction)
3. Skip competitive analysis
4. Focus on: 1 strong insight + 2 segments + 3 opportunities + 1 recommendation
5. A focused 10-slide deck with depth beats a scattered 20-slide deck

---

## ✅ DAY 1 CHECKLIST (Before you sleep)

- [ ] All 3 scrapers ran successfully
- [ ] Cleaned dataset has 2,000+ rows
- [ ] AI analysis completed (or web backup prompts generated)
- [ ] Top 20 evidence quotes read and feel real
- [ ] Problem statement drafted (1 paragraph)
- [ ] Slide outline sketched (10 slides)

## ✅ DAY 2 CHECKLIST (Before submission)

- [ ] 6 research questions answered with evidence
- [ ] 3 user segments named and described
- [ ] JTBD map complete
- [ ] Top 5 opportunities scored with ICE
- [ ] 10-slide deck complete
- [ ] PDF backup saved
- [ ] 3 expected Q&A answers written
- [ ] Read submission aloud once
- [ ] No placeholder text anywhere
- [ ] Submitted 30 minutes before deadline (buffer for tech issues)

---

## 💪 MINDSET FOR 2 DAYS

**This is a sprint, not a marathon.**

- **Perfection is the enemy.** A 9/10 submission that exists beats a 10/10 idea that doesn't.
- **The AI does the grunt work. You do the thinking.** Your value is in synthesis, judgment, and narrative — not in counting words.
- **Sleep is non-negotiable.** A tired brain makes bad PM decisions. 6 hours minimum each night.
- **If stuck for >30 minutes, move on.** Flag it, come back later. Momentum matters more than any single slide.

**You have everything you need in the toolkit. Execute ruthlessly.**
