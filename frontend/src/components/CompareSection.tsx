"use client";

import { useState } from "react";

import { ComparisonSeries } from "@/lib/types";

import CompareChart from "./CompareChart";

export default function CompareSection({
  franchise,
  year,
}: {
  franchise: ComparisonSeries[];
  year: ComparisonSeries[];
}) {
  const [mode, setMode] = useState<"franchise" | "year">(franchise.length > 0 ? "franchise" : "year");

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Compare</h2>
        <div className="flex gap-1 rounded-md border border-zinc-200 p-0.5 text-sm dark:border-zinc-800">
          <button
            type="button"
            onClick={() => setMode("franchise")}
            className={`rounded px-3 py-1 ${
              mode === "franchise"
                ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                : "text-zinc-600 dark:text-zinc-400"
            }`}
          >
            Franchise
          </button>
          <button
            type="button"
            onClick={() => setMode("year")}
            className={`rounded px-3 py-1 ${
              mode === "year"
                ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                : "text-zinc-600 dark:text-zinc-400"
            }`}
          >
            Same Year
          </button>
        </div>
      </div>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        {mode === "franchise"
          ? "Cumulative gross vs. weeks in release, compared against other films in this franchise."
          : "Compared against other films released the same year that have already been looked up in this app — this list grows as more movies get searched."}
      </p>
      <CompareChart series={mode === "franchise" ? franchise : year} />
    </div>
  );
}
