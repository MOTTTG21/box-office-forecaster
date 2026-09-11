"""Per-IP rate limiting. Keyed by client address, which requires uvicorn to be trusting
X-Forwarded-For from Railway's proxy (see the Procfile's --proxy-headers flag) - without that,
every visitor behind the proxy would share one bucket.

The default limit is a generous safety net against a runaway script, not something a real
visitor should ever hit browsing normally. Routes that trigger a live third-party API call with
no caching (search) or a first-time ingest (movie/person lookup by id) get a tighter limit,
since those are the ones that can burn through a shared external API quota (TMDB, OMDb) or get
the server's IP rate-limited by Box Office Mojo.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

DEFAULT_RATE_LIMIT = "100/minute"
SEARCH_RATE_LIMIT = "20/minute"
LOOKUP_RATE_LIMIT = "30/minute"
DATA_QUALITY_RATE_LIMIT = "10/minute"
STUDIO_RATE_LIMIT = "10/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMIT])
