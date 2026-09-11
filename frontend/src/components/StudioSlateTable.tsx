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
  const sorted = [...studios].sort((a, b) => {
    if (a.estimated_profit_usd == null) return 1;
    if (b.estimated_profit_usd == null) return -1;
    return b.estimated_profit_usd - a.estimated_profit_usd;
  });

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">{year} Studio Slate</h2>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        There&apos;s no public per-film P&amp;L to sum here - studios only disclose quarterly segment totals, never
        per-movie - so profit/loss is an estimate using the same 2.5x-worldwide-multiple breakeven rule of thumb
        used per-movie elsewhere in this app. Co-productions (e.g. a Marvel/Sony film) are credited to the first
        recognized major studio in TMDB&apos;s listing, an approximation. &ldquo;Releases&rdquo; counts films this
        app has tracked for the studio and year, not every wide release that actually happened.
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
            {sorted.map((studio) => (
              <tr
                key={studio.slug}
                className="border-b border-zinc-100 last:border-0 dark:border-zinc-900"
              >
                <td className="py-2 pr-4 text-zinc-900 dark:text-zinc-50">
                  {studio.display_name}
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
