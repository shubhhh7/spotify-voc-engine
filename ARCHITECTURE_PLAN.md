# 🏗️ Architecture & Phase-Wise Implementation Plan

## Spotify VoC (Voice of Customer) Engine — System Architecture

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SPOTIFY VoC ENGINE — 2-DAY PIPELINE                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────── PHASE 1: DATA INGESTION LAYER ─────────────────────────┐
│                                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ Reddit Scraper  │  │ App Store Scraper│  │ Play Store Scraper│          │
│  │ (1_reddit_*.py) │  │ (2_appstore_*.py)│  │ (3_playstore_*.py)│          │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                      │                    │
│  ┌────────▼────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐          │
│  │ Reddit JSON API │  │ app-store-scraper│  │google-play-scraper│          │
│  │  + PullPush     │  │    (library)     │  │    (library)      │          │
│  │  (fallback)     │  │                  │  │                   │          │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                      │                    │
│           ▼                     ▼                      ▼                    │
│     reddit_posts.csv     appstore_reviews.csv   playstore_reviews.csv      │
│                          data/raw/                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────── PHASE 2: DATA PROCESSING LAYER ────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Data Cleaner (4_data_cleaner.py)                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ① Merge 3 CSVs  →  ② Text Cleaning  →  ③ Language Detection      │   │
│  │  ④ Deduplication (TF-IDF + Cosine Similarity)  →  ⑤ Enrichment    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                         │
│                        data/clean/merged_reviews.csv                        │
│                          (~2,000+ cleaned records)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────── PHASE 3: AI ANALYSIS LAYER ────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │               Gemini AI Analyzer (5_gemini_analyzer.py)             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌─── PHASE 3A: Bulk Extraction ───┐  ┌── PHASE 3B: Deep JTBD ──┐ │   │
│  │  │  Model: Gemini 1.5 Flash        │  │  Model: Gemini 1.5 Pro   │ │   │
│  │  │  Batch size: 60 reviews          │  │  Individual analysis     │ │   │
│  │  │  Rate: 30 RPM                   │  │  Rate: 10 RPM            │ │   │
│  │  │  ALL 2,000+ records             │  │  Top 40 severe items     │ │   │
│  │  │  Output: extractions.csv        │  │  Output: deep_jtbd.csv   │ │   │
│  │  └─────────────────────────────────┘  └──────────────────────────┘ │   │
│  │                                                                     │   │
│  │  ┌────────────────── PHASE 3C: Merge ──────────────────────────┐   │   │
│  │  │  Combines original data + Flash extractions + Pro deep JTBD │   │   │
│  │  │  Output: analyzed_reviews.csv                                │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                        data/analyzed/analyzed_reviews.csv                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────── PHASE 4: SYNTHESIS LAYER ──────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │            Insight Synthesizer (6_insight_synthesizer.py)            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐   │   │
│  │  │Cross-Source  │  │  Competitive     │  │  Executive Report  │   │   │
│  │  │Theme Synthesis│  │  Intelligence    │  │  Generation        │   │   │
│  │  │(Pro Model)   │  │  (Pro Model)     │  │  (Pro Model)       │   │   │
│  │  └──────┬───────┘  └────────┬─────────┘  └─────────┬──────────┘   │   │
│  │         ▼                    ▼                       ▼              │   │
│  │  synthesis.json      competitive.json      executive_report.txt    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────── Summary Tables ──────────────┐                             │
│  │  pain_summary.csv   │  needs_summary.csv  │                             │
│  │  segment_summary.csv│  top_evidence.csv   │                             │
│  └───────────────────────────────────────────┘                             │
│                                                                             │
│                           data/final/                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────── PHASE 5: VALIDATION LAYER ─────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 Quick Validator (quick_validate.py)                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ① Quote Verification (AI quotes vs source text)                    │   │
│  │  ② Category Distribution Validation                                 │   │
│  │  ③ Anomaly Detection                                                │   │
│  │  ④ Accuracy Scoring (target: >80%)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │          Web Backup (gemini_web_backup.py) — FALLBACK               │   │
│  │  Generates copy-paste prompts if API fails                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────── PHASE 6: PRESENTATION LAYER (Manual) ──────────────────┐
│                                                                             │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Slide Deck │  │ ICE Scoring  │  │ Segment Naming│  │ Q&A Prep      │   │
│  │ (10 slides)│  │ (Override AI)│  │ (Human Touch) │  │ (5 questions) │   │
│  └────────────┘  └──────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Dependency Graph

```
config_turbo.py ←── .env (GEMINI_API_KEY)
       │
       ├──→ 1_reddit_scraper.py     (uses: requests, pandas)
       ├──→ 2_appstore_scraper.py   (uses: app-store-scraper, pandas)
       ├──→ 3_playstore_scraper.py  (uses: google-play-scraper, pandas)
       ├──→ 4_data_cleaner.py       (uses: pandas, langdetect, sklearn)
       ├──→ 5_gemini_analyzer.py    (uses: google-generativeai, prompts.py)
       ├──→ 6_insight_synthesizer.py(uses: google-generativeai, prompts.py)
       └──→ quick_validate.py

prompts.py ←── 5_gemini_analyzer.py
           ←── 6_insight_synthesizer.py
           ←── gemini_web_backup.py

turbo_pipeline.py ──→ orchestrates all scripts sequentially
```

---

## Data Flow & File System

```
data/
├── raw/                          ← Phase 1 Output
│   ├── reddit_posts.csv          (~500-1500 rows: posts + comments)
│   ├── appstore_reviews.csv      (~600 rows: US + GB)
│   └── playstore_reviews.csv     (~600 rows: US + GB)
│
├── clean/                        ← Phase 2 Output
│   └── merged_reviews.csv        (~2,000+ rows: deduplicated, enriched)
│
├── analyzed/                     ← Phase 3 Output
│   ├── extractions.csv           (bulk AI analysis per record)
│   ├── deep_jtbd.csv             (deep analysis on top 40)
│   └── analyzed_reviews.csv      (merged final dataset)
│
└── final/                        ← Phase 4 Output
    ├── synthesis.json            (strategic insights, 10 sections)
    ├── competitive.json          (competitive threats & responses)
    ├── executive_report.txt      (2-page narrative)
    ├── pain_summary.csv          (top 10 pain categories)
    ├── needs_summary.csv         (top 15 unmet needs)
    ├── segment_summary.csv       (top 10 user segments)
    ├── top_evidence.csv          (top 20 powerful quotes)
    └── web_prompts/              (backup prompts for manual Gemini)
```

---

## Phase-Wise Implementation Plan

---

### PHASE 1: DATA INGESTION (Parallel, ~1.5 hours)

| Component | Script | Method | Volume | Fallback |
|-----------|--------|--------|--------|----------|
| Reddit | `1_reddit_scraper.py` | Public JSON API (`/search.json`) | 8 subreddits × 15 queries × 75 posts | PullPush API → Manual |
| App Store | `2_appstore_scraper.py` | `app-store-scraper` library | 2 countries × 300 reviews | Reduce count |
| Play Store | `3_playstore_scraper.py` | `google-play-scraper` library | 2 countries × 300 reviews | Reduce count |

**Key Design Decisions:**
- No Reddit API key required (public JSON endpoints)
- Automatic fallback cascade: Reddit JSON → PullPush → Manual
- Rate limiting: 2s between Reddit requests, 3s between store requests
- Minimum engagement filter: posts with ≥5 comments only
- Comment extraction: top 3 posts per query, 15 comments each

**Schema (Common Output):**
```
id | source | text | date | rating/score | author | type | ...metadata
```

---

### PHASE 2: DATA PROCESSING (Sequential, ~15 minutes)

| Step | Operation | Tech | Purpose |
|------|-----------|------|---------|
| 1 | Merge | pandas.concat | Unify 3 CSVs into one DataFrame |
| 2 | Text Cleaning | regex | Remove URLs, whitespace, encoding issues |
| 3 | Length Filter | config | Drop <25 chars or truncate >2500 chars |
| 4 | Language Detection | langdetect | Keep English only |
| 5 | Deduplication | TF-IDF + Cosine Similarity | Threshold: 0.88 |
| 6 | Feature Enrichment | pandas | Add: word_count, sentiment proxies, engagement flags |

**Deduplication Algorithm:**
```
For datasets >1000 rows:
  - Sliding window of 50 (O(n×50) vs O(n²))
  - TF-IDF with bigrams, max 1000 features
  - Cosine similarity threshold: 0.88

For datasets ≤1000 rows:
  - Full pairwise similarity matrix
  - Upper triangle comparison
```

**Enrichment Features Added:**
- `text_length`, `word_count`
- `has_exclamation`, `has_question`, `caps_count`
- `negative_proxy` (19 negative keywords)
- `positive_proxy` (12 positive keywords)
- `is_low_rating`, `is_high_engagement`

---

### PHASE 3: AI ANALYSIS (Sequential, ~3 hours)

#### Phase 3A — Bulk Extraction (Gemini Flash)

| Parameter | Value |
|-----------|-------|
| Model | `gemini-1.5-flash` |
| Batch Size | 60 reviews per API call |
| Rate Limit | 30 requests/minute |
| Temperature | 0.1 (deterministic) |
| Max Output Tokens | 8,192 |
| Total Calls | ~35 (for 2,000 reviews) |
| Time Estimate | 1.5 hours |

**Extraction Schema (per review):**
```json
{
  "pain_point": true,
  "pain_category": "Discovery",
  "pain_severity": 4,
  "sentiment": "Negative",
  "emotion": "Frustration",
  "jtbd_statement": "When I [X], I want to [Y], so I can [Z]",
  "discovery_issue": true,
  "recommendation_issue": false,
  "repetition_issue": true,
  "unmet_need": "Fresh music without manual search",
  "user_segment_hint": "Power User",
  "key_quote": "I keep hearing the same 50 songs",
  "confidence": 4
}
```

#### Phase 3B — Deep JTBD Analysis (Gemini Pro)

| Parameter | Value |
|-----------|-------|
| Model | `gemini-1.5-pro` |
| Selection | Top 40 by `pain_severity` |
| Rate Limit | 10 requests/minute |
| Temperature | 0.2 |
| Max Output Tokens | 4,096 |
| Time Estimate | 1 hour |

**Deep JTBD Schema:**
```json
{
  "main_jtbd": "When I..., I want to..., so I can...",
  "secondary_jtbd": ["...", "..."],
  "emotional_trigger": "Frustration with repetition",
  "struggle_moment": "Opening Discover Weekly to same genres",
  "workarounds": ["YouTube", "Ask friends", "Shazam"],
  "switching_triggers": ["Apple Music curation", "..."],
  "churn_risk": "High",
  "pain_intensity": 8
}
```

#### Phase 3C — Merge

Combines: `original data` ← LEFT JOIN → `extractions` ← MAP → `deep_jtbd`

---

### PHASE 4: SYNTHESIS (Sequential, ~30 minutes)

| Sub-step | Prompt | Input | Output |
|----------|--------|-------|--------|
| Cross-Source Synthesis | `SYNTHESIS_PROMPT` | Aggregated themes, JTBDs, segments | `synthesis.json` (10-section strategic report) |
| Competitive Analysis | `COMPETITIVE_PROMPT` | Top 30 severe complaints | `competitive.json` |
| Executive Report | `REPORT_PROMPT` | Volume stats + synthesis insights | `executive_report.txt` |
| Summary Tables | Pandas aggregation | Analyzed CSV columns | 4 summary CSVs |

**Synthesis JSON Structure (10 Sections):**
1. `executive_summary` — 3 bullets for leadership
2. `strategic_insights` — 5-7 contrarian insights with evidence
3. `discovery_problems` — Why users can't find new music
4. `recommendation_frustrations` — Algorithm complaints
5. `behavioral_patterns` — What users are trying to achieve
6. `repetition_causes` — Why users get stuck in loops
7. `segment_profiles` — 3-4 distinct user archetypes
8. `unmet_needs` — Consistent gaps across sources
9. `opportunity_scoring` — Top 5 with ICE scores
10. `counter_evidence` — What contradicts our narrative

---

### PHASE 5: VALIDATION (Sequential, ~15 minutes)

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Quote Verification | Fuzzy match AI quotes against source text | >80% accuracy |
| Category Distribution | Statistical check for skew/anomalies | No single category >50% |
| Completeness | Check for null/failed extractions | <10% error rate |
| Anomaly Detection | Flag suspicious patterns | No hallucinated quotes |

---

### PHASE 6: PRESENTATION (Manual, Day 2)

| Deliverable | Source File | Human Value-Add |
|-------------|-------------|-----------------|
| Problem Statement | `executive_report.txt` | Rewrite in own voice |
| User Segments | `segment_summary.csv` | Rename with memorable labels |
| JTBD Map | `deep_jtbd.csv` | Synthesize patterns |
| Opportunity Scores | `synthesis.json` → `opportunity_scoring` | Override with PM judgment |
| Competitive Framing | `competitive.json` | Add market context |
| Evidence Quotes | `top_evidence.csv` | Select most impactful |

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.8+ | Pipeline scripting |
| Config | python-dotenv | Secrets management |
| HTTP | requests | Reddit public API |
| Scraping | app-store-scraper, google-play-scraper | Store reviews |
| Data | pandas, numpy | Tabular processing |
| NLP | langdetect | Language filtering |
| ML | scikit-learn (TF-IDF, cosine similarity) | Deduplication |
| AI | google-generativeai | Gemini Flash + Pro |
| Progress | tqdm | Progress bars |
| Orchestration | turbo_pipeline.py (subprocess) | Sequential execution |

---

## Error Handling & Resilience

```
┌────────────────────────────────────────────────────────┐
│                 RESILIENCE STRATEGY                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Reddit:  JSON API → PullPush → Manual Guide           │
│  API:     Auto-retry (3x) → Exponential backoff        │
│  Rate:    Auto-throttle (sleep 60s on 429)             │
│  Quota:   Wait + retry → Web backup prompts            │
│  Parse:   JSON strip → bracket search → null fallback  │
│  Pipeline: Fail-fast per step (fix & re-run)           │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Execution Timeline

```
DAY 1
─────
Hour 0-0.5    │████│ Setup (Python, deps, API key, .env)
Hour 0.5-2    │████████████│ Phase 1: Scraping (parallel)
Hour 2-2.25   │██│ Phase 2: Cleaning
Hour 2.25-5   │████████████████████│ Phase 3: AI Analysis
Hour 5-5.5    │████│ Phase 4: Synthesis
Hour 5.5-6    │████│ Phase 5: Validation
Hour 6-10     │██████████████████████████│ Begin writing + slide outline

DAY 2
─────
Hour 0-4      │██████████████████████████│ Write answers + name segments
Hour 4-8      │██████████████████████████│ Build 10-slide deck
Hour 8-9      │██████│ Review, polish, rehearse
Hour 9-10     │██████│ Final check + submit
```

---

## Key Architectural Principles

1. **Fail-fast, resume-easy** — Each script is idempotent. Re-run any step without redoing previous ones.
2. **Parallel where possible** — 3 scrapers run simultaneously in separate terminals.
3. **Two-tier AI strategy** — Flash for volume (cheap, fast), Pro for depth (expensive, slow).
4. **Automatic fallbacks** — Every external dependency has a backup path.
5. **Human-in-the-loop** — AI generates raw material; human applies PM judgment for scoring, naming, and narrative.
6. **Progressive enrichment** — Each phase adds layers to the same dataset (raw → clean → analyzed → synthesized).
7. **Evidence-first** — Every insight traces back to a specific quote and source.
