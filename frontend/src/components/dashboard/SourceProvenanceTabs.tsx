"use client";

import { useState } from "react";

import type { ProvenanceRecord, TraceStep } from "../../types/dashboard";
import { cleanSourceFile } from "../../lib/format";

const PSEUDO_STEPS: Record<string, string[]> = {
  agent_trace: ["trace_id := new_agent_trace()", "audit_log.open(trace_id)"],
  ingest_normalizer: [
    "session := load_session(session_id)",
    "telemetry := fetch_telemetry(session_id)",
    "dtc_rows := fetch_dtc_events(session_id)",
  ],
  sql_deviation: [
    "health := run_health_score(session_id)",
    "baseline := baseline_deviation(session_id)",
    "trim_trend := fuel_trim_trend(session_id)",
  ],
  dtc_interpreter: ["codes := list_dtc_codes(session_id)", "map codes -> sensor windows"],
  baseline_recall: [
    "bands := load_baseline_bands(vehicle_id)",
    "compare telemetry to stored healthy ranges",
  ],
  correlation: [
    "join dtc_events.ts to telemetry_samples",
    "window := +/- 30s around each fault timestamp",
  ],
  recommendation: [
    "rank findings from SQL facts only",
    "emit likely_cause + recommended_fix",
  ],
  report_writer: [
    "INSERT findings (session_id, trace_id, ...)",
    "link UI panels -> trace_id for audit",
  ],
  error: ["RAISE analysis_error", "skip finding write"],
};

type Tab = "source" | "provenance";

type Props = {
  records: ProvenanceRecord[];
  trace: TraceStep[];
  traceId: string;
};

export function SourceProvenanceTabs({ records, trace, traceId }: Props) {
  const [tab, setTab] = useState<Tab>("source");

  return (
    <article className="panel flowIn delayedFive">
      <div className="panelHead tabPanelHead">
        <div className="tabSwitch" role="tablist" aria-label="Data tabs">
          <button
            type="button"
            role="tab"
            className={`tabButton${tab === "source" ? " isActive" : ""}`}
            aria-selected={tab === "source"}
            onClick={() => setTab("source")}
          >
            Source Data
          </button>
          <button
            type="button"
            role="tab"
            className={`tabButton${tab === "provenance" ? " isActive" : ""}`}
            aria-selected={tab === "provenance"}
            onClick={() => setTab("provenance")}
          >
            Provenance
          </button>
        </div>
        <h2>{tab === "source" ? "Source Data" : "Provenance"}</h2>
      </div>

      {tab === "source" ? (
        <div className="provenanceRecords provenanceRecordsCompact" role="tabpanel">
          {records.map((record) => (
            <div className="provenanceRecord" key={`${record.vehicle}-${record.source_file}`}>
              <strong>{record.vehicle}</strong>
              <span className="provenanceEyebrow">{record.drive_label}</span>
              <code>{cleanSourceFile(record.source_file)}</code>
              <span className="licenseTag">{record.license}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="tracePanel" role="tabpanel">
          <p className="traceLead">
            Trace <code>{traceId}</code> — each step maps 1:1 to SQL and agent nodes in the
            pipeline.
          </p>
          <ol className="traceRoute">
            {trace.map((step, index) => {
              const pseudo = PSEUDO_STEPS[step.node] ?? [`run ${step.node}(session_id)`];
              return (
                <li key={`${step.node}-${index}`}>
                  <div className="traceStepHead">
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{step.agent_name ?? step.agent}</strong>
                    <code>{step.node}</code>
                  </div>
                  <p className="traceStepBody">{step.body ?? step.summary}</p>
                  <pre className="tracePseudo">
                    {pseudo.map((line) => (
                      <span key={line}>{line}</span>
                    ))}
                  </pre>
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </article>
  );
}
