"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { BacktestReport } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--bar:#2a78d6] " + "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--bar:#3987e5]";

export default function BacktestErrorBreakdown({ report }: { report: BacktestReport }) {
  if (report.sample_count === 0) {
    return <p className="text-xs text-zinc-500 dark:text-zinc-400">Backtest hasn&apos;t been run yet.</p>;
  }

  const director = report.by_comp_method.find((g) => g.label === "director");
  const genre = report.by_comp_method.find((g) => g.label === "genre");

  return (
    <div className={`flex flex-col gap-4 ${CHART_VARS}`}>
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <span className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          {report.overall_median_abs_pct_error}%
        </span>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          median absolute error, {report.sample_count} backtested predictions
          {report.computed_at && (
            <> &mdash; last computed {new Date(report.computed_at).toLocaleDateString("en-US")}</>
          )}
        </span>
      </div>

      {director && genre && (
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex flex-col gap-0.5">
            <span className="text-zinc-500 dark:text-zinc-400">Director comps ({director.sample_count})</span>
            <span className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {director.median_abs_pct_error}%
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-zinc-500 dark:text-zinc-400">Genre fallback ({genre.sample_count})</span>
            <span className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {genre.median_abs_pct_error}%
            </span>
          </div>
          <p className="max-w-xs self-end text-zinc-500 dark:text-zinc-400">
            A director&apos;s own track record predicts noticeably better than falling back to a broad genre
            average &mdash; which is the whole reason the model tries director comps first.
          </p>
        </div>
      )}

      {report.by_release_year.length > 1 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">Median error by release year</span>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={report.by_release_year} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
                axisLine={{ stroke: "var(--grid)" }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v: number) => `${v}%`}
                tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip formatter={(value) => [`${value}%`, "Median abs. error"]} />
              <Bar dataKey="median_abs_pct_error" fill="var(--bar)" radius={[4, 4, 0, 0]} maxBarSize={32} />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            2020&apos;s spike is real, not a bug &mdash; pandemic-era theatrical releases broke every historical
            comp a heuristic like this leans on.
          </p>
        </div>
      )}
    </div>
  );
}
