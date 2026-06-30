# Spotify VoC Intelligence Platform — Execution Plan

## How to Use This Document

Each step is atomic. Complete it, test it, then move to the next.
Steps marked with 🔑 are critical path — do not skip.
Steps marked with 💡 are enhancements — can defer if behind schedule.

---

## Phase 1: Backend Foundation

### Step 1.1 🔑 — Initialize Backend Project

**What:** Create the FastAPI project structure with all dependencies.

```bash
mkdir -p spotify-voc-platform/backend
cd spotify-voc-platform/backend
```

**Create `requirements.txt`:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
alembic==1.13.2
psycopg2-binary==2.9.9
python-dotenv==1.0.1
pydantic==2.9.0
pydantic-settings==2.5.0
google-generativeai==0.8.0
pandas==2.2.2
requests==2.32.3
beautifulsoup4==4.12.3
tqdm==4.66.5
rapidfuzz==3.9.7
langdetect==1.0.9
emoji==2.12.1
app-store-scraper==0.3.5
google-play-scraper==1.2.7
```

**Create `backend/.env`:**
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/spotify_voc
GEMINI_API_KEY=your_key_here
GROK_API_KEY=your_key_here
ENVIRONMENT=development
```

**Test:** `pip install -r requirements.txt` completes without errors.

---

### Step 1.2 🔑 — Create Config & Database Connection

**Create `backend/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/spotify_voc"
    gemini_api_key: str = ""
    grok_api_key: str = ""
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Create `backend/database.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Test:** Python imports without errors: `python -c "from database import engine; print(engine.url)"`

---

### Step 1.3 🔑 — Define ORM Models

**Create `backend/models.py`:**
```python
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy import ForeignKey, ARRAY
from sqlalchemy.sql import func
from database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False, index=True)
    text_original = Column(Text, nullable=False)
    text_clean = Column(Text)
    title = Column(Text)
    author = Column(String)
    rating = Column(Float)
    score = Column(Integer)
    sentiment = Column(String, index=True)
    date = Column(DateTime, index=True)
    url = Column(Text)
    country = Column(String)
    language = Column(String, default="en")
    quality_score = Column(Integer)
    relevance = Column(String)
    metadata_ = Column("metadata", JSON)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    reviews_found = Column(Integer, default=0)
    reviews_new = Column(Integer, default=0)
    errors = Column(JSON, default=[])
    runtime_seconds = Column(Float)
    config_snapshot = Column(JSON)
    progress_current = Column(Integer, default=0)
    progress_total = Column(Integer, default=0)
    progress_message = Column(String, default="")

class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow = Column(String, nullable=False, index=True)
    title = Column(String)
    content = Column(JSON, nullable=False)
    sources_used = Column(JSON, default=[])
    review_count = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    ai_model = Column(String)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    workflows = Column(JSON, default=[])
    sources = Column(JSON, default=[])
    review_count = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    status = Column(String, default="completed")
    created_at = Column(DateTime, server_default=func.now())

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**Test:** `python -c "from models import Review, ScrapeRun, Insight, Report; print('Models OK')"`

---

### Step 1.4 🔑 — Setup Alembic Migrations

```bash
cd backend
alembic init alembic
```

**Edit `alembic/env.py`** — set `target_metadata = Base.metadata` and load DB URL from config.

**Edit `alembic.ini`** — set `sqlalchemy.url` to your database URL.

```bash
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```

**Test:** Connect to PostgreSQL and verify tables exist:
```bash
psql -d spotify_voc -c "\dt"
```
Should show: reviews, scrape_runs, insights, reports, settings.

---

### Step 1.5 🔑 — Create FastAPI App with Health Check

**Create `backend/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Spotify VoC Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

**Test:**
```bash
uvicorn main:app --reload --port 8000
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}
```

---

### Step 1.6 🔑 — Create Pydantic Schemas

**Create `backend/schemas.py`:**
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- Scrapers ---
class ScraperInfo(BaseModel):
    name: str
    source: str
    status: str  # ready, running, error
    last_run: Optional[datetime]
    reviews_collected: int
    runtime_seconds: Optional[float]

class RunScrapersRequest(BaseModel):
    sources: list[str]

class ScraperStatus(BaseModel):
    run_id: int
    status: str
    sources: list[str]
    progress_current: int
    progress_total: int
    current_source: Optional[str]
    current_message: Optional[str]
    reviews_collected: int

# --- Reviews ---
class ReviewResponse(BaseModel):
    id: str
    source: str
    text_clean: Optional[str]
    title: Optional[str]
    author: Optional[str]
    rating: Optional[float]
    sentiment: Optional[str]
    date: Optional[datetime]
    url: Optional[str]
    quality_score: Optional[int]

class ReviewsListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# --- Insights ---
class GenerateInsightsRequest(BaseModel):
    workflows: list[str]
    sources: list[str]
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class InsightResponse(BaseModel):
    id: int
    workflow: str
    title: Optional[str]
    content: dict
    review_count: Optional[int]
    ai_model: Optional[str]
    created_at: datetime

# --- Reports ---
class ReportResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    workflows: list[str]
    sources: list[str]
    review_count: Optional[int]
    created_at: datetime

# --- Dashboard ---
class DashboardStats(BaseModel):
    total_reviews: int
    reviews_today: int
    sources_connected: int
    total_sources: int
    last_scrape: Optional[datetime]
    last_insight_run: Optional[datetime]
```

**Test:** `python -c "from schemas import DashboardStats; print('Schemas OK')"`

---

## Phase 2: Scraper Integration

### Step 2.1 🔑 — Create Base Scraper Interface

**Create `backend/scrapers/__init__.py`** (empty)

**Create `backend/scrapers/base.py`:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional

@dataclass
class ScraperResult:
    status: str = "completed"        # completed | failed
    reviews: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    runtime_seconds: float = 0.0

class BaseScraper(ABC):
    name: str = "Unknown"
    source: str = "unknown"

    @abstractmethod
    def run(self, progress_callback: Optional[Callable] = None) -> ScraperResult:
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        pass
```

---

### Step 2.2 🔑 — Wrap Reddit Scraper

**Create `backend/scrapers/reddit_scraper.py`:**

This adapter imports functions from the original script and calls them with progress reporting.

```python
import time
from datetime import datetime
from scrapers.base import BaseScraper, ScraperResult

# Import the original script's functions directly
# (Copy 1_reddit_scraper.py into backend/scrapers/scripts/ and import)
from scrapers.scripts.reddit import fetch_reddit_search_json, fetch_comments_json

SUBREDDITS = ["spotify", "truespotify", "spotifywrapped", "WeAreTheMusicMakers", "music"]
QUERIES = ["discover new music", "recommendation algorithm", "playlist stuck same songs",
           "bored with spotify", "discovery weekly bad", "shuffle algorithm"]

class RedditScraper(BaseScraper):
    name = "Reddit"
    source = "reddit"

    def validate_config(self) -> bool:
        return True  # No API key needed

    def run(self, progress_callback=None) -> ScraperResult:
        start = time.time()
        all_posts = []
        errors = []
        total = len(SUBREDDITS) * len(QUERIES)
        current = 0

        for subreddit in SUBREDDITS:
            for query in QUERIES:
                current += 1
                if progress_callback:
                    progress_callback(current, total, f"r/{subreddit}: '{query}'")

                try:
                    posts = fetch_reddit_search_json(subreddit, query, limit=75)
                    all_posts.extend(posts or [])
                except Exception as e:
                    errors.append(f"r/{subreddit} '{query}': {str(e)}")

                time.sleep(2)

        return ScraperResult(
            status="completed" if all_posts else "failed",
            reviews=all_posts,
            errors=errors,
            runtime_seconds=time.time() - start
        )
```

**Pattern:** Repeat this for each scraper (appstore, playstore, community, social).
Each adapter lives in `backend/scrapers/` and imports from `backend/scrapers/scripts/`.

---

### Step 2.3 🔑 — Wrap Remaining Scrapers

Create the same adapter pattern for:
- `backend/scrapers/appstore_scraper.py` → wraps `fetch_appstore_reviews()`
- `backend/scrapers/playstore_scraper.py` → wraps `fetch_playstore_reviews()`
- `backend/scrapers/community_scraper.py` → wraps `fetch_spotify_community_search()` + `fetch_reddit_extra()`
- `backend/scrapers/social_scraper.py` → wraps `fetch_mastodon()`, `fetch_lemmy()`, `fetch_hackernews()`, etc.

**Copy original scripts:**
```bash
mkdir -p backend/scrapers/scripts
cp ../1_reddit_scraper.py backend/scrapers/scripts/reddit.py
cp ../2_appstore_scraper.py backend/scrapers/scripts/appstore.py
cp ../3_playstore_scraper.py backend/scrapers/scripts/playstore.py
cp ../7_community_scraper.py backend/scrapers/scripts/community.py
cp ../8_social_scraper.py backend/scrapers/scripts/social.py
```

Remove the `if __name__ == "__main__"` blocks from the copies (or guard them).
The adapters import individual functions, not the `main()`.

---

### Step 2.4 🔑 — Scraper Service (Orchestrator)

**Create `backend/services/scraper_service.py`:**
```python
import time
from datetime import datetime
from sqlalchemy.orm import Session
from models import ScrapeRun, Review
from scrapers.reddit_scraper import RedditScraper
from scrapers.appstore_scraper import AppStoreScraper
from scrapers.playstore_scraper import PlayStoreScraper
from scrapers.community_scraper import CommunityScraper
from scrapers.social_scraper import SocialScraper

SCRAPER_REGISTRY = {
    "reddit": RedditScraper,
    "app_store": AppStoreScraper,
    "play_store": PlayStoreScraper,
    "spotify_community": CommunityScraper,
    "social": SocialScraper,
}

# Global state for current run (simple — single user tool)
current_run = {
    "run_id": None,
    "status": "idle",
    "sources": [],
    "progress_current": 0,
    "progress_total": 0,
    "current_source": None,
    "current_message": "",
    "reviews_collected": 0,
    "logs": [],
}

def execute_scrapers(run_id: int, sources: list[str], db: Session):
    """Runs in a background task. Updates DB and current_run dict."""
    global current_run
    current_run["run_id"] = run_id
    current_run["status"] = "running"
    current_run["sources"] = sources
    current_run["progress_total"] = len(sources)
    current_run["logs"] = []

    for i, source in enumerate(sources):
        current_run["progress_current"] = i
        current_run["current_source"] = source

        scraper_cls = SCRAPER_REGISTRY.get(source)
        if not scraper_cls:
            current_run["logs"].append(f"❌ Unknown source: {source}")
            continue

        scraper = scraper_cls()
        current_run["logs"].append(f"▶ Starting {scraper.name}...")

        def progress_cb(curr, total, msg):
            current_run["current_message"] = msg
            current_run["logs"].append(f"  {msg}")

        result = scraper.run(progress_callback=progress_cb)

        # Store reviews in DB (dedup by ID)
        new_count = 0
        for review_data in result.reviews:
            existing = db.query(Review).filter(Review.id == review_data["id"]).first()
            if not existing:
                review = Review(
                    id=review_data["id"],
                    source=review_data.get("source", source),
                    text_original=review_data.get("text", ""),
                    title=review_data.get("title"),
                    author=review_data.get("author"),
                    rating=review_data.get("rating"),
                    score=review_data.get("score"),
                    date=review_data.get("created_utc") or review_data.get("date"),
                    url=review_data.get("url"),
                    scrape_run_id=run_id,
                )
                db.add(review)
                new_count += 1

        db.commit()
        current_run["reviews_collected"] += new_count
        current_run["logs"].append(
            f"  ✅ {scraper.name}: {len(result.reviews)} found, {new_count} new"
        )

    # Mark run complete
    run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
    run.status = "completed"
    run.completed_at = datetime.utcnow()
    run.reviews_new = current_run["reviews_collected"]
    db.commit()

    current_run["status"] = "completed"
    current_run["progress_current"] = len(sources)
```

**Test:** Import and verify: `python -c "from services.scraper_service import SCRAPER_REGISTRY; print(list(SCRAPER_REGISTRY.keys()))"`

---

### Step 2.5 🔑 — Scrapers Router

**Create `backend/routers/__init__.py`** (empty)

**Create `backend/routers/scrapers.py`:**
```python
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import ScrapeRun
from schemas import RunScrapersRequest, ScraperStatus, ScraperInfo
from services.scraper_service import (
    SCRAPER_REGISTRY, execute_scrapers, current_run
)

router = APIRouter(prefix="/api/v1/scrapers", tags=["scrapers"])

@router.get("")
def list_scrapers(db: Session = Depends(get_db)):
    scrapers = []
    for source, cls in SCRAPER_REGISTRY.items():
        s = cls()
        last_run = db.query(ScrapeRun).filter(
            ScrapeRun.source == source,
            ScrapeRun.status == "completed"
        ).order_by(ScrapeRun.completed_at.desc()).first()

        scrapers.append(ScraperInfo(
            name=s.name,
            source=source,
            status="ready",
            last_run=last_run.completed_at if last_run else None,
            reviews_collected=last_run.reviews_new if last_run else 0,
            runtime_seconds=last_run.runtime_seconds if last_run else None,
        ))
    return scrapers

@router.post("/run")
def run_scrapers(
    request: RunScrapersRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create scrape run record
    run = ScrapeRun(
        source=",".join(request.sources),
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(execute_scrapers, run.id, request.sources, db)
    return {"run_id": run.id, "status": "started"}

@router.get("/status")
def get_status():
    return ScraperStatus(
        run_id=current_run["run_id"] or 0,
        status=current_run["status"],
        sources=current_run["sources"],
        progress_current=current_run["progress_current"],
        progress_total=current_run["progress_total"],
        current_source=current_run["current_source"],
        current_message=current_run["current_message"],
        reviews_collected=current_run["reviews_collected"],
    )

@router.get("/logs")
def get_logs():
    return {"logs": current_run.get("logs", [])}
```

**Register router in `main.py`:**
```python
from routers import scrapers
app.include_router(scrapers.router)
```

**Test:**
```bash
# Start server
uvicorn main:app --reload --port 8000

# List scrapers
curl http://localhost:8000/api/v1/scrapers

# Run reddit scraper
curl -X POST http://localhost:8000/api/v1/scrapers/run \
  -H "Content-Type: application/json" \
  -d '{"sources": ["reddit"]}'

# Check status
curl http://localhost:8000/api/v1/scrapers/status
```

---

### Step 2.6 — Cleaning Service Integration

**Create `backend/services/cleaning_service.py`:**

Wraps the text cleaning logic from `4_data_cleaner.py`. Called after scraping completes to populate `text_clean`, `sentiment`, `quality_score`, and `relevance` columns.

```python
from sqlalchemy.orm import Session
from models import Review
# Import cleaning functions from the original script
from scrapers.scripts.data_cleaner import (
    clean_single_record, detect_language, classify_relevance, compute_quality_score
)

def clean_reviews(db: Session, scrape_run_id: int):
    """Clean all reviews from a scrape run."""
    reviews = db.query(Review).filter(
        Review.scrape_run_id == scrape_run_id,
        Review.text_clean.is_(None)
    ).all()

    for review in reviews:
        review.text_clean = clean_single_record(review.text_original)
        review.language = detect_language(review.text_clean)
        review.relevance = classify_relevance(review.text_clean)
        review.quality_score = compute_quality_score({"text_clean": review.text_clean})

    db.commit()
    return len(reviews)
```

---

## Phase 3: Reviews API

### Step 3.1 🔑 — Reviews Router

**Create `backend/routers/reviews.py`:**
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
from typing import Optional

from database import get_db
from models import Review
from schemas import ReviewsListResponse, ReviewResponse

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

@router.get("", response_model=ReviewsListResponse)
def list_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    query = db.query(Review)

    # Apply filters
    if source:
        query = query.filter(Review.source == source)
    if sentiment:
        query = query.filter(Review.sentiment == sentiment)
    if rating_min is not None:
        query = query.filter(Review.rating >= rating_min)
    if rating_max is not None:
        query = query.filter(Review.rating <= rating_max)
    if date_from:
        query = query.filter(Review.date >= date_from)
    if date_to:
        query = query.filter(Review.date <= date_to)
    if search:
        query = query.filter(
            or_(
                Review.text_clean.ilike(f"%{search}%"),
                Review.title.ilike(f"%{search}%"),
            )
        )

    # Count total
    total = query.count()

    # Sort
    sort_col = getattr(Review, sort_by, Review.date)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Paginate
    reviews = query.offset((page - 1) * per_page).limit(per_page).all()

    return ReviewsListResponse(
        reviews=[ReviewResponse.model_validate(r.__dict__) for r in reviews],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )

@router.get("/stats")
def review_stats(db: Session = Depends(get_db)):
    total = db.query(Review).count()
    sources = db.query(Review.source, func.count(Review.id)).group_by(Review.source).all()
    sentiments = db.query(Review.sentiment, func.count(Review.id)).group_by(Review.sentiment).all()

    return {
        "total": total,
        "by_source": {s: c for s, c in sources},
        "by_sentiment": {s: c for s, c in sentiments if s},
    }
```

**Register in `main.py`:**
```python
from routers import reviews
app.include_router(reviews.router)
```

**Test:**
```bash
curl "http://localhost:8000/api/v1/reviews?page=1&per_page=5"
curl "http://localhost:8000/api/v1/reviews?search=shuffle&source=reddit"
curl "http://localhost:8000/api/v1/reviews/stats"
```

---

## Phase 4: Frontend Foundation

### Step 4.1 🔑 — Initialize Next.js Project

```bash
cd spotify-voc-platform
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false
cd frontend
```

### Step 4.2 🔑 — Install Dependencies

```bash
npm install @tanstack/react-query axios recharts lucide-react
npm install class-variance-authority clsx tailwind-merge
npx shadcn@latest init
```

Choose: New York style, Zinc color, CSS variables = yes.

### Step 4.3 🔑 — Install shadcn/ui Components

```bash
npx shadcn@latest add button card table input select badge
npx shadcn@latest add dialog sheet toast skeleton tabs
npx shadcn@latest add checkbox progress separator dropdown-menu
```

### Step 4.4 🔑 — Setup API Client

**Create `frontend/lib/api.ts`:**
```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

export default api;
```

### Step 4.5 🔑 — Setup React Query Provider

**Create `frontend/lib/providers.tsx`:**
```typescript
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, refetchOnWindowFocus: false },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

**Update `app/layout.tsx`** to wrap children with `<Providers>`.

### Step 4.6 🔑 — Create TypeScript Types

**Create `frontend/types/index.ts`:**
```typescript
export interface ScraperInfo {
  name: string;
  source: string;
  status: "ready" | "running" | "error";
  last_run: string | null;
  reviews_collected: number;
  runtime_seconds: number | null;
}

export interface ScraperStatus {
  run_id: number;
  status: "idle" | "running" | "completed" | "failed";
  sources: string[];
  progress_current: number;
  progress_total: number;
  current_source: string | null;
  current_message: string | null;
  reviews_collected: number;
}

export interface Review {
  id: string;
  source: string;
  text_clean: string | null;
  title: string | null;
  author: string | null;
  rating: number | null;
  sentiment: string | null;
  date: string | null;
  url: string | null;
  quality_score: number | null;
}

export interface ReviewsResponse {
  reviews: Review[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DashboardStats {
  total_reviews: number;
  reviews_today: number;
  sources_connected: number;
  total_sources: number;
  last_scrape: string | null;
  last_insight_run: string | null;
}

export interface Insight {
  id: number;
  workflow: string;
  title: string | null;
  content: Record<string, unknown>;
  review_count: number | null;
  ai_model: string | null;
  created_at: string;
}

export interface Report {
  id: number;
  title: string;
  description: string | null;
  workflows: string[];
  sources: string[];
  review_count: number | null;
  created_at: string;
}
```

**Test:** `npm run build` completes without TypeScript errors.

---

### Step 4.7 🔑 — Create Layout with Sidebar

**Create `frontend/components/shared/sidebar.tsx`:**

A vertical sidebar with nav links: Dashboard, Scrapers, Reviews, Insights, Reports, Settings.
Use `lucide-react` icons. Highlight active route.

**Create `frontend/app/layout.tsx`:**

Root layout with:
- Dark mode support (class-based toggling)
- Sidebar on the left (w-64)
- Main content area with padding

**Test:** `npm run dev` → Page renders with sidebar navigation.

---

## Phase 5: Frontend Pages

### Step 5.1 🔑 — Dashboard Page

**Create `frontend/app/page.tsx`:**
- 4 stat cards at top (Total Reviews, Today, Sources, Last Scrape)
- 2x2 chart grid (Review Trend, Source Distribution, Sentiment, Recent Activity)
- Fetch data from `GET /api/v1/dashboard/stats`

**Backend:** Create `backend/routers/dashboard.py` with:
```python
@router.get("/api/v1/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Review).count()
    today = db.query(Review).filter(
        func.date(Review.created_at) == func.current_date()
    ).count()
    sources = db.query(Review.source).distinct().count()
    last_run = db.query(ScrapeRun).order_by(ScrapeRun.completed_at.desc()).first()
    # ...
```

**Test:** Dashboard shows real numbers after running scrapers.

---

### Step 5.2 🔑 — Scrapers Page

**Create `frontend/app/scrapers/page.tsx`:**
- Fetch scraper list: `GET /api/v1/scrapers`
- Render ScraperCard for each
- Checkboxes for selection
- "Run Selected" button → `POST /api/v1/scrapers/run`
- Progress panel (polls `GET /api/v1/scrapers/status` every 2s while running)
- Live logs panel (polls `GET /api/v1/scrapers/logs`)

**Components:**
- `scraper-card.tsx` — Card with name, status badge, last run, reviews count
- `scraper-progress.tsx` — Progress bar + current source + ETA
- `live-logs.tsx` — Scrollable monospace log viewer

**Hook: `frontend/hooks/use-scraper-status.ts`:**
```typescript
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { ScraperStatus } from "@/types";

export function useScraperStatus(enabled: boolean) {
  return useQuery<ScraperStatus>({
    queryKey: ["scraper-status"],
    queryFn: () => api.get("/scrapers/status").then(r => r.data),
    refetchInterval: enabled ? 2000 : false,
  });
}
```

**Test:**
1. Page loads with all scraper cards
2. Select Reddit + Play Store → Click Run
3. Progress bar animates
4. Logs scroll with live updates
5. Toast on completion

---

### Step 5.3 🔑 — Reviews Page

**Create `frontend/app/reviews/page.tsx`:**
- Search input (debounced)
- Filter row: Source dropdown, Sentiment dropdown, Rating range, Date range
- Table with columns: Source, Rating, Date, Review (truncated), Sentiment badge
- Pagination controls at bottom

**Components:**
- `review-table.tsx` — Data table with shadcn Table
- `review-filters.tsx` — Filter bar

**Test:**
1. Table loads with paginated reviews
2. Search "algorithm" filters in real-time
3. Source filter works
4. Pagination navigates correctly
5. Mobile layout stacks filters

---

### Step 5.4 🔑 — Insights Page

**Create `frontend/app/insights/page.tsx`:**
- Source selector (checkboxes)
- Date range picker
- Workflow checkboxes (all 12 workflows)
- "Generate Insights" button
- Progress section (polls while generating)
- Results section: collapsible cards per workflow
- "Save as Report" button

**Backend: `backend/routers/insights.py`:**
```python
@router.post("/api/v1/insights/generate")
def generate_insights(request: GenerateInsightsRequest, background_tasks, db):
    # Creates a report, launches background task
    # Task queries reviews, chunks them, sends to Gemini/Grok per workflow
    pass

@router.get("/api/v1/insights/status")
def insight_status():
    # Returns current generation progress
    pass

@router.get("/api/v1/insights")
def list_insights(db):
    # Returns past insights
    pass
```

**Backend: `backend/ai/workflows.py`:**
```python
WORKFLOWS = {
    "executive_summary": {
        "name": "Executive Summary",
        "description": "High-level overview of all feedback",
        "prompt_template": "...",
    },
    "pain_points": {
        "name": "Pain Points",
        "description": "Top user frustrations ranked by severity",
        "prompt_template": "...",
    },
    "feature_requests": {
        "name": "Feature Requests",
        "description": "Most requested features by frequency",
        "prompt_template": "...",
    },
    "positive_feedback": { ... },
    "negative_feedback": { ... },
    "sentiment_analysis": { ... },
    "competitor_mentions": { ... },
    "jobs_to_be_done": { ... },
    "user_personas": { ... },
    "theme_clustering": { ... },
    "emerging_trends": { ... },
    "product_recommendations": { ... },
}
```

**Backend: `backend/ai/gemini_client.py`:**
```python
import google.generativeai as genai
from config import settings

def generate(prompt: str, model: str = "gemini-1.5-flash") -> dict:
    genai.configure(api_key=settings.gemini_api_key)
    m = genai.GenerativeModel(model)
    response = m.generate_content(prompt)
    return parse_json_response(response.text)
```

**Test:**
1. Select sources + date range + 3 workflows
2. Click Generate → progress shows
3. Each workflow result appears as collapsible card
4. Content is structured JSON rendered nicely
5. Save as Report works

---

### Step 5.5 🔑 — Reports Page

**Create `frontend/app/reports/page.tsx`:**
- List of reports as cards (title, date, workflow count, source count)
- Click to expand → shows all insight cards
- Delete button with confirmation dialog
- Export as JSON button

**Backend: `backend/routers/reports.py`:**
```python
@router.get("/api/v1/reports")
def list_reports(db): ...

@router.get("/api/v1/reports/{report_id}")
def get_report(report_id: int, db):
    # Return report + all linked insights
    ...

@router.delete("/api/v1/reports/{report_id}")
def delete_report(report_id: int, db): ...

@router.get("/api/v1/reports/{report_id}/export")
def export_report(report_id: int, db):
    # Return JSON file download
    ...
```

**Test:**
1. Reports page lists all saved reports
2. Click report → insights expand
3. Delete shows confirmation → removes report
4. Export downloads JSON file

---

### Step 5.6 — Settings Page

**Create `frontend/app/settings/page.tsx`:**
- Gemini API Key input (masked, with show/hide toggle)
- Grok API Key input (masked)
- Database connection status indicator
- Save button

**Backend: `backend/routers/settings.py`:**
```python
@router.get("/api/v1/settings")
def get_settings(db):
    # Return keys masked: "sk-...abc"
    ...

@router.put("/api/v1/settings")
def update_settings(data: dict, db):
    # Upsert into settings table
    ...
```

**Test:**
1. Settings page loads with current values (masked)
2. Update Gemini key → Save → toast confirmation
3. Backend stores encrypted/plain in DB

---

## Phase 6: Polish & Production Readiness

### Step 6.1 💡 — Loading States & Skeletons

Add to every page:
- Skeleton loaders while data fetches
- Empty states when no data ("No reviews yet. Run a scraper to get started.")
- Error states with retry buttons

### Step 6.2 💡 — Toast Notifications

Add toast for:
- Scraper started / completed / failed
- Insights generated
- Report saved / deleted
- Settings saved
- API errors

### Step 6.3 💡 — Dark Mode

- Add toggle in header (sun/moon icon)
- Persist preference in localStorage
- All components respect `dark:` classes

### Step 6.4 💡 — Responsive Design

- Sidebar collapses to hamburger on mobile
- Tables scroll horizontally on small screens
- Cards stack vertically
- Charts resize

### Step 6.5 💡 — Charts (Dashboard)

Using Recharts:
- **Review Trend:** `LineChart` with reviews per day over last 30 days
- **Source Distribution:** `PieChart` showing % per source
- **Sentiment Distribution:** `BarChart` with positive/neutral/negative
- **Recent Activity:** Simple timeline list (not a chart)

---

## Phase 7: Deployment

### Step 7.1 🔑 — Prepare Backend for Railway

**Create `backend/Procfile`:**
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Create `backend/runtime.txt`:**
```
python-3.11
```

**Update `backend/config.py`** to read `DATABASE_URL` from Railway's auto-injected env var.

**Railway setup:**
1. Create new project on Railway
2. Add PostgreSQL plugin → auto-provisions DB
3. Connect GitHub repo (or deploy from CLI)
4. Set environment variables: `GEMINI_API_KEY`, `GROK_API_KEY`
5. Railway auto-detects Python + Procfile

### Step 7.2 🔑 — Prepare Frontend for Vercel

**Create `frontend/.env.production`:**
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
```

**Vercel setup:**
1. Connect GitHub repo
2. Set root directory: `frontend`
3. Set environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

### Step 7.3 — Run Alembic Migrations on Railway

```bash
# Connect to Railway shell
railway run alembic upgrade head
```

### Step 7.4 — End-to-End Production Test

1. Open Vercel URL
2. Go to Settings → Enter Gemini API key
3. Go to Scrapers → Run Reddit
4. Verify reviews appear in Reviews page
5. Go to Insights → Generate Executive Summary
6. Verify report saved in Reports page
7. Dashboard reflects real data

---

## Quick Reference: File Creation Order

```
Phase 1 (Backend Foundation):
  backend/config.py
  backend/database.py
  backend/models.py
  backend/schemas.py
  backend/main.py
  backend/alembic/ (init + first migration)

Phase 2 (Scrapers):
  backend/scrapers/__init__.py
  backend/scrapers/base.py
  backend/scrapers/scripts/ (copy existing scripts)
  backend/scrapers/reddit_scraper.py
  backend/scrapers/appstore_scraper.py
  backend/scrapers/playstore_scraper.py
  backend/scrapers/community_scraper.py
  backend/scrapers/social_scraper.py
  backend/services/scraper_service.py
  backend/services/cleaning_service.py
  backend/routers/scrapers.py

Phase 3 (Reviews):
  backend/routers/reviews.py

Phase 4 (Frontend Foundation):
  frontend/ (Next.js init)
  frontend/lib/api.ts
  frontend/lib/providers.tsx
  frontend/types/index.ts
  frontend/components/shared/sidebar.tsx
  frontend/app/layout.tsx

Phase 5 (Frontend Pages):
  frontend/app/page.tsx (dashboard)
  frontend/app/scrapers/page.tsx
  frontend/app/reviews/page.tsx
  frontend/app/insights/page.tsx
  frontend/app/reports/page.tsx
  frontend/app/settings/page.tsx
  frontend/components/dashboard/*
  frontend/components/scrapers/*
  frontend/components/reviews/*
  frontend/components/insights/*
  frontend/components/reports/*
  backend/routers/dashboard.py
  backend/routers/insights.py
  backend/routers/reports.py
  backend/routers/settings.py
  backend/ai/gemini_client.py
  backend/ai/grok_client.py
  backend/ai/workflows.py
  backend/services/insight_service.py

Phase 6 (Polish):
  Loading skeletons in each page
  Toast integration
  Dark mode toggle
  Responsive adjustments
  Error boundaries

Phase 7 (Deploy):
  backend/Procfile
  backend/runtime.txt
  frontend/.env.production
  Railway + Vercel configuration
```

---

## Estimated Timeline

| Phase | Effort | Cumulative |
|-------|--------|-----------|
| Phase 1: Backend Foundation | 3-4 hours | 4 hours |
| Phase 2: Scraper Integration | 4-5 hours | 9 hours |
| Phase 3: Reviews API | 1-2 hours | 11 hours |
| Phase 4: Frontend Foundation | 2-3 hours | 14 hours |
| Phase 5: Frontend Pages | 8-10 hours | 24 hours |
| Phase 6: Polish | 3-4 hours | 28 hours |
| Phase 7: Deployment | 2-3 hours | 31 hours |

**Total: ~30-35 hours of focused development.**

---

## Pre-requisites Checklist

Before starting:
- [ ] PostgreSQL installed locally (or use Railway for dev too)
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Gemini API key from https://aistudio.google.com/app/apikey
- [ ] Railway account created
- [ ] Vercel account created
- [ ] GitHub repo created for the project

---

## Phase 8: Bonus Enhancement — Reports Page Redesign 🎨

> **Goal:** Transform the Reports page from a raw JSON viewer into a premium AI-powered Product Insights Dashboard that a PM would confidently present to leadership.

### Design Philosophy

The redesigned Reports page draws inspiration from Linear, Notion AI, Vercel Dashboard, and Perplexity.
Every insight gets its own dedicated visual component. No raw JSON is ever shown to the user.
The page reads like a long-form analytics dashboard — scannable in under 60 seconds.

---

### Step 8.1 💡 — Folder Structure & Module Setup

**Create the Reports module:**
```
frontend/components/reports/
├── ReportHeader.tsx
├── ExecutiveSummaryCard.tsx
├── MetricCard.tsx
├── SentimentSection.tsx
├── PainPointCard.tsx
├── FeatureRequestCard.tsx
├── TrendCard.tsx
├── ThemeClusterCard.tsx
├── JobToBeDoneCard.tsx
├── CompetitorCard.tsx
├── PersonaCard.tsx
├── RecommendationCard.tsx
├── ReviewCard.tsx
├── ChartCard.tsx
├── SectionHeader.tsx
├── ConfidenceBadge.tsx
├── SeverityBadge.tsx
├── PriorityBadge.tsx
├── SourceBadge.tsx
├── ProgressIndicator.tsx
├── EmptyState.tsx
├── SkeletonReport.tsx
├── ReportAppendix.tsx
├── ReportListView.tsx
├── rendering-layer/
│   ├── index.ts              # Component registry
│   ├── registry.ts           # Maps workflow types → renderer components
│   └── FallbackRenderer.tsx  # Generic JSON display for unrecognized types
└── types.ts                  # Report-specific TypeScript interfaces
```

**Test:** All files created, imports resolve, `npm run build` passes.

---

### Step 8.2 💡 — TypeScript Types for Report Data

**Create `frontend/components/reports/types.ts`:**

Define typed interfaces matching the backend AI workflow JSON responses:

```typescript
export interface ReportDetail {
  id: number;
  title: string;
  description: string | null;
  workflows: string[];
  sources: string[];
  review_count: number | null;
  date_range_start: string | null;
  date_range_end: string | null;
  status: string;
  created_at: string;
  insights: InsightDetail[];
}

export interface InsightDetail {
  id: number;
  workflow: string;
  title: string | null;
  content: Record<string, unknown>;
  review_count: number | null;
  ai_model: string | null;
  created_at: string;
}

export interface ExecutiveSummaryContent {
  bottom_line: string;
  key_findings: KeyFinding[];
  key_metric: string;
  overall_sentiment: string;
  confidence_score: number;
}

export interface KeyFinding {
  theme: string;
  severity: number;
  frequency: string;
  description: string;
}

export interface PainPoint {
  title: string;
  severity: number;
  frequency: number;
  category: string;
  explanation: string;
  representative_quotes: string[];
}

export interface FeatureRequest {
  title: string;
  description: string;
  request_count: number;
  complexity: "Low" | "Medium" | "High";
  business_value: "Low" | "Medium" | "High";
  user_segments: string[];
  representative_quote: string;
}

export interface EmergingTrend {
  name: string;
  description: string;
  growth_signal: string;
  potential_impact: "High" | "Medium" | "Low";
  time_horizon: string;
  confidence: number;
}

export interface ThemeCluster {
  theme: string;
  review_count: number;
  sentiment_mix: string;
  key_insight: string;
  sub_themes: string[];
  representative_quotes: string[];
}

export interface JobToBeDone {
  situation: string;
  motivation: string;
  expected_outcome: string;
  satisfaction: "Satisfied" | "Partially Satisfied" | "Unsatisfied";
  barriers: string[];
  workarounds: string[];
}

export interface CompetitorMention {
  competitor: string;
  mention_count: number;
  sentiment: "Positive" | "Neutral" | "Negative";
  context: string;
  perceived_advantage: string;
  representative_quotes: string[];
}

export interface UserPersona {
  name: string;
  description: string;
  listening_behavior: string;
  primary_need: string;
  main_frustration: string;
  discovery_approach: string;
  churn_risk: "High" | "Medium" | "Low";
  estimated_size: string;
  representative_quote: string;
}

export interface ProductRecommendation {
  title: string;
  description: string;
  rationale: string;
  impact_score: number;
  effort_score: number;
  confidence_score: number;
  ice_score: number;
  affected_personas: string[];
  success_metric: string;
}

export interface SentimentAnalysis {
  overall_sentiment: {
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
  };
  positive_drivers: string[];
  negative_drivers: string[];
  notable_shifts: string;
  by_topic: Array<{
    topic: string;
    positive: number;
    neutral: number;
    negative: number;
  }>;
}
```

**Test:** `npm run build` passes with no type errors.

---

### Step 8.3 💡 — Rendering Layer (Component Registry)

**Create `frontend/components/reports/rendering-layer/registry.ts`:**

```typescript
import { ComponentType } from "react";

// Registry maps workflow type → renderer component
const RENDERER_REGISTRY: Record<string, ComponentType<{ content: any }>> = {};

export function registerRenderer(workflow: string, component: ComponentType<{ content: any }>) {
  RENDERER_REGISTRY[workflow] = component;
}

export function getRenderer(workflow: string): ComponentType<{ content: any }> | null {
  return RENDERER_REGISTRY[workflow] || null;
}

export function getAllRegisteredWorkflows(): string[] {
  return Object.keys(RENDERER_REGISTRY);
}
```

**Create `frontend/components/reports/rendering-layer/index.ts`:**

```typescript
import { getRenderer } from "./registry";
import FallbackRenderer from "./FallbackRenderer";

export function resolveRenderer(workflow: string) {
  return getRenderer(workflow) || FallbackRenderer;
}

// Auto-register all renderers on import
import "./registrations";
```

**Create `frontend/components/reports/rendering-layer/registrations.ts`:**

```typescript
import { registerRenderer } from "./registry";
import ExecutiveSummaryCard from "../ExecutiveSummaryCard";
import SentimentSection from "../SentimentSection";
import PainPointsSection from "../PainPointsSection";
import FeatureRequestsSection from "../FeatureRequestsSection";
import EmergingTrendsSection from "../EmergingTrendsSection";
import ThemeClustersSection from "../ThemeClustersSection";
import JobsToBeDoneSection from "../JobsToBeDoneSection";
import CompetitorMentionsSection from "../CompetitorMentionsSection";
import UserPersonasSection from "../UserPersonasSection";
import ProductRecommendationsSection from "../ProductRecommendationsSection";

registerRenderer("executive_summary", ExecutiveSummaryCard);
registerRenderer("sentiment_analysis", SentimentSection);
registerRenderer("pain_points", PainPointsSection);
registerRenderer("feature_requests", FeatureRequestsSection);
registerRenderer("emerging_trends", EmergingTrendsSection);
registerRenderer("theme_clustering", ThemeClustersSection);
registerRenderer("jobs_to_be_done", JobsToBeDoneSection);
registerRenderer("competitor_mentions", CompetitorMentionsSection);
registerRenderer("user_personas", UserPersonasSection);
registerRenderer("product_recommendations", ProductRecommendationsSection);
```

**Pattern:** To add a new insight type, create a renderer component + add one `registerRenderer()` call.

**Test:** Import resolveRenderer for known and unknown workflows, verify correct component is returned.

---

### Step 8.4 💡 — Reusable Badge & Indicator Components

**Build these atomic components:**

| Component | Props | Behavior |
|-----------|-------|----------|
| `SeverityBadge` | `level: 1-5` | Red (4-5), Amber (2-3), Green (1). Labels: Critical, High, Medium, Low |
| `ConfidenceBadge` | `score: 0-100` | Green (80-100), Amber (50-79), Red (0-49). Shows percentage |
| `PriorityBadge` | `priority: "High" \| "Medium" \| "Low"` | Color-coded pill badge |
| `SourceBadge` | `source: string` | Icon + label for Reddit, App Store, Play Store, etc. |
| `ProgressIndicator` | `value: number, max: number` | Horizontal progress bar with numeric label |
| `SectionHeader` | `title, icon, description?` | Lucide icon + heading + optional subtitle |

**Design:** Use `class-variance-authority` (cva) for variant-driven styling. All badges use rounded-full pill shape with appropriate color backgrounds.

**Test:** Render each badge with various props. Visual inspection confirms correct colors and labels.

---

### Step 8.5 💡 — MetricCard & Key Metrics Row

**Create `MetricCard.tsx`:**
- Compact card with: icon, label, value, optional trend indicator
- Values > 9,999 display abbreviated (10.0K, 1.2M)
- Missing values show "—"
- Responsive: horizontal row on desktop, vertical stack on mobile

**Create `KeyMetricsRow.tsx`:**
- Renders exactly 8 MetricCards in a responsive grid
- Sources values from report metadata + aggregated insight data
- Grid: `grid-cols-2 md:grid-cols-4 lg:grid-cols-8`

**Test:** Metrics display correctly with real report data. Mobile layout stacks to 2 columns.

---

### Step 8.6 💡 — Executive Summary Card

**Create `ExecutiveSummaryCard.tsx`:**
- Full-width highlighted card (gradient or accent border)
- Displays: bottom-line summary, up to 5 key findings, key metric, sentiment indicator, confidence badge
- Key findings render as a mini-list with severity and frequency indicators
- Sentiment uses color-coded pill: green (Positive), amber (Mixed), red (Negative)
- Empty state if no executive summary present

**Test:** Card renders with sample executive summary JSON. Sentiment colors are correct.

---

### Step 8.7 💡 — Pain Points Section

**Create `PainPointsSection.tsx`:**
- Renders SectionHeader with AlertTriangle icon
- Maps pain points array → individual PainPointCard components
- Cards sorted by (severity × frequency) descending
- Each card shows: title, SeverityBadge, frequency count, category tag, AI explanation, callout quote
- Quote rendered in a bordered/highlighted callout block

**Test:** Pain points render sorted correctly. Severity badges show proper colors.

---

### Step 8.8 💡 — Feature Requests Section

**Create `FeatureRequestsSection.tsx`:**
- SectionHeader with Lightbulb icon
- Cards sorted by priority (High → Medium → Low), then by request count
- Priority logic: High = count ≥ 10 AND value = High; Low = count < 5 OR value = Low; else Medium
- Each card: title, description, request count, complexity badge, business value badge, user segments, callout quote

**Test:** Priority badges calculated correctly. Sort order matches specification.

---

### Step 8.9 💡 — Sentiment Analysis Section (Charts)

**Create `SentimentSection.tsx`:**
- SectionHeader with Heart icon
- Pie chart (Recharts PieChart) showing positive/neutral/negative distribution
- Bar chart showing sentiment by topic (up to 10 topics)
- Three Insight_Cards: Positive Drivers, Negative Drivers, Notable Shifts
- Charts responsive — resize on mobile, min height 200px

**Dependencies:** Uses Recharts (already installed in Phase 4.2).

**Test:** Charts render with sample data. Mobile layout stacks charts vertically.

---

### Step 8.10 💡 — Emerging Trends, Theme Clusters, JTBD

**Create section components for:**
- `EmergingTrendsSection.tsx` — Trend cards with growth signal, impact badge, time horizon, confidence badge. Watch list items in muted style below.
- `ThemeClustersSection.tsx` — Theme cards with review count, sentiment indicator, sub-theme tag chips (max 8), expandable quotes (collapsed by default, max 3). Cross-cutting themes as a distinct chip group.
- `JobsToBeDoneSection.tsx` — Job cards with situation/motivation/outcome, satisfaction indicator (green/amber/red), barriers list, workarounds. Underserved jobs highlighted with distinct border.

**Test:** Each section renders correctly with sample data and empty states.

---

### Step 8.11 💡 — Competitor Mentions, User Personas, Recommendations

**Create:**
- `CompetitorMentionsSection.tsx` — Competitor cards ordered by mention count. Switching signals sub-section. Spotify advantages in green callout.
- `UserPersonasSection.tsx` — Full-width persona cards. Churn risk badge (red/amber/green). Estimated size label. Quote in distinct block. Omit missing optional fields gracefully.
- `ProductRecommendationsSection.tsx` — Recommendation cards with ICE scoring. Progress bars for impact/effort/confidence (1-10 scale). Sorted by ICE score descending. Quick Wins and Strategic Bets sub-sections with distinct left-border accents.

**Test:** ICE score calculation correct. Progress bars proportional. Sort order validated.

---

### Step 8.12 💡 — Representative Reviews & Appendix

**Create:**
- `ReviewCard.tsx` — Source badge, star rating (1-5), date, sentiment badge, review text (truncated at 300 chars with expand toggle), keyword highlights with background color.
- `RepresentativeReviewsSection.tsx` — Displays up to 10 review cards ordered by relevance.
- `ReportAppendix.tsx` — Last section. Smaller/muted text. Shows: AI prompt (truncated 500 chars + expand), model name, timestamp (ISO 8601), sources list, review count. Missing fields show "N/A" placeholder.

**Test:** Review cards truncate and expand correctly. Appendix is visually subordinate.

---

### Step 8.13 💡 — Report Header (Redesigned)

**Create `ReportHeader.tsx`:**
- Report title (large heading)
- Generation date (human-readable)
- Source badges (one per source)
- Total review count
- AI model name
- Generation time
- Export button → triggers JSON download (`report_{id}.json`)
- Regenerate button → re-runs insight generation with same params
- Error state hides action buttons

**Test:** Export downloads correctly named file. Regenerate triggers API call.

---

### Step 8.14 💡 — Loading & Empty States

**Create `SkeletonReport.tsx`:**
- Shimmer-animated skeleton that matches final layout shape
- Header skeleton + metrics row skeleton + 4-5 section skeletons
- Shimmer cycles every 1.5-2s
- On load complete: no cumulative layout shift
- 30s timeout → error state with retry button

**Create `EmptyState.tsx`:**
- Section-appropriate icon
- Message identifying which section has no data
- Actionable suggestion (e.g., "Generate insights to populate this section")
- Minimum 120px height
- Distinct from loading state visually

**Test:** Loading state animates. Empty state shows for missing sections. Error state shows retry.

---

### Step 8.15 💡 — Report List View (Redesigned)

**Update `frontend/app/reports/page.tsx`:**
- Card-based list (not table) of all reports, ordered by date descending
- Each card shows: title, creation date, source badges, review count, workflow count
- Click card → navigates to `/reports/[id]` detail view
- Delete with confirmation dialog
- Empty state when no reports exist

**Create `frontend/app/reports/[id]/page.tsx`:**
- Fetches full report + insights from `GET /api/v1/reports/{id}`
- Renders: ReportHeader → ExecutiveSummary → KeyMetrics → each insight section via rendering layer
- Sections rendered in defined order (not arbitrary JSON order)

**Test:** Navigation works. Full report renders all sections. Delete removes report.

---

### Step 8.16 💡 — Mobile Responsive Polish

**Responsive rules:**
- Below 768px: all grids → single column
- Charts maintain minimum 200px height, resize width to container
- Text minimum 14px, touch targets minimum 44×44px
- No horizontal overflow at any breakpoint (320px–1920px)
- Sidebar collapses on mobile (already in Phase 6)

**Test:** Manually verify at 375px, 768px, 1024px, 1440px viewports.

---

### Step 8.17 💡 — Visual Design & Accessibility

**Standards:**
- No data tables for insight display
- 24px spacing between major sections, 16px between cards within sections
- Color coding always paired with text labels/icons (no color-only meaning)
- Lucide icons on all section headers
- Typographic hierarchy: headings ≥20px semibold, sub-headings ≥16px, body ≥14px
- Dark mode compatibility for all report components

**Test:** Accessibility audit — verify color contrast ratios (WCAG AA), keyboard navigation, screen reader labels.

---

### Reports Redesign: Component Summary

| Component | Purpose |
|-----------|---------|
| `ReportHeader` | Title, metadata, export/regenerate actions |
| `ExecutiveSummaryCard` | Top-level findings at a glance |
| `KeyMetricsRow` | 8 numeric KPI cards |
| `SentimentSection` | Charts + driver cards |
| `PainPointCard` | Individual pain point with severity |
| `FeatureRequestCard` | Feature demand + priority |
| `TrendCard` | Emerging signal + confidence |
| `ThemeClusterCard` | Topic cluster + sub-themes |
| `JobToBeDoneCard` | JTBD with satisfaction |
| `CompetitorCard` | Competitive context |
| `PersonaCard` | Data-driven persona |
| `RecommendationCard` | Actionable recommendation + ICE |
| `ReviewCard` | Individual review with highlights |
| `ChartCard` | Recharts container |
| `SectionHeader` | Icon + title + description |
| `ConfidenceBadge` | AI confidence (0-100) |
| `SeverityBadge` | Severity (1-5) |
| `PriorityBadge` | Priority (H/M/L) |
| `SourceBadge` | Data source indicator |
| `ProgressIndicator` | Horizontal progress bar |
| `EmptyState` | No-data placeholder |
| `SkeletonReport` | Loading placeholder |
| `ReportAppendix` | Generation metadata |
| `ReportListView` | Report card list + navigation |

---

### Reports Redesign: Estimated Timeline

| Step | Effort | Cumulative |
|------|--------|-----------|
| 8.1 Folder Structure | 0.5 hours | 0.5 hours |
| 8.2 TypeScript Types | 1 hour | 1.5 hours |
| 8.3 Rendering Layer | 1.5 hours | 3 hours |
| 8.4 Badge Components | 1.5 hours | 4.5 hours |
| 8.5 MetricCard & Row | 1.5 hours | 6 hours |
| 8.6 Executive Summary | 1.5 hours | 7.5 hours |
| 8.7 Pain Points | 1.5 hours | 9 hours |
| 8.8 Feature Requests | 1.5 hours | 10.5 hours |
| 8.9 Sentiment Charts | 2 hours | 12.5 hours |
| 8.10 Trends/Themes/JTBD | 3 hours | 15.5 hours |
| 8.11 Competitors/Personas/Recs | 3 hours | 18.5 hours |
| 8.12 Reviews & Appendix | 1.5 hours | 20 hours |
| 8.13 Report Header | 1 hour | 21 hours |
| 8.14 Loading & Empty States | 1.5 hours | 22.5 hours |
| 8.15 Report List + Detail View | 2 hours | 24.5 hours |
| 8.16 Mobile Responsive | 1.5 hours | 26 hours |
| 8.17 Visual Polish & A11y | 2 hours | 28 hours |

**Total Phase 8: ~28 hours of focused development.**

---

### Reports Redesign: JSON → Component Mapping

```
Backend AI Response          →  Frontend Component
─────────────────────────────────────────────────────
executive_summary            →  ExecutiveSummaryCard
sentiment_analysis           →  SentimentSection (Charts + Cards)
pain_points                  →  PainPointsSection → PainPointCard[]
feature_requests             →  FeatureRequestsSection → FeatureRequestCard[]
emerging_trends              →  EmergingTrendsSection → TrendCard[]
theme_clustering             →  ThemeClustersSection → ThemeClusterCard[]
jobs_to_be_done              →  JobsToBeDoneSection → JobToBeDoneCard[]
competitor_mentions          →  CompetitorMentionsSection → CompetitorCard[]
user_personas                →  UserPersonasSection → PersonaCard[]
product_recommendations      →  ProductRecommendationsSection → RecommendationCard[]
(unrecognized workflow)      →  FallbackRenderer (formatted JSON)
```

---

### Reports Redesign: UX Success Criteria

The redesigned report answers these questions within seconds:

1. ✅ **What are users saying?** → Executive Summary + Sentiment Section
2. ✅ **What are the biggest problems?** → Pain Points (severity-sorted)
3. ✅ **What features are most requested?** → Feature Requests (priority-sorted)
4. ✅ **What trends are emerging?** → Emerging Trends with growth signals
5. ✅ **What should the product team prioritize?** → Recommendations with ICE scores
6. ✅ **What evidence supports these conclusions?** → Representative Reviews + quotes in every card

A Product Manager should be able to scan the full report in under 60 seconds and extract the key narrative.

---

### Updated Total Project Timeline

| Phase | Effort | Cumulative |
|-------|--------|-----------|
| Phase 1: Backend Foundation | 3-4 hours | 4 hours |
| Phase 2: Scraper Integration | 4-5 hours | 9 hours |
| Phase 3: Reviews API | 1-2 hours | 11 hours |
| Phase 4: Frontend Foundation | 2-3 hours | 14 hours |
| Phase 5: Frontend Pages | 8-10 hours | 24 hours |
| Phase 6: Polish | 3-4 hours | 28 hours |
| Phase 7: Deployment | 2-3 hours | 31 hours |
| **Phase 8: Reports Redesign** 🎨 | **26-28 hours** | **~59 hours** |

**Total with Bonus: ~55-60 hours of focused development.**
