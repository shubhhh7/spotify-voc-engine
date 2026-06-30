"""
Spotify VoC Intelligence Platform — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import dashboard, scrapers, reviews, insights, reports, settings

app = FastAPI(
    title="Spotify VoC Intelligence Platform",
    description="AI-powered review analysis and insight generation",
    version="1.0.0",
)

# CORS — allow frontend origins
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "")

cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if FRONTEND_URL:
    cors_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router)
app.include_router(scrapers.router)
app.include_router(reviews.router)
app.include_router(insights.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "name": "Spotify VoC Intelligence Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }
