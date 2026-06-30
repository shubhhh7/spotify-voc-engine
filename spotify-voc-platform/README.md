# Spotify VoC Intelligence Platform

AI-powered review analysis and insight generation for Product Managers.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 15+

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up .env (edit with your values)
cp .env .env.local

# Create database
createdb spotify_voc

# Create tables
python create_tables.py

# Start server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

App available at: http://localhost:3000

## Project Structure

```
spotify-voc-platform/
├── backend/           FastAPI + Python
│   ├── main.py        App entry point
│   ├── models.py      SQLAlchemy ORM models
│   ├── schemas.py     Pydantic request/response models
│   ├── routers/       API route handlers
│   ├── services/      Business logic layer
│   ├── scrapers/      Scraper adapters + original scripts
│   └── ai/            Gemini/Grok integration
│
├── frontend/          Next.js + TypeScript
│   ├── app/           Pages (App Router)
│   ├── components/    React components
│   ├── lib/           Utilities, API client
│   └── types/         TypeScript interfaces
│
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/v1/dashboard/stats | Dashboard statistics |
| GET | /api/v1/scrapers | List all scrapers |
| POST | /api/v1/scrapers/run | Run selected scrapers |
| GET | /api/v1/scrapers/status | Current run progress |
| GET | /api/v1/reviews | Paginated reviews |
| POST | /api/v1/insights/generate | Generate AI insights |
| GET | /api/v1/reports | List saved reports |
| GET | /api/v1/settings | Get settings |
| PUT | /api/v1/settings | Update settings |
