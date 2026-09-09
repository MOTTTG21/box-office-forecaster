"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { MovieDetail } from "@/lib/types";

// Same categorical swatches already used in CompareChart.tsx, for palette consistency app-wide.
const RACE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"];

function GenderAgeBar({ label, leftLabel, leftPct, rightLabel, rightPct }: {
  label: string;
  leftLabel: string;
  leftPct: number;
  rightLabel: string;
  rightPct: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-zinc-500 dark:text-zinc-400">{label}</span>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
        <div className="h-full bg-[#2a78d6] dark:bg-[#3987e5]" style={{ width: `${leftPct}%` }} />
        <div className="h-full bg-[#eb6834] dark:bg-[#d95926]" style={{ width: `${rightPct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-zinc-700 dark:text-zinc-300">
        <span>
          {leftLabel} {leftPct.toFixed(0)}%
        </span>
        <span>
          {rightLabel} {rightPct.toFixed(0)}%
        </span>
      </div>
    </div>
  );
}

export default function AudienceDemographics({ movie }: { movie: MovieDetail }) {
  const hasGender = movie.demographic_percent_female != null && movie.demographic_percent_male != null;
  const hasAge = movie.demographic_percent_under_25 != null && movie.demographic_percent_25_and_over != null;
  const hasRaceBreakdown = !!movie.demographic_race_breakdown && movie.demographic_race_breakdown.length > 0;

  if (!hasGender && !hasAge && !hasRaceBreakdown) return null;

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Opening Weekend Audience</h2>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        Real exit-poll data (PostTrak/CinemaScore) as reported by trade press
        {movie.demographic_source_note && <> &mdash; {movie.demographic_source_note}</>}.
      </p>

      <div className="flex flex-col gap-3 sm:max-w-sm">
        {hasGender && (
          <GenderAgeBar
            label="Gender"
            leftLabel="Female"
            leftPct={movie.demographic_percent_female!}
            rightLabel="Male"
            rightPct={movie.demographic_percent_male!}
          />
        )}
        {hasAge && (
          <GenderAgeBar
            label="Age"
            leftLabel="Under 25"
            leftPct={movie.demographic_percent_under_25!}
            rightLabel="25 and over"
            rightPct={movie.demographic_percent_25_and_over!}
          />
        )}
      </div>

      {hasRaceBreakdown && (
        <div className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">Race / Ethnicity</span>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={movie.demographic_race_breakdown!}
                dataKey="percent"
                nameKey="group"
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                paddingAngle={2}
              >
                {movie.demographic_race_breakdown!.map((entry, index) => (
                  <Cell key={entry.group} fill={RACE_COLORS[index % RACE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${Number(value).toFixed(0)}%`} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
