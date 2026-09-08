export interface MovieSearchResult {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  poster_path: string | null;
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
