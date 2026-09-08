# Movie Box Office Forecaster

Looks up any movie and charts its actual week-by-week box office trajectory, then predicts opening weekend and final domestic/worldwide gross for movies that haven't released yet — using director/cast historical performance, genre, seasonality, budget, and live social-buzz signals from TMDB.

## Stack

- **Frontend**: Next.js (App Router, TypeScript, Tailwind) — `frontend/`
- **Backend**: FastAPI (Python) — `backend/`
- **Database**: PostgreSQL, managed with Alembic migrations
- **Data sources**: [TMDB API](https://www.themoviedb.org/documentation/api) for live movie metadata; a static historical dataset seeds training data; a scheduled Box Office Mojo scraper backfills post-release actuals for scoring predictions
- **ML**: ensemble regressors (opening weekend / domestic / worldwide gross) plus a movie-specific decay-curve model for the week-by-week trajectory

## Project status

Early scaffolding stage. See `docs/` for architecture notes. Current milestone: local dev environment running end-to-end (Next.js ↔ FastAPI ↔ Postgres). Feature work (TMDB ingestion, charts, ML pipeline) comes next.

## Local setup

### Prerequisites
- Node.js 20+, Python 3.11+
- PostgreSQL running locally (`brew install postgresql@16 && brew services start postgresql@16`)
- A free [TMDB API key](https://www.themoviedb.org/settings/api) (needed once we start pulling movie data)

### Database
```bash
createdb box_office_forecaster
```

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in TMDB_API_KEY when you have one
alembic upgrade head
uvicorn app.main:app --reload
```
API runs at http://localhost:8000 — check http://localhost:8000/api/health.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
App runs at http://localhost:3000.

## Repo layout

```
box-office-forecaster/
  frontend/   # Next.js app
  backend/    # FastAPI app, Alembic migrations, ETL scripts, ML pipeline
  docs/       # architecture notes
```
