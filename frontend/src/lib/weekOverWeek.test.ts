import { describe, expect, it } from "vitest";

import { weekOverWeekColor } from "./weekOverWeek";
import { WeeklyGrossPoint } from "./types";

function point(week_number: number, weekend_gross_usd: number | null): WeeklyGrossPoint {
  return { week_number, weekend_gross_usd, week_start_date: null, cumulative_gross_usd: null, theater_count: null, rank: null };
}

describe("weekOverWeekColor", () => {
  it("uses the neutral series color for week 1 (no prior weekend)", () => {
    const data = [point(1, 82_455_420), point(2, 46_705_630)];
    expect(weekOverWeekColor(data, 0)).toBe("var(--series)");
  });

  it("is green when the weekend grosses more than the prior one", () => {
    const data = [point(1, 10_000_000), point(2, 12_000_000)];
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-up)");
  });

  it("is yellow for a mild drop under 40%", () => {
    const data = [point(1, 10_000_000), point(2, 7_000_000)]; // -30%
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-mild)");
  });

  it("is orange for a steep drop between 40% and 60%", () => {
    const data = [point(1, 10_000_000), point(2, 5_000_000)]; // -50%
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-steep)");
  });

  it("is red for a severe drop over 60%", () => {
    const data = [point(1, 10_000_000), point(2, 3_000_000)]; // -70%
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-severe)");
  });

  it("boundary: exactly -40% is steep (orange), not mild", () => {
    const data = [point(1, 10_000_000), point(2, 6_000_000)]; // -40% exactly
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-steep)");
  });

  it("boundary: exactly -60% is steep (orange), not severe", () => {
    const data = [point(1, 10_000_000), point(2, 4_000_000)]; // -60% exactly
    expect(weekOverWeekColor(data, 1)).toBe("var(--wow-steep)");
  });

  it("falls back to the neutral color when data is missing", () => {
    const data = [point(1, 10_000_000), point(2, null)];
    expect(weekOverWeekColor(data, 1)).toBe("var(--series)");
  });
});
