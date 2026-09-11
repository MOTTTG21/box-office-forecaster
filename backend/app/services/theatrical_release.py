from app.models import Movie

MIN_THEATRICAL_RUNTIME_MINUTES = 60


def is_real_theatrical_release(movie: Movie) -> bool:
    # TMDB's release-type filter still lets through TV specials that got a token
    # theatrical qualifying run (e.g. a 50-minute streaming special) - these aren't
    # real wide releases and have no meaningful box office trajectory to predict.
    return movie.runtime_minutes is None or movie.runtime_minutes >= MIN_THEATRICAL_RUNTIME_MINUTES
