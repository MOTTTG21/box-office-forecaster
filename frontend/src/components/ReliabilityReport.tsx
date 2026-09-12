import { ReliabilityReport as ReliabilityReportData } from "@/lib/types";

const SERVICE_LABELS: Record<string, string> = {
  tmdb: "TMDB",
  omdb: "OMDb",
  box_office_mojo: "Box Office Mojo",
  yahoo_finance: "Yahoo Finance",
};

export default function ReliabilityReport({ report }: { report: ReliabilityReportData }) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">External Service Reliability</h2>
      <p className="max-w-2xl text-xs text-zinc-500 dark:text-zinc-400">
        Every external host this app depends on (TMDB, OMDb, Box Office Mojo, Yahoo Finance) sits behind a
        circuit breaker: after {report.services[0]?.failure_threshold ?? 3} consecutive real failures it trips
        open and fails fast for 60 seconds instead of letting requests pile up waiting on a host that&apos;s
        actually down, then automatically tries again. This reflects real state from this process, not a
        simulated demo.
      </p>
      <div className="flex flex-wrap gap-3">
        {report.services.map((service) => (
          <div
            key={service.name}
            className={`flex flex-col gap-1 rounded-lg border px-3 py-2 text-xs ${
              service.state === "open"
                ? "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/40"
                : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span
                className={`h-2 w-2 rounded-full ${service.state === "open" ? "bg-red-500" : "bg-[#0ca30c]"}`}
              />
              <span className="font-medium text-zinc-900 dark:text-zinc-50">
                {SERVICE_LABELS[service.name] ?? service.name}
              </span>
            </div>
            <span className="text-zinc-500 dark:text-zinc-400">
              {service.state === "open" ? "Open — failing fast" : "Closed — healthy"}
            </span>
            {service.total_trips > 0 && (
              <span className="text-zinc-400 dark:text-zinc-500">{service.total_trips} trip(s) this run</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
