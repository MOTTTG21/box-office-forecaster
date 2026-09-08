import { MovieDetail, MovieSearchResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function searchMovies(query: string): Promise<MovieSearchResult[]> {
  const res = await fetch(`${API_URL}/api/movies/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) {
    throw new Error("Search request failed");
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

export function posterUrl(posterPath: string | null, size: "w185" | "w342" | "w500" = "w342"): string | null {
  return posterPath ? `https://image.tmdb.org/t/p/${size}${posterPath}` : null;
}
