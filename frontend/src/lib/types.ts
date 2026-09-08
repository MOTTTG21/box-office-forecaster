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

export interface MovieDetail {
  id: number;
  tmdb_id: number;
  title: string;
  overview: string | null;
  release_date: string | null;
  status: string;
  runtime_minutes: number | null;
  budget_usd: number | null;
  genres: string[] | null;
  poster_path: string | null;
  popularity_tmdb_snapshot: number | null;
  director: Person | null;
  cast: Person[];
}

export interface WeeklyGrossPoint {
  week_number: number;
  week_start_date: string | null;
  weekend_gross_usd: number | null;
  cumulative_gross_usd: number | null;
  theater_count: number | null;
  rank: number | null;
}

export interface ThisWeekMovie {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  poster_path: string | null;
  predicted_opening_weekend_usd: number | null;
  actual_opening_weekend_usd: number | null;
}
