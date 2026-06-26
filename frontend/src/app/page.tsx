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
  title?: string;
  body?: string;
  agent_name?: string;
  agent_tagline?: string;
};

type GuideBlock = {
  title: string;
  body: string;
};

type ProvenanceRecord = {
  vehicle: string;
  drive_label: string;
  source_file: string;
  license: string;
  dataset_name: string;
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
  agents: Record<string, { name: string; tagline: string; role: string }>;
  disclaimer: string;
  healthGuide: GuideBlock;
  trendGuide: GuideBlock;
  faultGuide: GuideBlock;
  method: string[];
  workflow: Array<{ label: string; body: string }>;
  readOrder: string[];
  dataSource: {
    summary: string;
    sources: Array<{
      name: string;
      license: string;
      licenseUrl: string;
      url: string;
    }>;
    entries: string[];
    note: string;
    records: ProvenanceRecord[];
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
const huginnSteps = dashboard.agentTrace.filter((step) => step.agent === "huginn");
const muninnSteps = dashboard.agentTrace.filter((step) => step.agent === "muninn");

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
              {dashboard.dataSource.sources.map((source, index) => (
                <span key={source.name}>
                  {index > 0 ? " / " : "Data: "}
                  <a href={source.url}>{source.name}</a>
                  {" "}
                  <a href={source.licenseUrl}>{source.license}</a>
                </span>
              ))}
            </p>
            <p className="sourceDetail">{dashboard.dataSource.summary}</p>
          </div>
          <figure className="inspirationPlate" aria-label={dashboard.inspiration.label}>
            <img src={dashboard.inspiration.image} alt={dashboard.inspiration.label} />
            <figcaption>{dashboard.inspiration.label}</figcaption>
          </figure>
        </section>

        <section className="grid twoCol">
          <article className="panel scorePanel flowIn delayedOne">
            <div className="panelHead">
              <p>{dashboard.healthGuide.title}</p>
              <h2>{dashboard.focus.vehicle}</h2>
            </div>
            <div
              className="scoreRing"
              style={{ "--score-width": dashboard.focus.health_score_width } as Vars}
              aria-label={`Drive health ${dashboard.focus.health_score}`}
            >
              <span>{dashboard.focus.health_score}</span>
            </div>
            <p className="guideCopy">{dashboard.healthGuide.body}</p>
            <div className="meterBlock">
              <div className="meterLabel">
                <span>{dashboard.focus.drive_label}</span>
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
                <dt>Data points</dt>
                <dd>{dashboard.focus.telemetry_samples}</dd>
              </div>
              <div>
                <dt>Fault codes</dt>
                <dd>{dashboard.focus.dtc_count}</dd>
              </div>
              <div>
                <dt>Drive type</dt>
                <dd>{dashboard.focus.drive_label}</dd>
              </div>
              <div>
                <dt>Source file</dt>
                <dd className="factFile">{dashboard.focus.source_file}</dd>
              </div>
            </dl>
          </article>

          <article className="panel sessionsPanel flowIn delayedTwo">
            <div className="panelHead">
              <p>Three real cars</p>
              <h2>Pick a drive</h2>
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
              <p>{dashboard.trendGuide.title}</p>
              <h2>Over this drive</h2>
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
            <p className="guideCopy">{dashboard.trendGuide.body}</p>
            <p className="microCopy">
              Last rolling average: {dashboard.trend.at(-1)?.maf_30s} g/s
            </p>
          </article>

          <article className="panel flowIn delayedFour">
            <div className="panelHead">
              <p>{dashboard.faultGuide.title}</p>
              <h2>{hasDiagnosticRows ? diagnosticCode?.code : "None logged"}</h2>
            </div>
            {hasDiagnosticRows ? (
              <div
                className="evidenceTable"
                role="table"
                aria-label="Fault code sensor window"
              >
                <div className="tableRow tableHead" role="row">
                  <span role="columnheader">RPM</span>
                  <span role="columnheader">Load</span>
                  <span role="columnheader">Coolant</span>
                  <span role="columnheader">Status</span>
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
                <strong>No fault code in this file</strong>
                <p>{diagnosticCode?.description}</p>
              </div>
            )}
            <p className="guideCopy">{dashboard.faultGuide.body}</p>
          </article>
        </section>

        <section className="grid twoCol">
          <article className="panel agentPanel flowIn delayedFive">
            <div className="panelHead">
              <p>{dashboard.agents.huginn.tagline}</p>
              <h2>{dashboard.agents.huginn.name}</h2>
            </div>
            <p className="agentRole">{dashboard.agents.huginn.role}</p>
            <ol className="agentSteps">
              {huginnSteps.map((step) => (
                <li key={`${step.node}-${step.summary}`}>
                  <strong>{step.title ?? step.node}</strong>
                  <p>{step.body ?? step.summary}</p>
                </li>
              ))}
            </ol>
          </article>

          <article className="panel agentPanel flowIn delayedFive">
            <div className="panelHead">
              <p>{dashboard.agents.muninn.tagline}</p>
              <h2>{dashboard.agents.muninn.name}</h2>
            </div>
            <p className="agentRole">{dashboard.agents.muninn.role}</p>
            <ol className="agentSteps">
              {muninnSteps.map((step) => (
                <li key={`${step.node}-${step.summary}`}>
                  <strong>{step.title ?? step.node}</strong>
                  <p>{step.body ?? step.summary}</p>
                </li>
              ))}
            </ol>
          </article>
        </section>

        <section className="grid twoCol">
          <article className="panel flowIn delayedSix">
            <div className="panelHead">
              <p>How to read this page</p>
              <h2>Read order</h2>
            </div>
            <ol className="readOrderList">
              {dashboard.readOrder.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
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
              <p>Where this data came from</p>
              <h2>Provenance</h2>
            </div>
            <p className="guideCopy">{dashboard.dataSource.note}</p>
            <div className="provenanceRecords">
              {dashboard.dataSource.records.map((record) => (
                <div className="provenanceRecord" key={`${record.vehicle}-${record.source_file}`}>
                  <strong>{record.vehicle}</strong>
                  <span>{record.drive_label}</span>
                  <small>{record.dataset_name}</small>
                  <code>{record.source_file}</code>
                  <span className="licenseTag">{record.license}</span>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="panel flowIn delayedSix">
          <div className="panelHead">
            <p>Audit</p>
            <h2>What SQL and the ravens did</h2>
          </div>
          <ul className="methodList">
            {dashboard.method.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="finding">
            <strong>{dashboard.finding.likely_cause}</strong>
            <p>{dashboard.finding.recommended_fix}</p>
            <p className="traceId">Trace id: {dashboard.agentTraceId}</p>
          </div>
        </section>

        <footer className="footer flowIn delayedSix">
          <span>{dashboard.disclaimer}</span>
        </footer>
      </main>
    </>
  );
}
