import { WeeklyGrossPoint } from "./types";

// Week-over-week change vs. the prior weekend: up -> green, a mild drop (<40%) -> yellow,
// a steep drop (40-60%) -> orange, a severe drop (>60%) -> red. Week 1 has no prior
// weekend to compare against, so it stays the neutral series color.
export function weekOverWeekColor(data: WeeklyGrossPoint[], index: number): string {
  const current = data[index].weekend_gross_usd;
  const previous = index > 0 ? data[index - 1].weekend_gross_usd : null;
  if (current == null || !previous) return "var(--series)";

  const change = (current - previous) / previous;
  if (change >= 0) return "var(--wow-up)";
  if (change > -0.4) return "var(--wow-mild)";
  if (change >= -0.6) return "var(--wow-steep)";
  return "var(--wow-severe)";
}
