"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";

import { PredictionHistory } from "@/lib/types";

export default function PredictionSparkline({ history }: { history: PredictionHistory | null }) {
  if (!history || history.snapshots.length < 2) return null;

  const points = history.snapshots.map((s) => ({ value: s.predicted_weekend_gross_usd }));

  return (
    <div className="h-6 w-16 shrink-0 [--spark:#2a78d6] dark:[--spark:#3987e5]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--spark)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
