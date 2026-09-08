# Architecture Notes

See the root [`README.md`](../README.md) for the project overview, the backtest findings, and
local setup. This doc is the deeper technical reference: schema, endpoints, and how data flows
into the system.

## Data flow: ingest-on-lookup, not a batch job

There is no scheduled scraper or bulk backfill. Data enters the database only when something
triggers a lookup:

- A user searches for or opens a movie → its TMDB metadata is upserted, and (for released
  films) its Box Office Mojo weekly gross, lifetime gross, and OMDb critic scores are fetched
  and cached on first request.
- A movie needs a prediction → its director's TMDB credits are fetched, and up to 5 of their
  most recent prior films get the same ingestion treatment, so there's real comp data to
  scale against.
- A movie is part of a franchise comparison → the whole TMDB collection is proactively
  ingested (franchises are small and bounded, unlike "every movie from this year").

Almost everything is **cached once and never re-fetched** (weekly gross, lifetime gross,
critic scores) — the underlying facts don't change. The one exception is **predictions**,
which refresh once every 24 hours, so a budget figure that gets added to TMDB or a newly
ingested comp shows up in tomorrow's prediction without needing a new model version.

This means the database — and the quality of predictions and comparisons — grows organically
as the site gets used, rather than starting complete.

## Database schema

- **`movies`** — TMDB metadata (title, release date, budget, genres, franchise/collection id,
  runtime), plus everything scraped/fetched on top of it: `domestic_gross_usd`,
  `worldwide_gross_usd`, `rotten_tomatoes_score`, `metascore`, `imdb_rating`,
  `critic_scores_checked_at` (cache sentinel — OMDb is only queried once per movie)
- **`people`** — cast/crew, keyed by TMDB person id
- **`movie_credits`** — join table linking people to movies with a role (director/actor) and
  cast order
- **`weekly_gross_observations`** — week-by-week gross per movie/territory, tagged by
  `source` (currently always `boxofficemojo_scrape`) and `territory` (currently always
  `domestic` — see the README's known limitations on why there's no real worldwide weekly
  feed). Drives both the frontend chart and the prediction model's comp data.
- **`model_runs`** — one row per prediction methodology version (`model_version`,
  `feature_list`, `evaluation_metrics`, `is_active`). Changing the prediction logic bumps
  the version rather than silently rewriting historical predictions in place.
- **`predictions`** — per-movie predicted opening weekend, linked to the `model_runs` row
  that produced it, with `predicted_at` for the 24-hour refresh check.

## Backend structure

```
backend/app/
  routers/movies.py          # all API endpoints
  services/
    tmdb_client.py            # TMDB API wrapper
    omdb_client.py             # OMDb API wrapper
    prediction_service.py      # the baseline heuristic + 24h refresh
    comparison_service.py      # franchise/same-year comparison series
    profitability.py           # bomb/flop/success classification
  etl/
    ingest_tmdb.py              # upsert movie + credits from TMDB
    ingest_omdb.py               # fetch + cache critic scores
    scrape_boxofficemojo.py      # weekly gross, lifetime gross scraping
  ml/
    evaluate.py                  # the leave-one-out backtest script
```

### API endpoints

| Endpoint | What it does |
|---|---|
| `GET /api/movies/search?q=` | Live TMDB search |
| `GET /api/movies/browse` | Trending/popular/top-rated/upcoming rows for the home page |
| `GET /api/movies/this-week` | Predictions + actuals for movies opening this Mon–Sun box office week |
| `GET /api/movies/{tmdb_id}` | Full detail: metadata, credits, gross, profitability, critic scores |
| `GET /api/movies/{tmdb_id}/weekly-gross` | Week-by-week domestic gross |
| `GET /api/movies/{tmdb_id}/compare/franchise` | Cumulative gross vs. franchise siblings |
| `GET /api/movies/{tmdb_id}/compare/year` | Cumulative gross vs. same-year releases already in the DB |

## The prediction model, honestly

`prediction_service.py` predicts opening weekend as a **budget-scaled average of comps**: take
the director's prior films (or a genre fallback), and for each comp where *both* the target
film's budget and the comp's budget are known, scale the comp's real opening weekend by
`target_budget / comp_budget` and average. A comp with an unknown budget is dropped rather
than blended in raw — mixing a known-scale target with an unknown-scale comp is exactly what
produced nonsense predictions in an earlier version (see the README's backtest section).

No usable comps means no prediction — the model returns `null` ("not enough data") rather
than guess. This is a deliberate design choice: run `python -m app.ml.evaluate` and see for
yourself what the alternative (a confident, wrong number) actually looked like before this
rule existed.

## Known data limitations

- TMDB's `popularity` field is a live score with no historical time series — it's only usable
  as a signal for upcoming movies at request time, not reconstructable for historical rows.
- Box Office Mojo has no real per-week *international* breakdown, only lifetime totals per
  country — the "Worldwide (estimated)" chart toggle scales the real domestic weekly shape by
  the film's actual gross ratio rather than fabricating a real weekly curve.
- A movie's critic score is usually not public until close to release (embargoes), and — per
  the README's backtest — didn't correlate with prediction error in this project's data
  anyway (r = 0.140 across 42 movies), so it isn't used as a model input.

## Roadmap

See the README's "What's next" section.
