from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Movie
from app.services.omdb_client import omdb_client


def ingest_critic_scores(db: Session, movie: Movie) -> Movie:
    """Fetch and store Rotten Tomatoes/Metacritic/IMDb scores from OMDb. Cached on the movie row."""
    if movie.critic_scores_checked_at is not None or not movie.imdb_id:
        return movie

    data = omdb_client.get_ratings_by_imdb_id(movie.imdb_id)
    ratings = {r["Source"]: r["Value"] for r in data.get("Ratings", [])}

    rt_value = ratings.get("Rotten Tomatoes")
    if rt_value:
        movie.rotten_tomatoes_score = int(rt_value.rstrip("%"))

    metascore = data.get("Metascore")
    if metascore and metascore != "N/A":
        movie.metascore = int(metascore)

    imdb_rating = data.get("imdbRating")
    if imdb_rating and imdb_rating != "N/A":
        movie.imdb_rating = float(imdb_rating)

    movie.critic_scores_checked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(movie)
    return movie
