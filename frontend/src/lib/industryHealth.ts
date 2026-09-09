import { IndustryWeekPoint } from "./types";

// Percent change between the two most recent points that both actually have data - skips over
// null points (e.g. the current, not-yet-concluded week) rather than treating a missing value
// as 0, which would read as a real industry collapse instead of just missing data.
export function industryYoyChangePct(points: IndustryWeekPoint[]): number | null {
  const withData = points.filter((p) => p.total_gross_usd != null);
  if (withData.length < 2) return null;

  const latest = withData[withData.length - 1];
  const previous = withData[withData.length - 2];
  return ((latest.total_gross_usd! - previous.total_gross_usd!) / previous.total_gross_usd!) * 100;
}
