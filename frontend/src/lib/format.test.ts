import { describe, expect, it } from "vitest";

import { formatCompactUsd, formatUsd } from "./format";

describe("formatUsd", () => {
  it("formats a whole dollar amount with no decimals", () => {
    expect(formatUsd(975_811_333)).toBe("$975,811,333");
  });

  it("returns 'Unknown' for null", () => {
    expect(formatUsd(null)).toBe("Unknown");
  });

  it("formats zero as a real currency value, not 'Unknown'", () => {
    // zero is a legitimate (if unusual) amount - only null means "we don't have this"
    expect(formatUsd(0)).toBe("$0");
  });
});

describe("formatCompactUsd", () => {
  it("compacts millions with one decimal", () => {
    expect(formatCompactUsd(82_455_420)).toBe("$82.5M");
  });

  it("compacts billions", () => {
    expect(formatCompactUsd(1_200_000_000)).toBe("$1.2B");
  });

  it("compacts thousands", () => {
    expect(formatCompactUsd(65_942)).toBe("$65.9K");
  });
});
