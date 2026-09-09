"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { industryYoyChangePct } from "@/lib/industryHealth";
import { formatCompactUsd, formatUsd } from "@/lib/format";
import { IndustryHealthComparison } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--bar-past:#c3c2b7] [--bar-current:#2a78d6] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--bar-past:#52514e] dark:[--bar-current:#3987e5]";

interface TooltipPayloadItem {
  payload: { year: number; total_gross_usd: number | null };
}

function IndustryTooltip({ active, payload }: { active?: boolean; payload?: unknown }) {
  const items = payload as TooltipPayloadItem[] | undefined;
  if (!active || !items?.length) return null;
  const point = items[0].payload;

  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="font-medium text-zinc-900 dark:text-zinc-50">{point.year}</div>
      <div className="text-zinc-700 dark:text-zinc-300">
        {point.total_gross_usd != null ? formatUsd(point.total_gross_usd) : "Not reported yet"}
      </div>
    </div>
  );
}

export default function IndustryHealthChart({ comparison }: { comparison: IndustryHealthComparison }) {
  const usablePoints = comparison.points.filter((p) => p.total_gross_usd != null);
  if (usablePoints.length < 2) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">Not enough industry data yet.</p>;
  }

  const currentYear = new Date(`${comparison.current_week_start}T00:00:00`).getFullYear();
  const yoyPct = industryYoyChangePct(comparison.points);

  return (
    <div className={`flex flex-col gap-2 ${CHART_VARS}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-base font-medium text-zinc-900 dark:text-zinc-50">Industry Health</h2>
        {yoyPct != null && (
          <span className={yoyPct >= 0 ? "text-sm text-[#0ca30c]" : "text-sm text-[#d03b3b]"}>
            {yoyPct >= 0 ? "▲" : "▼"} {Math.abs(yoyPct).toFixed(0)}% vs. same week last comparable year
          </span>
        )}
      </div>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        Total domestic weekend gross across all films this ISO calendar week, vs. the same week in past years.
        The weekend total is a sum of Box Office Mojo&apos;s per-film chart, not a source-reported aggregate.
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={comparison.points} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis
            dataKey="year"
            tick={{ fill: "var(--axis-ink)", fontSize: 12 }}
            axisLine={{ stroke: "var(--grid)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => formatCompactUsd(v)}
            tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<IndustryTooltip />} cursor={{ fill: "var(--grid)" }} />
          <Bar dataKey="total_gross_usd" radius={[4, 4, 0, 0]} maxBarSize={40}>
            {comparison.points.map((point) => (
              <Cell key={point.year} fill={point.year === currentYear ? "var(--bar-current)" : "var(--bar-past)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
