"use client";

import Image from "next/image";
import Link from "next/link";
import { Fragment, useState } from "react";

import { posterUrl } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import { StudioSlateSummary } from "@/lib/types";

function profitCell(estimatedProfitUsd: number | null) {
  if (estimatedProfitUsd == null) {
    return <span className="text-zinc-400 dark:text-zinc-500">Not enough data</span>;
  }
  const isProfit = estimatedProfitUsd >= 0;
  return (
    <span className={isProfit ? "text-[#0ca30c]" : "text-[#d03b3b]"}>
      {isProfit ? "▲" : "▼"} {formatUsd(Math.abs(estimatedProfitUsd))}
    </span>
  );
}

export default function StudioSlateTable({ studios, year }: { studios: StudioSlateSummary[]; year: number }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const sorted = [...studios].sort((a, b) => {
    if (a.estimated_profit_usd == null) return 1;
    if (b.estimated_profit_usd == null) return -1;
    return b.estimated_profit_usd - a.estimated_profit_usd;
  });

  function toggle(slug: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">{year} Studio Slate</h2>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        There&apos;s no public per-film P&amp;L to sum here - studios only disclose quarterly segment totals, never
        per-movie - so profit/loss is an estimate using the same 2.5x-worldwide-multiple breakeven rule of thumb
        used per-movie elsewhere in this app. Co-productions (e.g. a Marvel/Sony film) are credited to the first
        recognized major studio in TMDB&apos;s listing, an approximation. &ldquo;Releases&rdquo; counts films this
        app has tracked for the studio and year, not every wide release that actually happened &mdash; click a
        studio to see which ones.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-left text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
              <th className="py-2 pr-4 font-medium">Studio</th>
              <th className="py-2 pr-4 font-medium">Releases</th>
              <th className="py-2 pr-4 font-medium">Est. Budget</th>
              <th className="py-2 pr-4 font-medium">Est. Worldwide Gross</th>
              <th className="py-2 pr-4 font-medium">Est. Profit / Loss</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((studio) => {
              const isExpanded = expanded.has(studio.slug);
              // Defensive against a stale cached response predating this field (see the
              // studio-slate loading-error incident): treat a missing list as empty, not a crash.
              const movies = studio.movies ?? [];
              return (
                <Fragment key={studio.slug}>
                  <tr className="border-b border-zinc-100 last:border-0 dark:border-zinc-900">
                    <td className="py-2 pr-4 text-zinc-900 dark:text-zinc-50">
                      <button
                        type="button"
                        onClick={() => toggle(studio.slug)}
                        disabled={movies.length === 0}
                        className="touch-manipulation flex items-center gap-1.5 py-1 text-left disabled:cursor-default"
                      >
                        {movies.length > 0 && (
                          <span className="text-zinc-400 dark:text-zinc-500">{isExpanded ? "▾" : "▸"}</span>
                        )}
                        <span>{studio.display_name}</span>
                      </button>
                      {studio.ticker ? (
                        <span className="ml-1.5 text-xs text-zinc-400 dark:text-zinc-500">({studio.ticker})</span>
                      ) : (
                        <span className="ml-1.5 text-xs text-zinc-400 dark:text-zinc-500">No public parent</span>
                      )}
                    </td>
                    <td className="py-2 pr-4 tabular-nums text-zinc-700 dark:text-zinc-300">
                      {studio.release_count}
                      {studio.movies_with_data < studio.release_count && (
                        <span className="text-xs text-zinc-400 dark:text-zinc-500">
                          {" "}
                          ({studio.movies_with_data} with data)
                        </span>
                      )}
                    </td>
                    <td className="py-2 pr-4 tabular-nums text-zinc-700 dark:text-zinc-300">
                      {formatUsd(studio.total_budget_usd)}
                    </td>
                    <td className="py-2 pr-4 tabular-nums text-zinc-700 dark:text-zinc-300">
                      {formatUsd(studio.total_worldwide_gross_usd)}
                    </td>
                    <td className="py-2 pr-4 tabular-nums">{profitCell(studio.estimated_profit_usd)}</td>
                  </tr>
                  {isExpanded && (
                    <tr className="border-b border-zinc-100 dark:border-zinc-900">
                      <td colSpan={5} className="py-3">
                        <div className="flex flex-wrap gap-3">
                          {movies.map((movie) => {
                            const poster = posterUrl(movie.poster_path, "w185");
                            return (
                              <Link
                                key={movie.tmdb_id}
                                href={`/movies/${movie.tmdb_id}`}
                                className="flex items-center gap-2 rounded-md px-1.5 py-1 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                              >
                                <div className="relative h-11 w-8 shrink-0 overflow-hidden rounded bg-zinc-200 dark:bg-zinc-800">
                                  {poster && (
                                    <Image src={poster} alt={movie.title} fill sizes="32px" className="object-cover" />
                                  )}
                                </div>
                                <span className="max-w-[10rem] truncate text-xs text-zinc-700 dark:text-zinc-300">
                                  {movie.title}
                                </span>
                              </Link>
                            );
                          })}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
