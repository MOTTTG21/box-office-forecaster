export interface MovieSearchResult {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  poster_path: string | null;
}

export interface MovieBrowseRows {
  trending: MovieSearchResult[];
  popular: MovieSearchResult[];
  top_rated: MovieSearchResult[];
  upcoming: MovieSearchResult[];
}

export interface Person {
  id: number;
  tmdb_id: number;
  name: string;
  character_name: string | null;
}

export interface PersonSearchResult {
  tmdb_id: number;
  name: string;
  profile_path: string | null;
  known_for_department: string | null;
}

export interface FilmographyItem {
  tmdb_id: number;
  title: string;
  poster_path: string | null;
  release_date: string | null;
  role: string;
}

export interface PersonDetail {
  tmdb_id: number;
  name: string;
  profile_path: string | null;
  known_for_department: string | null;
  biography: string | null;
  filmography: FilmographyItem[];
}

export interface MovieDetail {
  id: number;
  tmdb_id: number;
  title: string;
  overview: string | null;
  release_date: string | null;
  status: string;
  runtime_minutes: number | null;
  budget_usd: number | null;
  domestic_gross_usd: number | null;
  worldwide_gross_usd: number | null;
  profitability_status: "bomb" | "flop" | "success" | null;
  rotten_tomatoes_score: number | null;
  metascore: number | null;
  imdb_rating: number | null;
  genres: string[] | null;
  poster_path: string | null;
  popularity_tmdb_snapshot: number | null;
  director: Person | null;
  cast: Person[];
  budget_usd_inflation_adjusted: number | null;
  domestic_gross_usd_inflation_adjusted: number | null;
  worldwide_gross_usd_inflation_adjusted: number | null;
  inflation_adjusted_to_year: number | null;
}

export interface WeeklyGrossPoint {
  week_number: number;
  week_start_date: string | null;
  weekend_gross_usd: number | null;
  cumulative_gross_usd: number | null;
  theater_count: number | null;
  rank: number | null;
}

export interface HolidayHighlight {
  name: string;
  label: string;
  blurb: string;
}

export interface ThisWeekMovie {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  poster_path: string | null;
  is_new_release: boolean;
  week_number: number;
  predicted_weekend_gross_usd: number | null;
  actual_weekend_gross_usd: number | null;
  previous_weekend_gross_usd: number | null;
}

export interface PredictionSnapshotPoint {
  snapshot_date: string;
  predicted_weekend_gross_usd: number | null;
  news_reason: string | null;
}

export interface PredictionHistory {
  week_number: number;
  is_new_release: boolean;
  snapshots: PredictionSnapshotPoint[];
  actual_weekend_gross_usd: number | null;
}

export interface ComparisonPoint {
  week_number: number;
  cumulative_gross_usd: number | null;
}

export interface ComparisonSeries {
  tmdb_id: number;
  title: string;
  is_current: boolean;
  points: ComparisonPoint[];
}

export interface IndustryWeekPoint {
  year: number;
  week_start_date: string;
  total_gross_usd: number | null;
}

export interface IndustryHealthComparison {
  current_week_start: string;
  current_week_end: string;
  points: IndustryWeekPoint[];
}

export interface DataAnomaly {
  tmdb_id: number;
  title: string;
  poster_path: string | null;
  rule_name: string;
  severity: "high" | "medium" | "low";
  detail: string;
  ai_explanation: string | null;
  detected_at: string;
}
