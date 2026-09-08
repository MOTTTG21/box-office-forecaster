# Architecture Notes

## Overview

Monorepo with a Next.js frontend and a FastAPI backend backed by Postgres. See root `README.md` for local setup.

## Database schema (initial)

- `movies` — TMDB metadata snapshot (title, release date, budget, genres, franchise/collection id, popularity snapshot)
- `people` — cast/crew, keyed by TMDB person id
- `movie_credits` — join table linking people to movies with a role (director/actor/writer/producer) and cast order
- `weekly_gross_observations` — week-by-week gross figures per movie/territory, tagged by source (`kaggle_historical` or `boxofficemojo_scrape`); this is what both the frontend chart and the ML training set are built from
- `model_runs` — metadata for each trained model artifact (hyperparameters, evaluation metrics, which one is currently active)
- `predictions` — per-movie predicted totals and decay curve, linked to the model run that produced them

## Known data limitations

TMDB's `popularity` field is a live score with no historical time series — it's only usable as a "social buzz" feature for upcoming movies at inference time, not reconstructable for historical training rows. This gets documented on the app's methodology/about page once built.

## Roadmap

1. TMDB ingestion + movie search/detail UI, deployed live (Vercel + Railway)
2. Historical box-office dataset ETL + week-by-week gross chart
3. Feature engineering + ensemble regressors (opening weekend / domestic / worldwide) + prediction endpoint/UI
4. Movie-specific decay-curve model + Box Office Mojo scraper for post-release actuals + backtesting view + trends page
