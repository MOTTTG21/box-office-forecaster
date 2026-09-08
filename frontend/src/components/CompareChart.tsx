"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCompactUsd, formatUsd } from "@/lib/format";
import { ComparisonSeries } from "@/lib/types";

const SERIES_COLOR_VARS = [
  "var(--cmp-0)",
  "var(--cmp-1)",
  "var(--cmp-2)",
  "var(--cmp-3)",
  "var(--cmp-4)",
  "var(--cmp-5)",
];

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] " +
  "[--cmp-0:#2a78d6] [--cmp-1:#eb6834] [--cmp-2:#1baf7a] [--cmp-3:#eda100] [--cmp-4:#e87ba4] [--cmp-5:#008300] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] " +
  "dark:[--cmp-0:#3987e5] dark:[--cmp-1:#d95926] dark:[--cmp-2:#199e70] dark:[--cmp-3:#c98500] dark:[--cmp-4:#d55181] dark:[--cmp-5:#008300]";

interface TooltipEntry {
  color?: string;
  name?: string;
  value?: number;
}

function CompareTooltip({ active, label, payload }: { active?: boolean; label?: number; payload?: TooltipEntry[] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="mb-1 font-medium text-zinc-900 dark:text-zinc-50">Week {label}</div>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-1.5 text-zinc-700 dark:text-zinc-300">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          {entry.name}: <span className="font-medium">{entry.value != null ? formatUsd(entry.value) : "—"}</span>
        </div>
      ))}
    </div>
  );
}

export default function CompareChart({ series }: { series: ComparisonSeries[] }) {
  if (series.length === 0) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">Not enough comparable data yet.</p>
    );
  }

  const maxWeek = Math.max(...series.flatMap((s) => s.points.map((p) => p.week_number)));

  return (
    <div className={CHART_VARS}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis
            dataKey="week_number"
            type="number"
            domain={[1, maxWeek]}
            allowDuplicatedCategory={false}
            tickFormatter={(v) => `Wk ${v}`}
            tick={{ fill: "var(--axis-ink)", fontSize: 12 }}
            axisLine={{ stroke: "var(--grid)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatCompactUsd}
            tick={{ fill: "var(--axis-ink)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip content={<CompareTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((s, index) => (
            <Line
              key={s.tmdb_id}
              data={s.points}
              dataKey="cumulative_gross_usd"
              name={s.title}
              stroke={SERIES_COLOR_VARS[index % SERIES_COLOR_VARS.length]}
              strokeWidth={s.is_current ? 3 : 2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
