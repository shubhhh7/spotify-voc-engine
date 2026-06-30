# Spotify VoC Intelligence Platform — Architecture Document

## Overview

Transform the existing Python scraper scripts into a modern web application that serves as an internal AI-powered Review Intelligence platform for Product Managers.

---

## 1. Folder Structure

```
spotify-voc-platform/
├── frontend/                          # Next.js App Router
│   ├── app/
│   │   ├── layout.tsx                 # Root layout (sidebar, dark mode)
│   │   ├── page.tsx                   # Dashboard
│   │   ├── scrapers/
│   │   │   └── page.tsx               # Scraper control panel
│   │   ├── reviews/
│   │   │   └── page.tsx               # Review browser
│   │   ├── insights/
│   │   │   └── page.tsx               # Insight generation
│   │   ├── reports/
│   │   │   └── page.tsx               # Report viewer
│   │   └── settings/
│   │       └── page.tsx               # API keys & config
│   ├── components/
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── dashboard/
│   │   │   ├── stats-cards.tsx
│   │   │   ├── review-trend-chart.tsx
│   │   │   ├── source-distribution.tsx
│   │   │   ├── sentiment-chart.tsx
│   │   │   └── recent-activity.tsx
│   │   ├── scrapers/
│   │   │   ├── scraper-card.tsx
│   │   │   ├── scraper-progress.tsx
│   │   │   └── live-logs.tsx
│   │   ├── reviews/
│   │   │   ├── review-table.tsx
│   │   │   ├── review-filters.tsx
│   │   │   └── review-row.tsx
│   │   ├── insights/
│   │   │   ├── workflow-selector.tsx
│   │   │   ├── insight-progress.tsx
│   │   │   └── insight-card.tsx
│   │   ├── reports/
│   │   │   ├── report-list.tsx
│   │   │   └── report-viewer.tsx
│   │   └── shared/
│   │       ├── sidebar.tsx
│   │       ├── header.tsx
│   │       ├── loading-skeleton.tsx
│   │       └── empty-state.tsx
│   ├── lib/
│   │   ├── api.ts                     # API client (fetch wrapper)
│   │   └── utils.ts                   # Formatters, helpers
│   ├── hooks/
│   │   ├── use-scraper-status.ts      # Polling hook
│   │   └── use-reviews.ts
│   ├── types/
│   │   └── index.ts                   # TypeScript interfaces
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── package.json
│
├── backend/                           # FastAPI
│   ├── main.py                        # FastAPI app entry
│   ├── config.py                      # Settings (env vars)
│   ├── database.py                    # SQLAlchemy engine + session
│   ├── models.py                      # SQLAlchemy ORM models
│   ├── schemas.py                     # Pydantic request/response schemas
│   ├── routers/
│   │   ├── scrapers.py                # /scrapers endpoints
│   │   ├── reviews.py                 # /reviews endpoints
│   │   ├── insights.py                # /insights endpoints
│   │   ├── reports.py                 # /reports endpoints
│   │   ├── dashboard.py               # /dashboard stats
│   │   └── settings.py                # /settings endpoints
│   ├── services/
│   │   ├── scraper_service.py         # Wraps existing scraper scripts
│   │   ├── cleaning_service.py        # Wraps 4_data_cleaner.py
│   │   ├── analysis_service.py        # Wraps 5_gemini_analyzer.py
│   │   └── insight_service.py         # Wraps 6_insight_synthesizer.py
│   ├── scrapers/                      # Your existing scraper scripts (unchanged)
│   │   ├── reddit_scraper.py          # Copy of 1_reddit_scraper.py
│   │   ├── appstore_scraper.py        # Copy of 2_appstore_scraper.py
│   │   ├── playstore_scraper.py       # Copy of 3_playstore_scraper.py
│   │   ├── community_scraper.py       # Copy of 7_community_scraper.py
│   │   ├── social_scraper.py          # Copy of 8_social_scraper.py
│   │   └── base.py                    # Scraper interface/adapter
│   ├── ai/
│   │   ├── gemini_client.py           # Gemini API wrapper
│   │   ├── grok_client.py             # Grok API wrapper
│   │   └── workflows.py              # Insight workflow definitions
│   ├── alembic/                       # DB migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── requirements.txt
│   └── alembic.ini
│
└── README.md
```

---

## 2. Database Schema

```sql
-- Reviews table: stores all scraped reviews
CREATE TABLE reviews (
    id              TEXT PRIMARY KEY,        -- e.g. "reddit_abc123"
    source          TEXT NOT NULL,           -- reddit, app_store, play_store, etc.
    text_original   TEXT NOT NULL,
    text_clean      TEXT,
    title           TEXT,
    author          TEXT,
    rating          FLOAT,
    score           INTEGER,
    sentiment       TEXT,                    -- positive, negative, neutral
    date            TIMESTAMP,
    url             TEXT,
    country         TEXT,
    language        TEXT DEFAULT 'en',
    quality_score   INTEGER,
    relevance       TEXT,                    -- relevant, partially_relevant, not_relevant
    metadata        JSONB,                   -- flexible: subreddit, flair, version, etc.
    scrape_run_id   INTEGER REFERENCES scrape_runs(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Scrape runs: tracks each scraper execution
CREATE TABLE scrape_runs (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,           -- which scraper ran
    status          TEXT NOT NULL,           -- pending, running, completed, failed
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    reviews_found   INTEGER DEFAULT 0,
    reviews_new     INTEGER DEFAULT 0,       -- net new (after dedup)
    errors          TEXT[],
    runtime_seconds FLOAT,
    config_snapshot JSONB                    -- settings used for this run
);

-- Insights: stores AI-generated analysis results
CREATE TABLE insights (
    id              SERIAL PRIMARY KEY,
    workflow        TEXT NOT NULL,           -- executive_summary, pain_points, etc.
    title           TEXT,
    content         JSONB NOT NULL,          -- structured insight output
    sources_used    TEXT[],                  -- which sources were analyzed
    review_count    INTEGER,                 -- how many reviews fed in
    date_range_start DATE,
    date_range_end  DATE,
    ai_model        TEXT,                    -- gemini-1.5-pro, grok, etc.
    report_id       INTEGER REFERENCES reports(id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Reports: groups multiple insights into a saved report
CREATE TABLE reports (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT,
    workflows       TEXT[],                  -- which workflows were run
    sources         TEXT[],
    review_count    INTEGER,
    date_range_start DATE,
    date_range_end  DATE,
    status          TEXT DEFAULT 'completed', -- completed, generating
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Settings: key-value store for app configuration
CREATE TABLE settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reviews_source ON reviews(source);
CREATE INDEX idx_reviews_date ON reviews(date);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_scrape_run ON reviews(scrape_run_id);
CREATE INDEX idx_scrape_runs_status ON scrape_runs(status);
CREATE INDEX idx_insights_workflow ON insights(workflow);
CREATE INDEX idx_insights_report ON insights(report_id);
```

---

## 3. API Architecture

### Base URL: `/api/v1`

### Scrapers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scrapers` | List all scrapers with status |
| POST | `/scrapers/run` | Run selected scrapers (body: `{ sources: ["reddit", "play_store"] }`) |
| GET | `/scrapers/status` | Get current run status (progress, logs) |
| GET | `/scrapers/history` | Past scrape runs |
| POST | `/scrapers/stop` | Cancel running scrape |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reviews` | Paginated reviews with filters |
| GET | `/reviews/stats` | Review counts, distributions |
| GET | `/reviews/:id` | Single review detail |
| DELETE | `/reviews/:id` | Remove a review |

**Query params for GET /reviews:**
- `page` (default 1)
- `per_page` (default 25, max 100)
- `source` (filter by source)
- `sentiment` (positive/negative/neutral)
- `rating_min`, `rating_max`
- `date_from`, `date_to`
- `search` (full-text search on text_clean)
- `sort_by` (date, rating, quality_score)
- `sort_order` (asc, desc)

### Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/insights/generate` | Generate insights (body: `{ workflows, sources, date_range }`) |
| GET | `/insights/status` | Generation progress |
| GET | `/insights` | List past insights |
| GET | `/insights/:id` | Single insight detail |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports` | List all reports |
| GET | `/reports/:id` | Full report with insights |
| DELETE | `/reports/:id` | Delete a report |
| GET | `/reports/:id/export` | Export as PDF/JSON |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats` | Total reviews, today count, sources, last scrape |
| GET | `/dashboard/trend` | Reviews over time (for chart) |
| GET | `/dashboard/sources` | Source distribution (for pie chart) |
| GET | `/dashboard/sentiment` | Sentiment distribution |
| GET | `/dashboard/activity` | Recent activity feed |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings` | Get all settings (API keys masked) |
| PUT | `/settings` | Update settings |

---

## 4. Application Architecture

### Backend Service Layer

The backend wraps your existing scripts without rewriting them. Each scraper is adapted through a thin service layer:

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI Router Layer                                     │
│  (scrapers.py, reviews.py, insights.py, reports.py)      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Service Layer                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ScraperService│  │AnalysisService│  │InsightService│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────┐
│  Your Existing Scripts (unchanged)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ Reddit  │ │App Store│ │Play Store│ │Community│       │
│  │ Scraper │ │ Scraper │ │ Scraper │ │ Scraper │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│  ┌─────────┐ ┌─────────────┐ ┌───────────────────┐     │
│  │ Social  │ │Data Cleaner │ │Gemini Analyzer    │     │
│  │ Scraper │ │             │ │+ Insight Synth    │     │
│  └─────────┘ └─────────────┘ └───────────────────┘     │
└─────────────────────────────────────────────────────────┘
          │                                    │
┌─────────▼────────────────────────────────────▼──────────┐
│  PostgreSQL                                              │
│  reviews | scrape_runs | insights | reports | settings   │
└─────────────────────────────────────────────────────────┘
```

### Scraper Adapter Pattern

Each existing scraper is wrapped with a standard interface:

```python
# backend/scrapers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ScraperResult:
    status: str          # "completed" | "failed"
    reviews: list[dict]  # Raw review dicts
    errors: list[str]
    runtime_seconds: float

class BaseScraper(ABC):
    name: str
    source: str

    @abstractmethod
    def run(self, config: dict, progress_callback=None) -> ScraperResult:
        """Execute the scraper. progress_callback(current, total, message)"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Check if required config/keys are available."""
        pass
```

Each adapter calls the existing script's functions directly (e.g., `fetch_reddit_search_json`, `fetch_appstore_reviews`) rather than running the script as a subprocess. This gives real-time progress.

### Background Task Execution

Scrapers and insight generation run as **FastAPI BackgroundTasks** (no Celery needed):

```python
# Simplified — actual implementation uses asyncio
from fastapi import BackgroundTasks

@router.post("/scrapers/run")
async def run_scrapers(request: RunRequest, background_tasks: BackgroundTasks):
    run_id = create_scrape_run(request.sources)
    background_tasks.add_task(execute_scrapers, run_id, request.sources)
    return {"run_id": run_id, "status": "started"}
```

Progress is tracked in the `scrape_runs` table and polled by the frontend.

### Frontend Data Flow

```
Next.js Page → useQuery (polling) → /api/v1/endpoint → FastAPI → PostgreSQL
```

No WebSockets needed. Simple polling every 2-3 seconds during active operations.

---

## 5. UI Wireframes (Component Layout)

### Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Sidebar │  Dashboard                                     │
│         │                                                │
│ 📊 Dash │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│
│ 🔄 Scr  │  │ Total  │ │ Today  │ │Sources │ │ Last   ││
│ 📝 Rev  │  │Reviews │ │Reviews │ │Connect │ │ Scrape ││
│ 💡 Ins  │  │ 2,847  │ │   34   │ │  5/6   │ │ 2h ago ││
│ 📄 Rep  │  └────────┘ └────────┘ └────────┘ └────────┘│
│ ⚙️ Set  │                                               │
│         │  ┌─────────────────┐ ┌────────────────────┐  │
│         │  │ Review Trend    │ │ Source Distribution │  │
│         │  │ (line chart)    │ │ (donut chart)       │  │
│         │  │                 │ │                     │  │
│         │  └─────────────────┘ └────────────────────┘  │
│         │                                               │
│         │  ┌─────────────────┐ ┌────────────────────┐  │
│         │  │Sentiment Dist.  │ │ Recent Activity    │  │
│         │  │ (bar chart)     │ │ • Reddit scraped   │  │
│         │  │                 │ │ • Insights gen'd   │  │
│         │  └─────────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Scrapers Page
```
┌─────────────────────────────────────────────────────────┐
│ Sidebar │  Scrapers                   [Run Selected ▶]  │
│         │                                                │
│         │  ┌─ ☑ Reddit ─────────────────────────────┐   │
│         │  │  Status: Ready  │  Last: 2h ago         │   │
│         │  │  Reviews: 847   │  Runtime: 3m 22s      │   │
│         │  └─────────────────────────────────────────┘   │
│         │  ┌─ ☑ Play Store ──────────────────────────┐   │
│         │  │  Status: Ready  │  Last: 2h ago         │   │
│         │  │  Reviews: 598   │  Runtime: 1m 45s      │   │
│         │  └─────────────────────────────────────────┘   │
│         │  ┌─ ☐ App Store ───────────────────────────┐   │
│         │  │  Status: Ready  │  Last: 5h ago         │   │
│         │  │  Reviews: 412   │  Runtime: 2m 10s      │   │
│         │  └─────────────────────────────────────────┘   │
│         │  ┌─ ☑ Spotify Community ───────────────────┐   │
│         │  │  Status: Ready  │  Last: 1d ago         │   │
│         │  │  Reviews: 156   │  Runtime: 4m 05s      │   │
│         │  └─────────────────────────────────────────┘   │
│         │  ┌─ ☐ HackerNews ──────────────────────────┐   │
│         │  │  Status: Ready  │  Last: Never          │   │
│         │  │  Reviews: 0     │  Runtime: —           │   │
│         │  └─────────────────────────────────────────┘   │
│         │                                                │
│         │  ── Running ───────────────────────────────    │
│         │  ┌─────────────────────────────────────────┐   │
│         │  │ Progress: ████████░░ 3/5 sources        │   │
│         │  │ Current:  Play Store (127 reviews)      │   │
│         │  │ ETA:      ~2 min remaining              │   │
│         │  ├─────────────────────────────────────────┤   │
│         │  │ > Fetching US Play Store...             │   │
│         │  │ > ✅ 298 reviews                       │   │
│         │  │ > Fetching GB Play Store...             │   │
│         │  │ > ✅ 127 reviews so far                │   │
│         │  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Reviews Page
```
┌─────────────────────────────────────────────────────────┐
│ Sidebar │  Reviews                                       │
│         │                                                │
│         │  ┌ Search ─────────────────────────────────┐  │
│         │  │ 🔍 Search reviews...                     │  │
│         │  └─────────────────────────────────────────┘  │
│         │  Filters: [Source ▾] [Sentiment ▾] [Rating ▾] │
│         │           [Date From] [Date To]               │
│         │                                                │
│         │  ┌──────┬───────┬──────┬──────────────┬─────┐│
│         │  │Source│Rating │Date  │Review        │Sent.││
│         │  ├──────┼───────┼──────┼──────────────┼─────┤│
│         │  │Reddit│  —    │Jun 25│The algorithm │ 😡  ││
│         │  │      │       │      │keeps playing…│     ││
│         │  ├──────┼───────┼──────┼──────────────┼─────┤│
│         │  │Play  │ ⭐⭐  │Jun 24│Daily mix has │ 😐  ││
│         │  │Store │       │      │same songs…   │     ││
│         │  ├──────┼───────┼──────┼──────────────┼─────┤│
│         │  │App   │ ⭐⭐⭐⭐│Jun 23│Great app but │ 😊  ││
│         │  │Store │       │      │discovery…    │     ││
│         │  └──────┴───────┴──────┴──────────────┴─────┘│
│         │                                                │
│         │  ← 1  2  3  4  5 ... 47 →    Showing 1-25    │
└─────────────────────────────────────────────────────────┘
```

### Insights Page
```
┌─────────────────────────────────────────────────────────┐
│ Sidebar │  Generate Insights                             │
│         │                                                │
│         │  Sources: [☑ All] [☑ Reddit] [☑ Play Store]   │
│         │  Date:    [Jun 1, 2025] → [Jun 28, 2025]      │
│         │                                                │
│         │  Workflows:                                    │
│         │  ┌─────────────────────────────────────────┐  │
│         │  │ ☑ Executive Summary                      │  │
│         │  │ ☑ Pain Points                            │  │
│         │  │ ☑ Feature Requests                       │  │
│         │  │ ☐ Positive Feedback                      │  │
│         │  │ ☐ Negative Feedback                      │  │
│         │  │ ☑ Sentiment Analysis                     │  │
│         │  │ ☐ Competitor Mentions                    │  │
│         │  │ ☐ Jobs To Be Done                        │  │
│         │  │ ☐ User Personas                          │  │
│         │  │ ☐ Theme Clustering                       │  │
│         │  │ ☐ Emerging Trends                        │  │
│         │  │ ☐ Product Recommendations                │  │
│         │  └─────────────────────────────────────────┘  │
│         │                                                │
│         │  [Generate Insights ▶]                         │
│         │                                                │
│         │  ── Progress ──────────────────────────────    │
│         │  Overall: ████████░░ 3/4 workflows             │
│         │  Current: "Pain Points" — Analyzing batch 2/5  │
│         │  ETA: ~1 min remaining                         │
│         │                                                │
│         │  ── Results ───────────────────────────────    │
│         │  ▼ Executive Summary                           │
│         │  │  Based on 2,847 reviews across 5 sources…  │
│         │  │  Key findings: ...                          │
│         │  │                                             │
│         │  ▶ Pain Points (click to expand)               │
│         │  ▶ Feature Requests (click to expand)          │
│         │                                                │
│         │  [Save as Report]                              │
└─────────────────────────────────────────────────────────┘
```

---

## 6. User Flows

### Flow 1: Scraping
```
User opens Scrapers page
  → Sees all scraper cards with last run info
  → Checks Reddit, Play Store, Spotify Community
  → Clicks "Run Selected Scrapers"
  → UI shows progress panel with live updates
  → Each scraper runs sequentially via BackgroundTask
  → Progress polls every 2s: GET /scrapers/status
  → On completion: toast notification
  → Reviews stored in PostgreSQL
  → Dashboard stats auto-update on next visit
```

### Flow 2: Browsing Reviews
```
User opens Reviews page
  → Paginated table loads (GET /reviews?page=1)
  → User types "shuffle" in search bar
  → Table filters live (debounced 300ms)
  → User selects "Source: Reddit" and "Sentiment: Negative"
  → Results narrow to relevant reviews
  → User clicks a row for detail view (modal)
```

### Flow 3: Generating Insights
```
User opens Insights page
  → Selects sources: Reddit, Play Store
  → Selects date range: Last 30 days
  → Checks workflows: Executive Summary, Pain Points, Feature Requests
  → Clicks "Generate Insights"
  → POST /insights/generate fires
  → UI shows progress with current workflow name
  → Backend queries reviews from DB, chunks them
  → Sends batches to Gemini/Grok
  → Each workflow result saved as it completes
  → Frontend polls progress every 3s
  → Results appear as collapsible cards
  → User clicks "Save as Report"
  → Report saved (POST creates report + links insights)
```

### Flow 4: Viewing Reports
```
User opens Reports page
  → Sees list of past reports with date, title, workflow count
  → Clicks a report → expands to show all insight cards
  → Can export as JSON
  → Can delete (with confirmation dialog)
```

---

## 7. Development Roadmap

### Milestone 1: Project Skeleton & Database
**Objective:** Set up both projects, database connection, basic health check.

**Files to create:**
- `backend/main.py` — FastAPI app with CORS, health endpoint
- `backend/config.py` — Environment settings
- `backend/database.py` — SQLAlchemy async engine
- `backend/models.py` — All ORM models
- `backend/alembic/` — Migration setup
- `frontend/` — Next.js scaffolding with shadcn/ui, TailwindCSS, dark mode

**API Endpoints:**
- `GET /health` → `{ status: "ok" }`

**Database changes:** Create all tables via Alembic migration

**Testing:**
- Backend starts: `uvicorn main:app`
- Frontend starts: `npm run dev`
- `/health` returns 200
- Tables created in PostgreSQL

**Definition of Done:** Both apps run, DB connected, dark mode layout renders.

---

### Milestone 2: Scraper Integration
**Objective:** Wrap existing scrapers, run them from API, store results in DB.

**Files to create:**
- `backend/scrapers/base.py` — Scraper interface
- `backend/scrapers/reddit_scraper.py` — Adapter for 1_reddit_scraper.py
- `backend/scrapers/appstore_scraper.py` — Adapter for 2_appstore_scraper.py
- `backend/scrapers/playstore_scraper.py` — Adapter for 3_playstore_scraper.py
- `backend/scrapers/community_scraper.py` — Adapter for 7_community_scraper.py
- `backend/scrapers/social_scraper.py` — Adapter for 8_social_scraper.py
- `backend/services/scraper_service.py` — Orchestrates scraper runs
- `backend/services/cleaning_service.py` — Wraps 4_data_cleaner.py
- `backend/routers/scrapers.py` — API routes
- `backend/schemas.py` — Pydantic models

**API Endpoints:**
- `GET /scrapers` — List scrapers + status
- `POST /scrapers/run` — Start scrape
- `GET /scrapers/status` — Poll progress
- `GET /scrapers/history` — Past runs

**Database changes:** None (tables exist from M1)

**Testing:**
- `POST /scrapers/run { sources: ["reddit"] }` triggers scraper
- Reviews appear in `reviews` table
- Status endpoint shows progress
- Completed run logged in `scrape_runs`

**Definition of Done:** All 5 scrapers runnable via API, reviews stored in DB.

---

### Milestone 3: Reviews API & Frontend Table
**Objective:** Browse, search, and filter reviews from the UI.

**Files to create:**
- `backend/routers/reviews.py` — CRUD + filters
- `frontend/app/reviews/page.tsx`
- `frontend/components/reviews/review-table.tsx`
- `frontend/components/reviews/review-filters.tsx`
- `frontend/lib/api.ts`
- `frontend/types/index.ts`

**API Endpoints:**
- `GET /reviews` — Paginated with all query params
- `GET /reviews/stats`

**Testing:**
- Reviews page shows table with data
- Search filters work (source, sentiment, date, keyword)
- Pagination works
- Responsive on mobile

**Definition of Done:** Full review browsing experience with all filters working.

---

### Milestone 4: Scrapers Frontend
**Objective:** Control scrapers from the UI with live progress.

**Files to create:**
- `frontend/app/scrapers/page.tsx`
- `frontend/components/scrapers/scraper-card.tsx`
- `frontend/components/scrapers/scraper-progress.tsx`
- `frontend/components/scrapers/live-logs.tsx`
- `frontend/hooks/use-scraper-status.ts`

**Testing:**
- Scraper cards render with correct status
- Selecting scrapers and clicking Run triggers API
- Progress bar updates live
- Live log panel scrolls with output
- Toast on completion

**Definition of Done:** Full scraper control from UI matching wireframe.

---

### Milestone 5: Insights & AI Integration
**Objective:** Generate insights using Gemini/Grok from the UI.

**Files to create:**
- `backend/ai/gemini_client.py`
- `backend/ai/grok_client.py`
- `backend/ai/workflows.py` — Defines all 12 workflows
- `backend/services/insight_service.py`
- `backend/routers/insights.py`
- `frontend/app/insights/page.tsx`
- `frontend/components/insights/workflow-selector.tsx`
- `frontend/components/insights/insight-progress.tsx`
- `frontend/components/insights/insight-card.tsx`

**API Endpoints:**
- `POST /insights/generate`
- `GET /insights/status`
- `GET /insights`

**Testing:**
- Select workflows + sources → Generate runs
- Progress shows current workflow
- Results render in collapsible cards
- Save as Report works

**Definition of Done:** All 12 workflows functional, results display correctly.

---

### Milestone 6: Reports & Dashboard
**Objective:** Reports CRUD and dashboard with charts.

**Files to create:**
- `backend/routers/reports.py`
- `backend/routers/dashboard.py`
- `frontend/app/page.tsx` (dashboard)
- `frontend/app/reports/page.tsx`
- `frontend/components/dashboard/*`
- `frontend/components/reports/*`

**API Endpoints:**
- All `/reports` and `/dashboard` endpoints

**Testing:**
- Dashboard shows correct stats and charts
- Reports list, view, delete, export all work
- Charts render with real data (Recharts)

**Definition of Done:** Polished dashboard and reports experience.

---

### Milestone 7: Settings & Polish
**Objective:** Settings page, dark mode toggle, error handling, loading states.

**Files to create:**
- `backend/routers/settings.py`
- `frontend/app/settings/page.tsx`
- Polish: loading skeletons, empty states, error boundaries, toast notifications

**Testing:**
- API keys save and load (masked in UI)
- Dark/light mode persists
- All loading states show skeletons
- Errors show toast notifications
- Empty states show helpful messages

**Definition of Done:** Production-ready feel. No broken states.

---

### Milestone 8: Deployment
**Objective:** Deploy frontend to Vercel, backend + DB to Railway.

**Tasks:**
- Configure Railway PostgreSQL
- Deploy FastAPI to Railway
- Deploy Next.js to Vercel
- Set environment variables
- Test end-to-end in production

**Definition of Done:** App accessible via public URL, all features working.

---

## 8. Design Tokens & Conventions

### UI Principles
- **Whitespace:** Generous padding (p-6 on cards, gap-6 between sections)
- **Corners:** Rounded (rounded-lg on cards, rounded-md on buttons)
- **Typography:** System font stack, semibold headings, regular body
- **Colors:** Neutral grays, accent blue for actions, red/yellow/green for status
- **Animations:** `transition-all duration-200` — subtle hover and state changes
- **Dark mode:** `dark:` Tailwind classes throughout, toggle in header

### Component Library
All UI components from **shadcn/ui**:
- Card, Table, Button, Input, Select, Badge
- Dialog, Sheet, Toast, Skeleton
- Tabs, Checkbox, Progress, Separator

### Charts
All charts via **Recharts**:
- LineChart for trends
- BarChart for distributions
- PieChart/DonutChart for source breakdown

---

## 9. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State management | React Query (TanStack Query) | Server state caching + polling built-in |
| Background tasks | FastAPI BackgroundTasks | Simple, no infra overhead |
| Progress tracking | DB polling (2-3s interval) | Simpler than WebSockets for this scale |
| Scraper execution | Sequential per run | Avoids rate limit issues across sources |
| AI rate limiting | Built into service layer | Respects Gemini/Grok RPM limits |
| Auth | None (internal tool) | Single-user PM tool, behind VPN/local |
| File storage | PostgreSQL JSONB | No S3 needed for structured data |
| Search | PostgreSQL full-text + ILIKE | Good enough for ~10K reviews |
| Export | Server-side JSON generation | Simple, no PDF library needed initially |

---

## 10. Adding a New Scraper

To add a new source (e.g., YouTube Comments):

1. Create `backend/scrapers/youtube_scraper.py` implementing `BaseScraper`
2. Register it in `backend/services/scraper_service.py` SCRAPER_REGISTRY
3. Add source to frontend's scraper list (single constant)
4. Run — the scraper card auto-appears in UI

No database migration needed. The `reviews` table handles any source via the `source` column and `metadata` JSONB field.

---

## Summary

This architecture prioritizes:
- **Simplicity** — No message queues, no containers, no microservices
- **Modularity** — New scrapers plug in with one file
- **Wrapping not rewriting** — Your existing scripts stay intact
- **PM-friendly UX** — Clean, responsive, usable daily
- **Incremental delivery** — Each milestone is independently testable

Ready to start with Milestone 1 on your approval.
