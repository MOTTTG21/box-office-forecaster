"use client";

import Image from "next/image";
import { useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { posterUrl } from "@/lib/api";
import { formatCompactUsd, formatUsd } from "@/lib/format";
import { PredictionHistory, ThisWeekMovie } from "@/lib/types";

const CHART_VARS =
  "[--grid:#e1e0d9] [--axis-ink:#898781] [--muted-line:#c3c2b7] [--highlight-line:#2a78d6] " +
  "[--resolved-up:#0ca30c] [--resolved-down:#d03b3b] " +
  "dark:[--grid:#2c2c2a] dark:[--axis-ink:#898781] dark:[--muted-line:#52514e] dark:[--highlight-line:#3987e5] " +
  "dark:[--resolved-up:#0ca30c] dark:[--resolved-down:#e66767]";

const HEAT_TIERS = [
  { max: 5_000_000, label: "Light", chip: "bg-[#2a78d6]/15 text-[#2a78d6] dark:bg-[#3987e5]/20 dark:text-[#6da7ec]" },
  { max: 30_000_000, label: "Moderate", chip: "bg-zinc-500/15 text-zinc-600 dark:bg-zinc-400/20 dark:text-zinc-300" },
  { max: 80_000_000, label: "Hot", chip: "bg-[#eb6834]/15 text-[#eb6834] dark:bg-[#d95926]/20 dark:text-[#f0955f]" },
  {
    max: Infinity,
    label: "Blockbuster",
    chip: "bg-[#e34948]/15 text-[#e34948] dark:bg-[#e66767]/20 dark:text-[#ef8a89]",
  },
];

function heatTier(amount: number | null) {
  if (amount == null) return HEAT_TIERS[1];
  return HEAT_TIERS.find((tier) => amount <= tier.max) ?? HEAT_TIERS[HEAT_TIERS.length - 1];
}

function dayLabel(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

function movieKey(tmdbId: number): string {
  return `m${tmdbId}`;
}

interface Entry {
  movie: ThisWeekMovie;
  history: PredictionHistory | null;
}

interface ChartRow {
  label: string;
  [movieKey: string]: string | number | null;
}

interface DotProps {
  cx?: number;
  cy?: number;
  index?: number;
}

interface TooltipPayloadItem {
  dataKey?: string;
  value?: number;
}

function ChartTooltip({
  active,
  label,
  payload,
  entries,
}: {
  active?: boolean;
  label?: string | number;
  payload?: unknown;
  entries: Entry[];
}) {
  const items = payload as TooltipPayloadItem[] | undefined;
  if (!active || !items?.length) return null;

  const sorted = items.filter((p) => p.value != null).sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  if (sorted.length === 0) return null;

  return (
    <div className="max-h-64 max-w-[240px] overflow-y-auto rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="mb-1 font-medium text-zinc-900 dark:text-zinc-50">{label}</div>
      {sorted.map((item) => {
        const entry = entries.find((e) => movieKey(e.movie.tmdb_id) === item.dataKey);
        if (!entry) return null;
        return (
          <div key={item.dataKey} className="flex justify-between gap-3 text-zinc-700 dark:text-zinc-300">
            <span className="line-clamp-1">{entry.movie.title}</span>
            <span className="font-medium tabular-nums">{formatUsd(item.value ?? null)}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function CombinedForecastChart({ entries }: { entries: Entry[] }) {
  const [highlightedId, setHighlightedId] = useState<number | null>(null);

  const allDates = Array.from(
    new Set(entries.flatMap((e) => e.history?.snapshots.map((s) => s.snapshot_date) ?? [])),
  ).sort();

  if (allDates.length === 0) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        No forecast history recorded yet - check back tomorrow.
      </p>
    );
  }

  const rows: ChartRow[] = allDates.map((date) => {
    const row: ChartRow = { label: dayLabel(date) };
    for (const { movie, history } of entries) {
      const snapshot = history?.snapshots.find((s) => s.snapshot_date === date);
      row[movieKey(movie.tmdb_id)] = snapshot?.predicted_weekend_gross_usd ?? null;
    }
    return row;
  });

  function lastValueIndex(key: string): number {
    for (let i = rows.length - 1; i >= 0; i--) {
      if (rows[i][key] != null) return i;
    }
    return -1;
  }

  return (
    <div className={`flex flex-col gap-4 ${CHART_VARS}`}>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Forecast Trend</h2>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          Experimental
        </span>
      </div>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        The chart above tracks each film&apos;s <strong>projected amount made during the weekend</strong>, day by
        day, fluctuating as Claude researches recent news and buzz. Hover a title below to highlight its line. This
        overlay is exploratory, not a validated accuracy improvement on top of the backtested baseline model.
      </p>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--axis-ink)", fontSize: 11 }}
            axisLine={{ stroke: "var(--grid)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => formatCompactUsd(v)}
            tick={{ fill: "var(--axis-ink)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            content={({ active, label, payload }) => (
              <ChartTooltip active={active} label={label} payload={payload} entries={entries} />
            )}
            cursor={{ stroke: "var(--grid)" }}
          />
          {entries.map(({ movie, history }) => {
            const key = movieKey(movie.tmdb_id);
            const isHighlighted = highlightedId === movie.tmdb_id;
            const isResolved = history?.actual_weekend_gross_usd != null;
            const lastIndex = lastValueIndex(key);
            const beatForecast =
              isResolved && lastIndex >= 0 && history!.actual_weekend_gross_usd! >= (rows[lastIndex][key] as number);

            return (
              <Line
                key={key}
                dataKey={key}
                stroke={isHighlighted ? "var(--highlight-line)" : "var(--muted-line)"}
                strokeWidth={isHighlighted ? 2.5 : 1.5}
                dot={({ cx, cy, index }: DotProps) => {
                  if (index !== lastIndex) return <g key={`${key}-dot-${index}`} />;
                  if (isResolved) {
                    return (
                      <circle
                        key={`${key}-dot-${index}`}
                        cx={cx}
                        cy={cy}
                        r={5}
                        fill={beatForecast ? "var(--resolved-up)" : "var(--resolved-down)"}
                        stroke="#fff"
                        strokeWidth={1.5}
                      />
                    );
                  }
                  return (
                    <circle
                      key={`${key}-dot-${index}`}
                      cx={cx}
                      cy={cy}
                      r={isHighlighted ? 3 : 2}
                      fill={isHighlighted ? "var(--highlight-line)" : "var(--muted-line)"}
                    />
                  );
                }}
                activeDot={{ r: 4 }}
                connectNulls
                isAnimationActive={false}
                onMouseEnter={() => setHighlightedId(movie.tmdb_id)}
                onMouseLeave={() => setHighlightedId(null)}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>

      <div className="flex flex-col gap-1">
        <h3 className="px-2 text-sm font-medium text-zinc-900 dark:text-zinc-50">Projected Rank</h3>
        <p className="px-2 text-xs text-zinc-500 dark:text-zinc-400">
          Films ranked by projected box office performance this weekend - not a confirmed final result until the
          real numbers are reported.
        </p>
        {entries.map(({ movie }, index) => {
          const headline = movie.actual_weekend_gross_usd ?? movie.predicted_weekend_gross_usd;
          const tier = heatTier(headline);
          const poster = posterUrl(movie.poster_path, "w185");
          const isHighlighted = highlightedId === movie.tmdb_id;

          return (
            <div
              key={movie.tmdb_id}
              onMouseEnter={() => setHighlightedId(movie.tmdb_id)}
              onMouseLeave={() => setHighlightedId(null)}
              className={`flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors ${
                isHighlighted ? "bg-zinc-100 dark:bg-zinc-800" : ""
              }`}
            >
              <span className="w-5 shrink-0 text-right text-sm font-semibold tabular-nums text-zinc-400 dark:text-zinc-500">
                {index + 1}
              </span>
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: isHighlighted ? "#2a78d6" : "#c3c2b7" }}
              />
              <div className="relative h-11 w-8 shrink-0 overflow-hidden rounded bg-zinc-200 dark:bg-zinc-800">
                {poster && <Image src={poster} alt={movie.title} fill sizes="32px" className="object-cover" />}
              </div>
              <span className="line-clamp-1 flex-1 text-sm text-zinc-900 dark:text-zinc-50">{movie.title}</span>
              {movie.has_audience_demographics && (
                <span
                  title="Audience demographics reported for this release"
                  className="hidden shrink-0 text-zinc-400 dark:text-zinc-500 sm:inline-flex"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2" />
                    <path d="M6 1a5 5 0 0 1 4.33 7.5L6 6V1z" fill="currentColor" />
                  </svg>
                </span>
              )}
              <span
                className={`hidden rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide sm:inline ${tier.chip}`}
              >
                {tier.label}
              </span>
              <span className="w-20 shrink-0 text-right text-sm font-medium tabular-nums text-zinc-900 dark:text-zinc-50">
                {headline != null ? formatCompactUsd(headline) : "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
