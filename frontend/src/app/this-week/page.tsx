import CombinedForecastChart from "@/components/CombinedForecastChart";
import HolidayBadge from "@/components/HolidayBadge";
import IndustryHealthChart from "@/components/IndustryHealthChart";
import { getHolidayContext, getIndustryHealth, getPredictionHistory, getThisWeek } from "@/lib/api";
import { HolidayHighlight, IndustryHealthComparison, PredictionHistory } from "@/lib/types";

export default async function ThisWeekPage() {
  const movies = await getThisWeek();
  const histories = await Promise.all(
    movies.map(async (movie): Promise<PredictionHistory | null> => {
      try {
        return await getPredictionHistory(movie.tmdb_id);
      } catch {
        return null;
      }
    }),
  );

  let holiday: HolidayHighlight | null = null;
  try {
    holiday = await getHolidayContext();
  } catch {
    holiday = null;
  }

  let industryHealth: IndustryHealthComparison | null = null;
  try {
    industryHealth = await getIndustryHealth();
  } catch {
    industryHealth = null;
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Top 10 in Theaters This Week
          </h1>
          <p className="max-w-xl text-sm text-zinc-600 dark:text-zinc-400">
            The top 10 highest-grossing films predicted for this box office weekend (Monday&ndash;Sunday) &mdash;
            new releases (opening-weekend forecast) and holdovers (predicted from their own trajectory so far),
            ranked together. A prediction only shows once there&apos;s enough data to compare against, so
            &ldquo;not enough data&rdquo; is expected for some titles.
          </p>
        </div>

        <HolidayBadge holiday={holiday} />

        {industryHealth && <IndustryHealthChart comparison={industryHealth} />}

        {movies.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No movies found in this window.</p>
        ) : (
          <CombinedForecastChart entries={movies.map((movie, index) => ({ movie, history: histories[index] }))} />
        )}
      </div>
    </div>
  );
}
