import { ComparisonSeries, MovieBrowseRows, MovieDetail, MovieSearchResult, ThisWeekMovie, WeeklyGrossPoint } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function searchMovies(query: string): Promise<MovieSearchResult[]> {
  const res = await fetch(`${API_URL}/api/movies/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) {
    throw new Error("Search request failed");
  }
  return res.json();
}

export async function getBrowseRows(): Promise<MovieBrowseRows> {
  const res = await fetch(`${API_URL}/api/movies/browse`, { next: { revalidate: 3600 } });
  if (!res.ok) {
    throw new Error("Failed to load browse rows");
  }
  return res.json();
}

export async function getMovie(tmdbId: number): Promise<MovieDetail> {
  const res = await fetch(`${API_URL}/api/movies/${tmdbId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Movie not found");
  }
  return res.json();
}

export async function getWeeklyGross(tmdbId: number): Promise<WeeklyGrossPoint[]> {
  const res = await fetch(`${API_URL}/api/movies/${tmdbId}/weekly-gross`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load weekly gross");
  }
  return res.json();
}

export async function getThisWeek(): Promise<ThisWeekMovie[]> {
  const res = await fetch(`${API_URL}/api/movies/this-week`, { next: { revalidate: 900 } });
  if (!res.ok) {
    throw new Error("Failed to load this week's movies");
  }
  return res.json();
}

export async function getFranchiseComparison(tmdbId: number): Promise<ComparisonSeries[]> {
  const res = await fetch(`${API_URL}/api/movies/${tmdbId}/compare/franchise`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load franchise comparison");
  }
  return res.json();
}

export async function getYearComparison(tmdbId: number): Promise<ComparisonSeries[]> {
  const res = await fetch(`${API_URL}/api/movies/${tmdbId}/compare/year`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to load year comparison");
  }
  return res.json();
}

export function posterUrl(posterPath: string | null, size: "w185" | "w342" | "w500" = "w342"): string | null {
  return posterPath ? `https://image.tmdb.org/t/p/${size}${posterPath}` : null;
}
