import Link from "next/link";

import StudioMarketPanel from "@/components/StudioMarketPanel";
import StudioSlateTable from "@/components/StudioSlateTable";
import { getStudioMarketComparison, getStudioSlate } from "@/lib/api";
import { StudioMarketComparison } from "@/lib/types";

const YEAR_OPTIONS_BACK = 4;

export default async function StudiosPage({
  searchParams,
}: {
  searchParams: Promise<{ year?: string }>;
}) {
  const { year: yearParam } = await searchParams;
  const currentYear = new Date().getFullYear();
  const year = yearParam ? parseInt(yearParam, 10) || currentYear : currentYear;

  const slate = await getStudioSlate(year);

  const withTicker = slate.studios.filter((s) => s.ticker != null);
  const marketComparisons: StudioMarketComparison[] = await Promise.all(
    withTicker.map(async (studio) => {
      try {
        return await getStudioMarketComparison(studio.slug, year);
      } catch {
        return { slug: studio.slug, display_name: studio.display_name, ticker: studio.ticker, year, points: [] };
      }
    }),
  );

  const yearOptions = Array.from({ length: YEAR_OPTIONS_BACK + 1 }, (_, i) => currentYear - i);

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Studios</h1>
          <p className="max-w-xl text-sm text-zinc-600 dark:text-zinc-400">
            How each major studio&apos;s theatrical slate performed for the year, and whether that slate&apos;s box
            office moved with its publicly traded parent company&apos;s stock.
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {yearOptions.map((y) => (
            <Link
              key={y}
              href={`/studios?year=${y}`}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                y === year
                  ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
              }`}
            >
              {y}
            </Link>
          ))}
        </div>

        <StudioSlateTable studios={slate.studios} year={year} />

        <StudioMarketPanel comparisons={marketComparisons} />
      </div>
    </div>
  );
}
