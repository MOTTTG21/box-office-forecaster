import Link from "next/link";

import HomeBrowser from "@/components/HomeBrowser";
import { getBrowseRows } from "@/lib/api";

export default async function Home() {
  const rows = await getBrowseRows();

  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-50 py-16 dark:bg-black">
      <main className="flex w-full max-w-7xl flex-col items-center gap-10">
        <div className="flex flex-col items-center gap-3 px-6 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Movie Box Office Forecaster
          </h1>
          <p className="max-w-lg text-sm text-zinc-600 dark:text-zinc-400">
            Predicts opening weekends by scaling a director&apos;s past films (or genre comps) to a movie&apos;s
            budget &mdash; then backtests every prediction, leave-one-out, against what actually happened.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-xs text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">~67% median error</span>
            <span>on wide releases &mdash; an honest number, not a polished one.</span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-1">
            <Link
              href="/this-week"
              className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              See this week&apos;s predictions
            </Link>
            <Link
              href="/about"
              className="text-sm text-zinc-600 underline decoration-zinc-300 underline-offset-2 hover:text-zinc-900 dark:text-zinc-400 dark:decoration-zinc-700 dark:hover:text-zinc-50"
            >
              How the backtest works
            </Link>
          </div>
        </div>
        <HomeBrowser rows={rows} />
      </main>
    </div>
  );
}
