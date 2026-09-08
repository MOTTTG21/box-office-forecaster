type ProfitabilityStatus = "bomb" | "flop" | "success";

const STATUS_STYLE: Record<ProfitabilityStatus, { label: string; bg: string; text: string }> = {
  bomb: { label: "Bomb", bg: "#d03b3b", text: "#ffffff" },
  flop: { label: "Flop", bg: "#fab219", text: "#0b0b0b" },
  success: { label: "Financial Success", bg: "#0ca30c", text: "#ffffff" },
};

export default function ProfitabilityBanner({ status }: { status: ProfitabilityStatus | null }) {
  if (!status) return null;
  const { label, bg, text } = STATUS_STYLE[status];

  return (
    <div
      className="pointer-events-none absolute top-3 -left-9 w-32 -rotate-45 py-1 text-center text-[11px] font-semibold uppercase tracking-wide shadow-md"
      style={{ backgroundColor: bg, color: text }}
    >
      {label}
    </div>
  );
}
