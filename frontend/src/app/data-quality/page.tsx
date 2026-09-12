import Image from "next/image";
import Link from "next/link";

import LatencyReportSection from "@/components/LatencyReport";
import ReliabilityReportSection from "@/components/ReliabilityReport";
import { getDataAnomalies, getLatencyReport, getReliabilityReport, posterUrl } from "@/lib/api";
import { DataAnomaly, LatencyReport, ReliabilityReport } from "@/lib/types";

const SEVERITY_STYLES: Record<DataAnomaly["severity"], string> = {
  high: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  medium: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

function humanizeRuleName(ruleName: string): string {
  return ruleName.charAt(0).toUpperCase() + ruleName.slice(1).replace(/_/g, " ");
}

export default async function DataQualityPage() {
  let anomalies: DataAnomaly[] = [];
  let loadError = false;
  try {
    anomalies = await getDataAnomalies();
  } catch {
    loadError = true;
  }

  let latencyReport: LatencyReport | null = null;
  try {
    latencyReport = await getLatencyReport();
  } catch {
    latencyReport = null;
  }

  let reliabilityReport: ReliabilityReport | null = null;
  try {
    reliabilityReport = await getReliabilityReport();
  } catch {
    reliabilityReport = null;
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Data Quality</h1>
          <p className="max-w-xl text-sm text-zinc-600 dark:text-zinc-400">
            A set of deterministic rules scans every movie in the database for numeric contradictions (e.g.
            domestic gross exceeding worldwide gross) and statistical outliers (a budget-to-gross ratio wildly out
            of line with genre peers). Claude then writes a one-sentence, plain-English explanation of each flag —
            it only explains a contradiction the rules already found; it never originates or corrects a fact
            itself. Nothing here is auto-corrected — this page exists so bad data gets surfaced, not silently fixed.
          </p>
        </div>

        {loadError && (
          <p className="text-sm text-red-600 dark:text-red-400">
            Couldn&apos;t load the data quality report. Is the backend running?
          </p>
        )}

        {!loadError && anomalies.length === 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No anomalies currently flagged across the movies in the database.
          </p>
        )}

        <div className="flex flex-col gap-4">
          {anomalies.map((anomaly) => {
            const poster = posterUrl(anomaly.poster_path, "w185");
            return (
              <div
                key={`${anomaly.tmdb_id}-${anomaly.rule_name}`}
                className="flex gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <Link href={`/movies/${anomaly.tmdb_id}`} className="relative h-24 w-16 shrink-0 overflow-hidden rounded-md bg-zinc-100 dark:bg-zinc-800">
                  {poster && <Image src={poster} alt={anomaly.title} fill sizes="64px" className="object-cover" />}
                </Link>
                <div className="flex flex-1 flex-col gap-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link href={`/movies/${anomaly.tmdb_id}`} className="text-sm font-medium text-zinc-900 hover:underline dark:text-zinc-50">
                      {anomaly.title}
                    </Link>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[anomaly.severity]}`}>
                      {anomaly.severity}
                    </span>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">{humanizeRuleName(anomaly.rule_name)}</span>
                  </div>
                  <p className="text-xs text-zinc-600 dark:text-zinc-400">{anomaly.detail}</p>
                  {anomaly.ai_explanation && (
                    <p className="text-xs italic text-zinc-500 dark:text-zinc-500">
                      <span className="font-medium not-italic">Claude:</span> {anomaly.ai_explanation}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {(reliabilityReport || latencyReport) && (
          <div className="flex flex-col gap-6 border-t border-zinc-200 pt-6 dark:border-zinc-800">
            {reliabilityReport && <ReliabilityReportSection report={reliabilityReport} />}
            {latencyReport && <LatencyReportSection report={latencyReport} />}
          </div>
        )}
      </div>
    </div>
  );
}
