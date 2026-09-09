import { describe, expect, it } from "vitest";

import { industryYoyChangePct } from "./industryHealth";
import { IndustryWeekPoint } from "./types";

function point(year: number, total_gross_usd: number | null): IndustryWeekPoint {
  return { year, week_start_date: `${year}-09-07`, total_gross_usd };
}

describe("industryYoyChangePct", () => {
  it("returns null with fewer than two data points", () => {
    expect(industryYoyChangePct([point(2026, 1_000_000)])).toBeNull();
    expect(industryYoyChangePct([])).toBeNull();
  });

  it("computes the percent change between the two most recent points with data", () => {
    const points = [point(2024, 80_000_000), point(2025, 100_000_000)];
    expect(industryYoyChangePct(points)).toBeCloseTo(25);
  });

  it("is negative when the industry is down vs. the prior comparable point", () => {
    const points = [point(2024, 100_000_000), point(2025, 80_000_000)];
    expect(industryYoyChangePct(points)).toBeCloseTo(-20);
  });

  it("skips a null point (e.g. the current, not-yet-concluded week) rather than treating it as 0", () => {
    const points = [point(2024, 80_000_000), point(2025, 100_000_000), point(2026, null)];
    // should compare 2025 vs 2024, not 2026 (null) vs 2025
    expect(industryYoyChangePct(points)).toBeCloseTo(25);
  });

  it("skips multiple trailing nulls to find the last two real points", () => {
    const points = [point(2023, 50_000_000), point(2024, 60_000_000), point(2025, null), point(2026, null)];
    expect(industryYoyChangePct(points)).toBeCloseTo(20);
  });

  it("returns null when fewer than two points have real data even if the list is long", () => {
    const points = [point(2022, null), point(2023, null), point(2024, null), point(2025, 100_000_000)];
    expect(industryYoyChangePct(points)).toBeNull();
  });
});
