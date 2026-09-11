"use client";

import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { StudioMarketComparison } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--boxoffice-line:#eb6834] [--stock-line:#2a78d6] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--boxoffice-line:#d95926] dark:[--stock-line:#3987e5]";

function weekLabel(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function StudioMarketPanel({ comparisons }: { comparisons: StudioMarketComparison[] }) {
  const withTicker = comparisons.filter((c) => c.ticker != null);
  const [selectedSlug, setSelectedSlug] = useState(withTicker[0]?.slug);

  if (withTicker.length === 0) {
    return null;
  }

  const selected = withTicker.find((c) => c.slug === selectedSlug) ?? withTicker[0];
  const chartData = selected.points.map((p) => ({
    label: weekLabel(p.week_start_date),
    box_office_pct_change: p.box_office_pct_change,
    stock_pct_change: p.stock_pct_change,
  }));

  return (
    <div className={`flex flex-col gap-3 ${CHART_VARS}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Slate vs. Parent Stock</h2>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          Experimental
        </span>
      </div>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        Each studio&apos;s own weekly domestic box office (its tracked slate, not the parent company&apos;s actual
        revenue) plotted against real weekly closing-price moves in its publicly traded parent, both indexed to %
        change from the first comparable week - box office dollars and a stock price live on different scales, so
        this is one shared axis, not two. This is <strong>not a statistically meaningful correlation</strong>: a
        studio&apos;s theatrical slate is a small, lumpy fraction of its parent&apos;s overall business (streaming,
        parks, cable, and more), while the stock reflects all of it at once. Read it as an exploratory overlay, not
        a validated signal.
      </p>

      <div className="flex flex-wrap gap-1.5">
        {withTicker.map((c) => (
          <button
            key={c.slug}
            onClick={() => setSelectedSlug(c.slug)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              c.slug === selected.slug
                ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
            }`}
          >
            {c.display_name}
          </button>
        ))}
      </div>

      {chartData.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Not enough overlapping box office and stock data yet for {selected.display_name} in {selected.year}.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
              axisLine={{ stroke: "var(--grid)" }}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis
              tickFormatter={(v: number) => `${v}%`}
              tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={44}
            />
            <Tooltip
              formatter={(value, name) => [
                `${Number(value).toFixed(1)}%`,
                name === "box_office_pct_change" ? "Box office" : "Stock",
              ]}
            />
            <Legend
              formatter={(value: string) => (value === "box_office_pct_change" ? "Box office" : "Stock")}
              wrapperStyle={{ fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="box_office_pct_change"
              stroke="var(--boxoffice-line)"
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="stock_pct_change"
              stroke="var(--stock-line)"
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
