from datetime import date

from pydantic import BaseModel, ConfigDict


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    release_date: date | None = None
    poster_path: str | None = None


class MovieBrowseRows(BaseModel):
    trending: list[MovieSearchResult]
    popular: list[MovieSearchResult]
    top_rated: list[MovieSearchResult]
    upcoming: list[MovieSearchResult]


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    name: str
    character_name: str | None = None


class RaceEthnicityGroup(BaseModel):
    group: str
    percent: float


class MovieDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    title: str
    overview: str | None = None
    release_date: date | None = None
    status: str
    runtime_minutes: int | None = None
    budget_usd: int | None = None
    domestic_gross_usd: int | None = None
    worldwide_gross_usd: int | None = None
    profitability_status: str | None = None
    rotten_tomatoes_score: int | None = None
    metascore: int | None = None
    imdb_rating: float | None = None
    genres: list[str] | None = None
    poster_path: str | None = None
    popularity_tmdb_snapshot: float | None = None
    director: PersonOut | None = None
    cast: list[PersonOut] = []
    budget_usd_inflation_adjusted: int | None = None
    domestic_gross_usd_inflation_adjusted: int | None = None
    worldwide_gross_usd_inflation_adjusted: int | None = None
    inflation_adjusted_to_year: int | None = None
    demographic_percent_female: float | None = None
    demographic_percent_male: float | None = None
    demographic_percent_under_25: float | None = None
    demographic_percent_25_and_over: float | None = None
    demographic_race_breakdown: list[RaceEthnicityGroup] | None = None
    demographic_source_note: str | None = None


class WeeklyGrossPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_number: int
    week_start_date: date | None = None
    weekend_gross_usd: int | None = None
    cumulative_gross_usd: int | None = None
    theater_count: int | None = None
    rank: int | None = None


class HolidayHighlight(BaseModel):
    name: str
    label: str
    blurb: str


class ThisWeekMovie(BaseModel):
    tmdb_id: int
    title: str
    release_date: date | None = None
    poster_path: str | None = None
    is_new_release: bool
    week_number: int
    predicted_weekend_gross_usd: float | None = None
    actual_weekend_gross_usd: int | None = None
    previous_weekend_gross_usd: int | None = None
    has_audience_demographics: bool = False


class PredictionSnapshotPoint(BaseModel):
    snapshot_date: date
    predicted_weekend_gross_usd: float | None = None
    news_reason: str | None = None


class PredictionHistory(BaseModel):
    week_number: int
    is_new_release: bool
    snapshots: list[PredictionSnapshotPoint]
    actual_weekend_gross_usd: int | None = None


class ComparisonPoint(BaseModel):
    week_number: int
    cumulative_gross_usd: int | None = None


class ComparisonSeries(BaseModel):
    tmdb_id: int
    title: str
    is_current: bool
    points: list[ComparisonPoint]
