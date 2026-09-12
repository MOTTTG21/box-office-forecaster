import { LatencyReport as LatencyReportData } from "@/lib/types";

export default function LatencyReport({ report }: { report: LatencyReportData }) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">API Latency</h2>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        Real timing recorded on every request over the last {report.retention_days} days, not a synthetic
        benchmark. A route needs at least {report.min_samples} samples in that window before it&apos;s shown here
        at all &mdash; a percentile from a couple of requests would look precise without meaning anything.
      </p>
      {report.endpoints.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Not enough traffic yet to report latency.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-left text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
                <th className="py-2 pr-4 font-medium">Endpoint</th>
                <th className="py-2 pr-4 font-medium">Samples</th>
                <th className="py-2 pr-4 font-medium">P50</th>
                <th className="py-2 pr-4 font-medium">P95</th>
                <th className="py-2 pr-4 font-medium">P99</th>
              </tr>
            </thead>
            <tbody>
              {report.endpoints.map((endpoint) => (
                <tr
                  key={`${endpoint.method}-${endpoint.route_template}`}
                  className="border-b border-zinc-100 last:border-0 dark:border-zinc-900"
                >
                  <td className="py-2 pr-4 font-mono text-xs text-zinc-900 dark:text-zinc-50">
                    <span className="text-zinc-400 dark:text-zinc-500">{endpoint.method}</span>{" "}
                    {endpoint.route_template}
                  </td>
                  <td className="py-2 pr-4 tabular-nums text-zinc-500 dark:text-zinc-400">
                    {endpoint.sample_count}
                  </td>
                  <td className="py-2 pr-4 tabular-nums text-zinc-700 dark:text-zinc-300">{endpoint.p50_ms} ms</td>
                  <td className="py-2 pr-4 tabular-nums text-zinc-700 dark:text-zinc-300">{endpoint.p95_ms} ms</td>
                  <td className="py-2 pr-4 tabular-nums font-medium text-zinc-900 dark:text-zinc-50">
                    {endpoint.p99_ms} ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
