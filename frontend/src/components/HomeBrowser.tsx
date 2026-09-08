"use client";

import { useState } from "react";

import { searchMovies } from "@/lib/api";
import { MovieBrowseRows, MovieSearchResult } from "@/lib/types";

import MovieCard from "./MovieCard";
import MovieRow from "./MovieRow";

const ROW_TITLES: { key: keyof MovieBrowseRows; title: string; autoScroll?: boolean }[] = [
  { key: "trending", title: "Trending This Week", autoScroll: true },
  { key: "popular", title: "Popular Movies" },
  { key: "top_rated", title: "Top Rated" },
  { key: "upcoming", title: "Coming Soon" },
];

export default function HomeBrowser({ rows }: { rows: MovieBrowseRows }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MovieSearchResult[] | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setResults(null);
      return;
    }

    setStatus("loading");
    try {
      const movies = await searchMovies(trimmed);
      setResults(movies);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  function handleClear() {
    setQuery("");
    setResults(null);
    setStatus("idle");
  }

  return (
    <div className="flex w-full flex-col gap-10">
      <form onSubmit={handleSubmit} className="flex w-full gap-2 px-6 sm:px-0">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a movie..."
          className="flex-1 rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900"
        >
          {status === "loading" ? "Searching..." : "Search"}
        </button>
        {results !== null && (
          <button
            type="button"
            onClick={handleClear}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300"
          >
            Clear
          </button>
        )}
      </form>

      {status === "error" && (
        <p className="px-6 text-sm text-red-600 dark:text-red-400 sm:px-0">
          Something went wrong searching. Is the backend running?
        </p>
      )}

      {results !== null ? (
        <div className="grid grid-cols-2 gap-4 px-6 sm:grid-cols-3 sm:px-0 md:grid-cols-4 lg:grid-cols-5">
          {results.map((movie) => (
            <MovieCard key={movie.tmdb_id} movie={movie} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-10">
          {ROW_TITLES.map(({ key, title, autoScroll }) => (
            <MovieRow key={key} title={title} movies={rows[key]} autoScroll={autoScroll} />
          ))}
        </div>
      )}
    </div>
  );
}
