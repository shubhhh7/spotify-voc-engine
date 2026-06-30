"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# --- Scrapers ---

class ScraperInfo(BaseModel):
    name: str
    source: str
    status: str  # ready, running, error
    last_run: Optional[datetime] = None
    reviews_collected: int = 0
    runtime_seconds: Optional[float] = None


class RunScrapersRequest(BaseModel):
    sources: list[str]


class ScraperStatus(BaseModel):
    run_id: int = 0
    status: str = "idle"  # idle, running, completed, failed
    sources: list[str] = []
    progress_current: int = 0
    progress_total: int = 0
    current_source: Optional[str] = None
    current_message: Optional[str] = None
    reviews_collected: int = 0


# --- Reviews ---

class ReviewResponse(BaseModel):
    id: str
    source: str
    text_clean: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    rating: Optional[float] = None
    sentiment: Optional[str] = None
    date: Optional[datetime] = None
    url: Optional[str] = None
    quality_score: Optional[int] = None

    class Config:
        from_attributes = True


class ReviewsListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# --- Insights ---

class GenerateInsightsRequest(BaseModel):
    workflows: list[str]
    sources: list[str] = []
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class InsightResponse(BaseModel):
    id: int
    workflow: str
    title: Optional[str] = None
    content: dict
    review_count: Optional[int] = None
    ai_model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Reports ---

class ReportResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    workflows: list[str] = []
    sources: list[str] = []
    review_count: Optional[int] = None
    status: str = "completed"
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_reviews: int = 0
    reviews_today: int = 0
    sources_connected: int = 0
    total_sources: int = 5
    last_scrape: Optional[datetime] = None
    last_insight_run: Optional[datetime] = None


# --- Settings ---

class SettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None
