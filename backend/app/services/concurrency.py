"""Runs network-bound per-item work (TMDB discovery, Box Office Mojo scraping) concurrently
instead of one item at a time. The Studios feature originally did this sequentially across 7
studios and, per studio, across every movie missing data - slow enough on a cold cache to
exceed Vercel's serverless function timeout (a real production incident: "Failed to load
studio slate" errors in Vercel logs, traced to the backend endpoint alone taking 20+ seconds).

Each worker gets its own DB session, since a SQLAlchemy Session isn't safe to share across
threads. A worker's unexpected failure is swallowed rather than propagated - the same "one bad
item never takes down the whole batch" rule already applied to individual httpx errors
elsewhere in this codebase, just enforced one level up for whatever a worker didn't already
catch itself.
"""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from sqlalchemy.orm import Session

from app.core.db import SessionLocal

T = TypeVar("T")

MAX_WORKERS = 8


def run_with_isolated_sessions(items: Iterable[T], work: Callable[[Session, T], None]) -> None:
    items = list(items)
    if not items:
        return

    def _run(item: T) -> None:
        session = SessionLocal()
        try:
            work(session, item)
        except Exception:
            pass  # this item's data just won't be updated this request; never crash the batch
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(items))) as executor:
        list(executor.map(_run, items))
