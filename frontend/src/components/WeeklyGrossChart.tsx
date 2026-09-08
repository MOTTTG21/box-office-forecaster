"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCompactUsd, formatUsd } from "@/lib/format";
import { WeeklyGrossPoint } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--series:#2a78d6] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--series:#3987e5]";

function tickInterval(pointCount: number): number {
  return Math.max(0, Math.ceil(pointCount / 10) - 1);
}

interface ChartTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: unknown;
  valueLabel: string;
}

function ChartTooltip({ active, payload, label, valueLabel }: ChartTooltipProps) {
  const points = payload as { value?: string | number; payload: WeeklyGrossPoint }[] | undefined;
  if (!active || !points?.length) return null;
  const point = points[0].payload;
  const value = Number(points[0].value);

  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="font-medium text-zinc-900 dark:text-zinc-50">Week {label}</div>
      {point.week_start_date && <div className="text-zinc-500 dark:text-zinc-400">{point.week_start_date}</div>}
      <div className="mt-1 text-zinc-700 dark:text-zinc-300">
        {valueLabel}: <span className="font-medium">{formatUsd(value)}</span>
      </div>
      {point.theater_count != null && (
        <div className="text-zinc-500 dark:text-zinc-400">{point.theater_count.toLocaleString()} theaters</div>
      )}
    </div>
  );
}

export default function WeeklyGrossChart({ data }: { data: WeeklyGrossPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
        No box office data found for this release yet.
      </div>
    );
  }

  const interval = tickInterval(data.length);

  return (
    <div className="flex flex-col gap-8">
      <section className={`flex flex-col gap-2 ${CHART_VARS}`}>
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Weekly Box Office</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis
              dataKey="week_number"
              tickFormatter={(v) => `Wk ${v}`}
              interval={interval}
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
            <Tooltip
              content={({ active, label, payload }) => (
                <ChartTooltip active={active} label={label} payload={payload} valueLabel="Weekend gross" />
              )}
              cursor={{ fill: "var(--grid)" }}
            />
            <Bar dataKey="weekend_gross_usd" fill="var(--series)" radius={[4, 4, 0, 0]} maxBarSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className={`flex flex-col gap-2 ${CHART_VARS}`}>
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Cumulative Gross</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <defs>
              <linearGradient id="cumulativeFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--series)" stopOpacity={0.1} />
                <stop offset="100%" stopColor="var(--series)" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis
              dataKey="week_number"
              tickFormatter={(v) => `Wk ${v}`}
              interval={interval}
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
            <Tooltip
              content={({ active, label, payload }) => (
                <ChartTooltip active={active} label={label} payload={payload} valueLabel="Cumulative gross" />
              )}
              cursor={{ stroke: "var(--grid)" }}
            />
            <Area
              type="monotone"
              dataKey="cumulative_gross_usd"
              stroke="var(--series)"
              strokeWidth={2}
              fill="url(#cumulativeFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}
