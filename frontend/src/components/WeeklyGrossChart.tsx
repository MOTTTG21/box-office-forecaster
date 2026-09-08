"use client";

import { useState } from "react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Label,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatCompactUsd, formatUsd } from "@/lib/format";
import { WeeklyGrossPoint } from "@/lib/types";

// Must match PROFIT_MULTIPLE_FOR_SUCCESS in backend/app/services/profitability.py
const PROFIT_MULTIPLE_FOR_SUCCESS = 2.5;

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--series:#2a78d6] " +
  "[--wow-up:#0ca30c] [--wow-mild:#fab219] [--wow-steep:#ec835a] [--wow-severe:#d03b3b] " +
  "[--budget-line:#52514e] [--profit-line:#0ca30c] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--series:#3987e5] " +
  "dark:[--wow-up:#0ca30c] dark:[--wow-mild:#fab219] dark:[--wow-steep:#ec835a] dark:[--wow-severe:#d03b3b] " +
  "dark:[--budget-line:#c3c2b7] dark:[--profit-line:#0ca30c]";

function tickInterval(pointCount: number): number {
  return Math.max(0, Math.ceil(pointCount / 10) - 1);
}

// Week-over-week change vs. the prior weekend: up -> green, a mild drop (<40%) -> yellow,
// a steep drop (40-60%) -> orange, a severe drop (>60%) -> red. Week 1 has no prior
// weekend to compare against, so it stays the neutral series color.
function weekOverWeekColor(data: WeeklyGrossPoint[], index: number): string {
  const current = data[index].weekend_gross_usd;
  const previous = index > 0 ? data[index - 1].weekend_gross_usd : null;
  if (current == null || !previous) return "var(--series)";

  const change = (current - previous) / previous;
  if (change >= 0) return "var(--wow-up)";
  if (change > -0.4) return "var(--wow-mild)";
  if (change >= -0.6) return "var(--wow-steep)";
  return "var(--wow-severe)";
}

interface ChartTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: unknown;
  valueLabel: string;
  fullData?: WeeklyGrossPoint[];
}

function ChartTooltip({ active, payload, label, valueLabel, fullData }: ChartTooltipProps) {
  const points = payload as { value?: string | number; payload: WeeklyGrossPoint }[] | undefined;
  if (!active || !points?.length) return null;
  const point = points[0].payload;
  const value = Number(points[0].value);

  const index = fullData?.findIndex((p) => p.week_number === point.week_number) ?? -1;
  const previous = index > 0 ? fullData![index - 1].weekend_gross_usd : null;
  const weekOverWeekPct =
    fullData && previous && point.weekend_gross_usd != null ? (point.weekend_gross_usd - previous) / previous : null;

  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="font-medium text-zinc-900 dark:text-zinc-50">Week {label}</div>
      {point.week_start_date && <div className="text-zinc-500 dark:text-zinc-400">{point.week_start_date}</div>}
      <div className="mt-1 text-zinc-700 dark:text-zinc-300">
        {valueLabel}: <span className="font-medium">{formatUsd(value)}</span>
      </div>
      {weekOverWeekPct != null && (
        <div className="text-zinc-500 dark:text-zinc-400">
          {weekOverWeekPct >= 0 ? "▲" : "▼"} {Math.abs(weekOverWeekPct * 100).toFixed(0)}% vs. prior weekend
        </div>
      )}
      {point.theater_count != null && (
        <div className="text-zinc-500 dark:text-zinc-400">{point.theater_count.toLocaleString()} theaters</div>
      )}
    </div>
  );
}

export default function WeeklyGrossChart({
  data,
  budgetUsd,
  domesticGrossUsd,
  worldwideGrossUsd,
}: {
  data: WeeklyGrossPoint[];
  budgetUsd?: number | null;
  domesticGrossUsd?: number | null;
  worldwideGrossUsd?: number | null;
}) {
  const canEstimateWorldwide =
    !!domesticGrossUsd && !!worldwideGrossUsd && worldwideGrossUsd > domesticGrossUsd * 1.05;
  const [territory, setTerritory] = useState<"domestic" | "worldwide">("domestic");

  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
        No box office data found for this release yet.
      </div>
    );
  }

  const interval = tickInterval(data.length);
  const scaleFactor =
    territory === "worldwide" && canEstimateWorldwide ? worldwideGrossUsd! / domesticGrossUsd! : 1;
  const displayData =
    scaleFactor === 1
      ? data
      : data.map((point) => ({
          ...point,
          weekend_gross_usd: point.weekend_gross_usd != null ? point.weekend_gross_usd * scaleFactor : null,
          cumulative_gross_usd: point.cumulative_gross_usd != null ? point.cumulative_gross_usd * scaleFactor : null,
        }));
  const valueLabelSuffix = territory === "worldwide" ? " (est. worldwide)" : "";

  return (
    <div className="flex flex-col gap-8">
      {canEstimateWorldwide && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-zinc-500 dark:text-zinc-400">Territory:</span>
          <div className="flex gap-1 rounded-md border border-zinc-200 p-0.5 dark:border-zinc-800">
            <button
              type="button"
              onClick={() => setTerritory("domestic")}
              className={`rounded px-3 py-1 ${
                territory === "domestic"
                  ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                  : "text-zinc-600 dark:text-zinc-400"
              }`}
            >
              Domestic
            </button>
            <button
              type="button"
              onClick={() => setTerritory("worldwide")}
              className={`rounded px-3 py-1 ${
                territory === "worldwide"
                  ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                  : "text-zinc-600 dark:text-zinc-400"
              }`}
            >
              Worldwide (estimated)
            </button>
          </div>
          {territory === "worldwide" && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              Scales the real domestic weekly shape by this film&apos;s domestic-to-worldwide ratio — not actual
              weekly international data, which isn&apos;t publicly available.
            </span>
          )}
        </div>
      )}

      <section className={`flex flex-col gap-2 ${CHART_VARS}`}>
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Weekly Box Office</h2>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-zinc-500 dark:text-zinc-400">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--wow-up)" }} /> Up
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--wow-mild)" }} /> Drop &lt;40%
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--wow-steep)" }} /> Drop 40-60%
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--wow-severe)" }} /> Drop &gt;60%
            </span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={displayData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
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
                <ChartTooltip
                  active={active}
                  label={label}
                  payload={payload}
                  valueLabel={`Weekend gross${valueLabelSuffix}`}
                  fullData={displayData}
                />
              )}
              cursor={{ fill: "var(--grid)" }}
            />
            <Bar dataKey="weekend_gross_usd" radius={[4, 4, 0, 0]} maxBarSize={24}>
              {displayData.map((_, index) => (
                <Cell key={index} fill={weekOverWeekColor(displayData, index)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className={`flex flex-col gap-2 ${CHART_VARS}`}>
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Cumulative Gross</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={displayData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
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
                <ChartTooltip
                  active={active}
                  label={label}
                  payload={payload}
                  valueLabel={`Cumulative gross${valueLabelSuffix}`}
                />
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
            {!!budgetUsd && (
              <ReferenceLine y={budgetUsd} stroke="var(--budget-line)" strokeDasharray="4 4" strokeWidth={1.5}>
                <Label value="Budget" position="insideTopLeft" fill="var(--budget-line)" fontSize={11} />
              </ReferenceLine>
            )}
            {!!budgetUsd && (
              <ReferenceLine
                y={budgetUsd * PROFIT_MULTIPLE_FOR_SUCCESS}
                stroke="var(--profit-line)"
                strokeDasharray="4 4"
                strokeWidth={1.5}
              >
                <Label
                  value={`Profit (${PROFIT_MULTIPLE_FOR_SUCCESS}x budget)`}
                  position="insideTopLeft"
                  fill="var(--profit-line)"
                  fontSize={11}
                />
              </ReferenceLine>
            )}
          </AreaChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}
