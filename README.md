# Movie Box Office Forecaster

**[Live app](https://frontend-rho-ashy-79wbl21zmk.vercel.app)** · **[API health check](https://backend-production-185f1.up.railway.app/api/health)**

Look up any movie and see its real week-by-week box office trajectory. See a weekly forecast
for movies opening this box office week. Compare a film against its franchise or its release
year. See whether it was a bomb, a flop, or a financial success — and whether the model's own
predictions are any good, because I checked.

## What it does

- **Browse & search** — Netflix-style rows (trending / popular / top rated / coming soon), full search, live TMDB data
- **Week-by-week box office** — real weekend-by-weekend gross, scraped from Box Office Mojo, color-coded by week-over-week change (a steep or severe drop is a real signal — bad word-of-mouth, not just "normal decline")
- **Domestic / Worldwide toggle** — the site only has real *weekly* data for domestic (that's what Box Office Mojo publishes); worldwide is shown as an explicitly-labeled estimate, scaled from the real domestic curve by the film's actual gross ratio — not fabricated as if it were real data
- **This Week forecast** — opening-weekend predictions for movies releasing in the current Monday–Sunday box office week, refreshed daily
- **Profitability banner** — bomb / flop / financial success, using the industry rule of thumb that a film needs ~2.5x its budget worldwide to be profitable
- **Franchise & same-year comparisons** — cumulative gross curves overlaid and indexed by *week in release* (not calendar date), so films released years apart compare fairly
- **Critic scores** — Rotten Tomatoes, Metacritic, IMDb, via OMDb

## The interesting part: I backtested the prediction model, and it exposed real bugs

It would have been easy to ship the forecasting heuristic, screenshot a plausible-looking
number, and move on. Instead I built a leave-one-out backtest (`backend/app/ml/evaluate.py`)
that runs the exact prediction logic against every movie already in the database with both a
known budget and a real opening-weekend actual, excluding each movie from its own comp pool,
and compares predicted to actual.

**Current result: 43 eligible movies, 100% coverage, median absolute error 79%.**

That's not a good number, and I'd rather show it than hide it. Digging into *why* found two
real bugs that are now fixed, with regression tests:

1. **A director whose only real comp was a Netflix original's token theatrical run** predicted
   a Sandra Bullock/Nicole Kidman studio sequel's opening at ~$50K. The root cause: the
   original heuristic blended raw historical dollar figures across comps regardless of scale.
   Fixed by requiring *both* the target film's budget and a comp's budget to be known before
   using that comp at all — "same director" or "same genre" is not a guarantee of similar
   scale, and an unscaled comp is worse than no comp.
2. **A 50-minute LEGO Star Wars streaming special got predicted at $100M+.** It had slipped
   into the "This Week" discovery filter via a token theatrical qualifying run, had no budget
   on record, and the (now-removed) unscaled genre-average fallback blended in a real
   blockbuster sharing one of its five broad genre tags. Fixed with a runtime floor on
   discovery *and* by removing the unscaled fallback entirely.

I also had a real hypothesis for improving accuracy: pair each movie's real Rotten Tomatoes
score against its prediction error and see if quality explains the misses. I ran the
correlation — **0.140** across 42 movies. Essentially noise. Rather than force critic score
into the model as an unvalidated "quality multiplier" just because the data was sitting
right there, I shipped it as a standalone display feature and left the prediction model
alone. The actual pattern in the worst misses (limited/platform releases scored against
wide-release comps) points somewhere else, and that's next.

## Known limitations (stated plainly, not buried)

- **The prediction model is a heuristic baseline, not a trained model.** It's an average of
  historical comps scaled by budget ratio — see the backtest above for exactly how well
  that works today.
- **A film's own critic score usually isn't public until shortly before release** (review
  embargoes), so it can't feed most live pre-release forecasts even where it would help.
- **The database grows organically**, not from a comprehensive backfill — it only contains
  movies someone has actually looked up (plus their auto-backfilled director history). Same-
  year comparisons and comp pools are sparser for less-explored corners of the catalog.
- **Worldwide weekly data doesn't exist as a real feed** — Box Office Mojo only publishes
  clean weekly breakdowns for domestic; the "Worldwide (estimated)" toggle is a labeled
  approximation, not real international weekly data.
- **Box Office Mojo scraping** is done for this personal, non-commercial project with a
  low-frequency, identifying User-Agent; it would need a licensed data source to ever be
  anything else. (Letterboxd was considered for reviews and explicitly ruled out — its
  `robots.txt` blocks AI crawlers by name, including Claude's, and that felt like a real line
  rather than a gray area.)

## Tech stack

| | |
|---|---|
| **Frontend** | Next.js 16 (App Router, TypeScript), Tailwind, Recharts |
| **Backend** | FastAPI (Python), SQLAlchemy, Alembic |
| **Database** | PostgreSQL |
| **Data sources** | [TMDB API](https://www.themoviedb.org/documentation/api) (live metadata), Box Office Mojo (scraped weekly gross), [OMDb](https://www.omdbapi.com/) (critic scores) |
| **Testing** | pytest + ruff (backend), Vitest + ESLint + tsc (frontend) — 35 tests |
| **CI/CD** | GitHub Actions (lint/type/test on every push) · Vercel (frontend) · Railway (backend + Postgres) |

See [`docs/architecture.md`](docs/architecture.md) for the database schema, endpoint list, and
data-ingestion design in more depth.

## Local setup

### Prerequisites
- Node.js 20+, Python 3.11+
- PostgreSQL running locally (`brew install postgresql@16 && brew services start postgresql@16`)
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- A free [OMDb API key](https://www.omdbapi.com/apikey.aspx)

### Database
```bash
createdb box_office_forecaster
```

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in TMDB_API_KEY and OMDB_API_KEY
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

## Testing & CI

```bash
# backend
cd backend && source venv/bin/activate
ruff check app/ tests/
pytest -v

# frontend
cd frontend
npm run lint
npm run typecheck
npm run test
```

GitHub Actions (`.github/workflows/ci.yml`) runs all of the above on every push/PR to `main`.
It deliberately does **not** run a full `next build` — a couple of pages fetch live data
(TMDB, Box Office Mojo) at build time for static generation, which would make CI slow,
network-dependent, and require secrets for no real benefit: Vercel already runs a full
production build with real data on every push, so CI's job here is fast, hermetic
lint/type/unit-test coverage, not a redundant second full build.

## Repo layout

```
box-office-forecaster/
  frontend/   # Next.js app
  backend/    # FastAPI app, Alembic migrations, ETL/scraping, prediction model, backtest
  docs/       # architecture notes
```

## What's next

- Investigate the release-strategy mismatch (limited/platform releases vs. wide-release
  comps) that the backtest points to as the likely bigger driver of error than missing
  quality signal
- Second-weekend drop prediction, computed from the site's own scraped data by genre
- A "This Week" news/headline panel for movies currently in theaters
