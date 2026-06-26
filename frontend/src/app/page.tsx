import type { CSSProperties } from "react";

import { ConstellationField } from "../components/ConstellationField";
import dashboardData from "../data/dashboard.json";

type SessionRow = {
  session_id: number;
  vehicle: string;
  source: string;
  notes: string;
  source_file: string;
  drive_label: string;
  health_score: string;
  health_score_width: string;
  telemetry_samples: string;
  dtc_count: string;
  pct_out_of_range: string;
  baseline_width: string;
};

type TrendRow = {
  ts: string;
  maf_gps: string;
  maf_30s: string;
  height_pct: string;
};

type DtcRow = {
  code: string;
  status: string;
  description: string;
  ts: string;
  rpm: string;
  engine_load_pct: string;
  coolant_temp_c: string;
};

type TraceStep = {
  agent: string;
  node: string;
  kind: string;
  summary: string;
};

type DashboardData = {
  version: string;
  statement: string;
  focus: SessionRow & {
    started_at: string;
    ended_at: string;
    metric_penalty_points: string;
    dtc_penalty_points: string;
    score_basis: string;
    out_of_range_samples: string;
    sample_count: string;
  };
  sessions: SessionRow[];
  trend: TrendRow[];
  dtcEvidence: DtcRow[];
  finding: {
    likely_cause: string;
    recommended_fix: string;
    expected_range: string;
    agent_trace_id: string;
  };
  agentTrace: TraceStep[];
  agentTraceId: string;
  disclaimer: string;
  method: string[];
  workflow: Array<{
    label: string;
    body: string;
  }>;
  dataSource: {
    name: string;
    vehicle: string;
    entries: string[];
    note: string;
    doi: string;
    license: string;
    licenseUrl: string;
  };
  inspiration: {
    label: string;
    image: string;
  };
};

type Vars = CSSProperties & {
  "--score-width"?: string;
  "--baseline-width"?: string;
  "--bar-height"?: string;
};

const dashboard = dashboardData as DashboardData;
const diagnosticCode = dashboard.dtcEvidence[0];
const hasDiagnosticRows = diagnosticCode?.status !== "none";

export default function Home() {
  return (
    <>
      <ConstellationField />
      <main className="dashboard" aria-label="Corvus dashboard">
      <section className="heroSurface flowIn" aria-labelledby="corvus-title">
        <div className="heroCopy">
          <div className="topLine">
            <span>{dashboard.version}</span>
            <span>real public telemetry</span>
          </div>
          <h1 id="corvus-title" className="wordmark" data-text="corvus">
            corvus
          </h1>
          <p className="statement">{dashboard.statement}</p>
          <p className="sourceLine">
            Data:{" "}
            <a href={dashboard.dataSource.doi}>{dashboard.dataSource.name}</a>
            {" / "}
            <a href={dashboard.dataSource.licenseUrl}>{dashboard.dataSource.license}</a>
          </p>
          <p className="sourceDetail">
            Public dashboard rows use real {dashboard.dataSource.vehicle} drive entries from
            the KIT/RADAR archive.
          </p>
        </div>
        <figure className="inspirationPlate" aria-label={dashboard.inspiration.label}>
          <img src={dashboard.inspiration.image} alt={dashboard.inspiration.label} />
          <figcaption>{dashboard.inspiration.label}</figcaption>
        </figure>
      </section>

      <section className="grid twoCol">
        <article className="panel scorePanel flowIn delayedOne">
          <div className="panelHead">
            <p>Focus session</p>
            <h2>Session {dashboard.focus.session_id}</h2>
          </div>
          <div
            className="scoreRing"
            style={{ "--score-width": dashboard.focus.health_score_width } as Vars}
            aria-label={`Health score ${dashboard.focus.health_score}`}
          >
            <span>{dashboard.focus.health_score}</span>
          </div>
          <div className="meterBlock">
            <div className="meterLabel">
              <span>{dashboard.focus.score_basis}</span>
              <span>{dashboard.focus.health_score_width}</span>
            </div>
            <div className="meterTrack">
              <span
                className="meterFill"
                style={{ "--score-width": dashboard.focus.health_score_width } as Vars}
              />
            </div>
          </div>
          <dl className="factGrid">
            <div>
              <dt>Vehicle</dt>
              <dd>{dashboard.focus.vehicle}</dd>
            </div>
            <div>
              <dt>Drive</dt>
              <dd>{dashboard.focus.drive_label}</dd>
            </div>
            <div>
              <dt>Samples</dt>
              <dd>{dashboard.focus.telemetry_samples}</dd>
            </div>
            <div>
              <dt>Code rows</dt>
              <dd>{dashboard.focus.dtc_count}</dd>
            </div>
          </dl>
        </article>

        <article className="panel sessionsPanel flowIn delayedTwo">
          <div className="panelHead">
            <p>Real entries</p>
            <h2>Drive set</h2>
          </div>
          <div className="sessionList">
            {dashboard.sessions.map((session) => (
              <div className="sessionRow" key={session.session_id}>
                <div>
                  <span>{session.drive_label}</span>
                  <strong>{session.vehicle}</strong>
                  <small>{session.source_file}</small>
                </div>
                <div className="miniMeters">
                  <span>{session.health_score}</span>
                  <div className="meterTrack">
                    <span
                      className="meterFill"
                      style={{ "--score-width": session.health_score_width } as Vars}
                    />
                  </div>
                  <small>{session.telemetry_samples} rows</small>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid twoCol evidenceGrid">
        <article className="panel flowIn delayedThree">
          <div className="panelHead">
            <p>Mass air flow</p>
            <h2>Rolling trend</h2>
          </div>
          <div className="barChart" aria-label="Mass air flow rolling trend">
            {dashboard.trend.map((point) => (
              <span
                key={point.ts}
                className="bar"
                title={`${point.ts}: ${point.maf_30s} g/s`}
                style={{ "--bar-height": point.height_pct } as Vars}
              />
            ))}
          </div>
          <p className="microCopy">
            SQL window over logged mass air flow rows. Current focus ends at{" "}
            {dashboard.trend.at(-1)?.maf_30s} g/s.
          </p>
        </article>

        <article className="panel flowIn delayedFour">
          <div className="panelHead">
            <p>Diagnostic code</p>
            <h2>{hasDiagnosticRows ? diagnosticCode?.code : "None logged"}</h2>
          </div>
          {hasDiagnosticRows ? (
            <div
              className="evidenceTable"
              role="table"
              aria-label="Diagnostic trouble code telemetry window"
            >
              <div className="tableRow tableHead" role="row">
                <span role="columnheader">rpm</span>
                <span role="columnheader">load</span>
                <span role="columnheader">coolant</span>
                <span role="columnheader">status</span>
              </div>
              {dashboard.dtcEvidence.map((row) => (
                <div className="tableRow" role="row" key={row.ts}>
                  <span role="cell">{row.rpm}</span>
                  <span role="cell">{row.engine_load_pct}</span>
                  <span role="cell">{row.coolant_temp_c}</span>
                  <span role="cell">{row.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="emptyEvidence">
              <strong>No diagnostic trouble code rows</strong>
              <p>{diagnosticCode?.description}</p>
            </div>
          )}
          {hasDiagnosticRows ? <p className="microCopy">{diagnosticCode?.description}</p> : null}
        </article>
      </section>

      <section className="grid twoCol">
        <article className="panel flowIn delayedFive">
          <div className="panelHead">
            <p>Workflow</p>
            <h2>Read order</h2>
          </div>
          <ol className="workflowList">
            {dashboard.workflow.map((step) => (
              <li key={step.label}>
                <span>{step.label}</span>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>
        </article>

        <article className="panel flowIn delayedSix">
          <div className="panelHead">
            <p>Source</p>
            <h2>Provenance</h2>
          </div>
          <div className="provenanceBlock">
            <strong>{dashboard.dataSource.name}</strong>
            <p>{dashboard.dataSource.note}</p>
            <ul>
              {dashboard.dataSource.entries.map((entry) => (
                <li key={entry}>{entry}</li>
              ))}
            </ul>
          </div>
        </article>
      </section>

      <section className="grid twoCol">
        <article className="panel flowIn delayedFive">
          <div className="panelHead">
            <p>Huginn / Muninn</p>
            <h2>Agent trace</h2>
          </div>
          <p className="traceId">{dashboard.agentTraceId}</p>
          <ol className="traceList">
            {dashboard.agentTrace.map((step) => (
              <li key={`${step.agent}-${step.node}`}>
                <span>{step.agent}</span>
                <strong>{step.node}</strong>
                <small>{step.kind}</small>
              </li>
            ))}
          </ol>
        </article>

        <article className="panel flowIn delayedSix">
          <div className="panelHead">
            <p>Method</p>
            <h2>Evidence path</h2>
          </div>
          <ul className="methodList">
            {dashboard.method.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="finding">
            <strong>{dashboard.finding.expected_range}</strong>
            <p>{dashboard.finding.likely_cause}</p>
            <p>{dashboard.finding.recommended_fix}</p>
          </div>
        </article>
      </section>

      <footer className="footer flowIn delayedSix">
        <span>{dashboard.disclaimer}</span>
      </footer>
      </main>
    </>
  );
}
