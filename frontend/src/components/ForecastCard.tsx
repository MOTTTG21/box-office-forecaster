import Image from "next/image";
import Link from "next/link";

import { posterUrl } from "@/lib/api";
import { formatCompactUsd } from "@/lib/format";
import { ThisWeekMovie } from "@/lib/types";

const HEAT_TIERS = [
  { max: 5_000_000, label: "Light", chip: "bg-[#2a78d6]/15 text-[#2a78d6] dark:bg-[#3987e5]/20 dark:text-[#6da7ec]" },
  { max: 30_000_000, label: "Moderate", chip: "bg-zinc-500/15 text-zinc-600 dark:bg-zinc-400/20 dark:text-zinc-300" },
  { max: 80_000_000, label: "Hot", chip: "bg-[#eb6834]/15 text-[#eb6834] dark:bg-[#d95926]/20 dark:text-[#f0955f]" },
  { max: Infinity, label: "Blockbuster", chip: "bg-[#e34948]/15 text-[#e34948] dark:bg-[#e66767]/20 dark:text-[#ef8a89]" },
];

function heatTier(amount: number | null) {
  if (amount == null) return HEAT_TIERS[1];
  return HEAT_TIERS.find((tier) => amount <= tier.max) ?? HEAT_TIERS[HEAT_TIERS.length - 1];
}

function dayLabel(dateStr: string | null): { weekday: string; date: string } {
  if (!dateStr) return { weekday: "TBA", date: "" };
  const d = new Date(`${dateStr}T00:00:00`);
  return {
    weekday: d.toLocaleDateString("en-US", { weekday: "short" }).toUpperCase(),
    date: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  };
}

export default function ForecastCard({ movie }: { movie: ThisWeekMovie }) {
  const poster = posterUrl(movie.poster_path, "w185");
  const { weekday, date } = dayLabel(movie.release_date);

  const headline = movie.actual_opening_weekend_usd ?? movie.predicted_opening_weekend_usd;
  const tier = heatTier(headline);

  const hasDelta = movie.actual_opening_weekend_usd != null && movie.predicted_opening_weekend_usd != null;
  const beatPrediction =
    hasDelta && movie.actual_opening_weekend_usd! >= movie.predicted_opening_weekend_usd! * 1.05;
  const missedPrediction =
    hasDelta && movie.actual_opening_weekend_usd! <= movie.predicted_opening_weekend_usd! * 0.95;

  return (
    <Link
      href={`/movies/${movie.tmdb_id}`}
      className="flex flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white transition-shadow hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="flex items-center justify-between px-4 pt-3">
        <span className="text-xs font-semibold tracking-wide text-zinc-500 dark:text-zinc-400">
          {weekday} <span className="font-normal">{date}</span>
        </span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tier.chip}`}>
          {tier.label}
        </span>
      </div>

      <div className="flex items-center gap-3 px-4 py-3">
        <div className="relative h-16 w-11 shrink-0 overflow-hidden rounded bg-zinc-200 dark:bg-zinc-800">
          {poster && <Image src={poster} alt={movie.title} fill sizes="44px" className="object-cover" />}
        </div>
        <div className="flex flex-1 flex-col">
          <span className="line-clamp-1 text-sm font-medium text-zinc-900 dark:text-zinc-50">{movie.title}</span>
          <span className="text-3xl font-semibold tabular-nums text-zinc-900 dark:text-zinc-50">
            {headline != null ? formatCompactUsd(headline) : "—"}
          </span>
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {movie.actual_opening_weekend_usd != null ? "Actual opening" : "Forecast opening"}
          </span>
        </div>
      </div>

      {hasDelta && (
        <div className="flex items-center gap-1.5 border-t border-zinc-100 px-4 py-2 text-xs dark:border-zinc-800">
          <span
            className={
              beatPrediction
                ? "text-[#0ca30c]"
                : missedPrediction
                  ? "text-[#d03b3b]"
                  : "text-zinc-500 dark:text-zinc-400"
            }
          >
            {beatPrediction ? "▲" : missedPrediction ? "▼" : "≈"} vs. forecast of{" "}
            {formatCompactUsd(movie.predicted_opening_weekend_usd!)}
          </span>
        </div>
      )}
    </Link>
  );
}
