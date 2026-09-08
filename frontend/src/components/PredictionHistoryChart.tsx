"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCompactUsd, formatUsd } from "@/lib/format";
import { PredictionHistory } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--forecast-line:#2a78d6] [--resolved-up:#0ca30c] [--resolved-down:#d03b3b] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--forecast-line:#3987e5] " +
  "dark:[--resolved-up:#0ca30c] dark:[--resolved-down:#e66767]";

function dayLabel(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

interface ChartRow {
  label: string;
  predicted: number | null;
  actual: number | null;
  newsReason: string | null;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: ChartRow }[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;

  return (
    <div className="max-w-[220px] rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="font-medium text-zinc-900 dark:text-zinc-50">{row.label}</div>
      {row.predicted != null && (
        <div className="mt-1 text-zinc-700 dark:text-zinc-300">
          Forecast: <span className="font-medium">{formatUsd(row.predicted)}</span>
        </div>
      )}
      {row.actual != null && (
        <div className="mt-1 text-zinc-700 dark:text-zinc-300">
          Actual: <span className="font-medium">{formatUsd(row.actual)}</span>
        </div>
      )}
      {row.newsReason && (
        <div className="mt-1 italic text-zinc-500 dark:text-zinc-500">
          <span className="font-medium not-italic">Claude:</span> {row.newsReason}
        </div>
      )}
    </div>
  );
}

export default function PredictionHistoryChart({ history }: { history: PredictionHistory | null }) {
  if (!history || history.snapshots.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
        No forecast history yet for this release.
      </div>
    );
  }

  const rows: ChartRow[] = history.snapshots.map((s) => ({
    label: dayLabel(s.snapshot_date),
    predicted: s.predicted_weekend_gross_usd,
    actual: null,
    newsReason: s.news_reason,
  }));

  const lastPredicted = [...history.snapshots].reverse().find((s) => s.predicted_weekend_gross_usd != null)
    ?.predicted_weekend_gross_usd;
  const isResolved = history.actual_weekend_gross_usd != null;
  if (isResolved) {
    rows.push({
      label: "Resolved",
      predicted: null,
      actual: history.actual_weekend_gross_usd,
      newsReason: null,
    });
  }

  const beatForecast = isResolved && lastPredicted != null && history.actual_weekend_gross_usd! >= lastPredicted;

  return (
    <div className={`flex flex-col gap-2 ${CHART_VARS}`}>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          {history.is_new_release ? "Opening Weekend Forecast" : `Week ${history.week_number} Forecast`}
        </h2>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          Experimental
        </span>
      </div>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        Fluctuates day to day as Claude researches recent news and buzz for this release. This is a visual,
        exploratory overlay on the backtested baseline model - not itself a validated accuracy improvement.
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={rows} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
            axisLine={{ stroke: "var(--grid)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatCompactUsd}
            tick={{ fill: "var(--axis-ink)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={56}
            domain={["auto", "auto"]}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: "var(--grid)" }} />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="var(--forecast-line)"
            strokeWidth={2}
            strokeDasharray="5 3"
            dot={{ r: 3, strokeWidth: 0, fill: "var(--forecast-line)" }}
            connectNulls
          />
          {isResolved && (
            <Line
              dataKey="actual"
              stroke="none"
              dot={{ r: 6, strokeWidth: 2, stroke: "#fff", fill: beatForecast ? "var(--resolved-up)" : "var(--resolved-down)" }}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
