type ProfitabilityStatus = "bomb" | "flop" | "success";

const STATUS_STYLE: Record<ProfitabilityStatus, { label: string; bg: string; text: string }> = {
  bomb: { label: "Bomb", bg: "#d03b3b", text: "#ffffff" },
  flop: { label: "Flop", bg: "#fab219", text: "#0b0b0b" },
  success: { label: "Financial Success", bg: "#0ca30c", text: "#ffffff" },
};

// A still-in-theaters bomb/flop reading isn't final yet - a film could still climb out
// of it with more weeks of exhibition or an international rollout. A "success" reading
// needs no such hedge: worldwide gross has already cleared the profitability bar.
const STILL_IN_THEATERS_WINDOW_DAYS = 70;

function isLikelyStillInTheaters(releaseDate: string | null, movieStatus: string): boolean {
  if (movieStatus !== "released" || !releaseDate) return false;
  const daysSinceRelease = (Date.now() - new Date(releaseDate).getTime()) / 86_400_000;
  return daysSinceRelease <= STILL_IN_THEATERS_WINDOW_DAYS;
}

export default function ProfitabilityBanner({
  status,
  releaseDate,
  movieStatus,
}: {
  status: ProfitabilityStatus | null;
  releaseDate: string | null;
  movieStatus: string;
}) {
  if (!status) return null;
  const { label: baseLabel, bg, text } = STATUS_STYLE[status];
  const showPotential = status !== "success" && isLikelyStillInTheaters(releaseDate, movieStatus);
  const label = showPotential ? `Potential ${baseLabel}` : baseLabel;

  return (
    <div className="pointer-events-none absolute top-0 left-0 h-24 w-24 overflow-hidden rounded-tl-lg">
      <div
        className="absolute top-[22px] -left-[32px] w-[150px] -rotate-45 py-1 text-center text-[10px] font-semibold uppercase tracking-wide shadow-md"
        style={{ backgroundColor: bg, color: text }}
      >
        {label}
      </div>
    </div>
  );
}
