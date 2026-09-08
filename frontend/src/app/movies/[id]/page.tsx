import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getFranchiseComparison, getMovie, getWeeklyGross, getYearComparison, posterUrl } from "@/lib/api";
import CompareSection from "@/components/CompareSection";
import CriticScores from "@/components/CriticScores";
import ProfitabilityBanner from "@/components/ProfitabilityBanner";
import WeeklyGrossChart from "@/components/WeeklyGrossChart";
import { formatUsd } from "@/lib/format";
import { ComparisonSeries, WeeklyGrossPoint } from "@/lib/types";

export default async function MovieDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tmdbId = Number(id);

  let movie;
  try {
    movie = await getMovie(tmdbId);
  } catch {
    notFound();
  }

  const poster = posterUrl(movie.poster_path, "original");

  let weeklyGross: WeeklyGrossPoint[] = [];
  let franchiseComparison: ComparisonSeries[] = [];
  let yearComparison: ComparisonSeries[] = [];
  if (movie.status === "released") {
    try {
      weeklyGross = await getWeeklyGross(tmdbId);
    } catch {
      weeklyGross = [];
    }
    try {
      [franchiseComparison, yearComparison] = await Promise.all([
        getFranchiseComparison(tmdbId),
        getYearComparison(tmdbId),
      ]);
    } catch {
      franchiseComparison = [];
      yearComparison = [];
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
        <Link href="/" className="text-sm text-zinc-500 hover:underline dark:text-zinc-400">
          &larr; Back to search
        </Link>

        <div className="flex flex-col gap-6 sm:flex-row">
          <div className="relative w-48 shrink-0">
            <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-zinc-200 dark:bg-zinc-800">
              {poster ? (
                <Image src={poster} alt={movie.title} fill sizes="192px" className="object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-xs text-zinc-400">No poster</div>
              )}
            </div>
            <ProfitabilityBanner
              status={movie.profitability_status}
              releaseDate={movie.release_date}
              movieStatus={movie.status}
            />
          </div>

          <div className="flex flex-1 flex-col gap-3">
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{movie.title}</h1>
            <div className="flex flex-wrap gap-2 text-xs text-zinc-500 dark:text-zinc-400">
              <span>{movie.release_date ?? "Release date TBA"}</span>
              {movie.runtime_minutes && <span>&middot; {movie.runtime_minutes} min</span>}
              <span className="capitalize">&middot; {movie.status}</span>
            </div>
            {movie.genres && movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {movie.genres.map((genre) => (
                  <span
                    key={genre}
                    className="rounded-full bg-zinc-200 px-2.5 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}
            <CriticScores
              rottenTomatoesScore={movie.rotten_tomatoes_score}
              metascore={movie.metascore}
              imdbRating={movie.imdb_rating}
            />
            {movie.overview && (
              <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">{movie.overview}</p>
            )}
            <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <dt className="text-zinc-500 dark:text-zinc-400">Budget</dt>
              <dd className="text-zinc-900 dark:text-zinc-50">{formatUsd(movie.budget_usd)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Director</dt>
              <dd className="text-zinc-900 dark:text-zinc-50">{movie.director?.name ?? "Unknown"}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Domestic Gross</dt>
              <dd className="text-zinc-900 dark:text-zinc-50">{formatUsd(movie.domestic_gross_usd)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Worldwide Gross</dt>
              <dd className="text-zinc-900 dark:text-zinc-50">{formatUsd(movie.worldwide_gross_usd)}</dd>
            </dl>
          </div>
        </div>

        {movie.cast.length > 0 && (
          <div className="flex flex-col gap-3">
            <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Top Cast</h2>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-zinc-700 dark:text-zinc-300">
              {movie.cast.map((member) => (
                <span key={member.id}>
                  {member.name}
                  {member.character_name && (
                    <span className="text-zinc-500 dark:text-zinc-400"> as {member.character_name}</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        <WeeklyGrossChart
          data={weeklyGross}
          budgetUsd={movie.budget_usd}
          domesticGrossUsd={movie.domestic_gross_usd}
          worldwideGrossUsd={movie.worldwide_gross_usd}
        />

        {(franchiseComparison.length > 0 || yearComparison.length > 0) && (
          <CompareSection franchise={franchiseComparison} year={yearComparison} />
        )}

        <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
          Gross prediction coming soon.
        </div>
      </div>
    </div>
  );
}
