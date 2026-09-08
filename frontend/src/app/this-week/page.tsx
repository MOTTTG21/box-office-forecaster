import ForecastCard from "@/components/ForecastCard";
import { getThisWeek } from "@/lib/api";

export default async function ThisWeekPage() {
  const movies = await getThisWeek();

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            This Week in Box Office
          </h1>
          <p className="max-w-xl text-sm text-zinc-600 dark:text-zinc-400">
            Domestic opening weekend forecast for movies releasing this box office week (Monday&ndash;Sunday).
            Predictions refresh daily. Early baseline model &mdash; a prediction only shows once we have real
            budget data to compare against, so &ldquo;not enough data&rdquo; is expected and will fill in as
            that data becomes available.
          </p>
        </div>

        {movies.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No wide releases found in this window.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {movies.map((movie) => (
              <ForecastCard key={movie.tmdb_id} movie={movie} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
