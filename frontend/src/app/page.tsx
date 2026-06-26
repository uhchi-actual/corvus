import type { CSSProperties } from "react";

import dashboardData from "../data/dashboard.json";

type SessionRow = {
  session_id: number;
  vehicle: string;
  source: string;
  health_score: string;
  health_score_width: string;
  telemetry_samples: string;
  dtc_count: string;
  pct_out_of_range: string;
  baseline_width: string;
};

type DriftRow = {
  ts: string;
  ltft_b1_pct: string;
  ltft_30s: string;
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
  drift: DriftRow[];
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
  dataSource: {
    name: string;
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

export default function Home() {
  return (
    <main className="dashboard" aria-label="Corvus dashboard">
      <section className="heroSurface flowIn" aria-labelledby="corvus-title">
        <div className="heroCopy">
          <div className="topLine">
            <span>{dashboard.version}</span>
            <span>static SQL demo</span>
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
              <dt>Samples</dt>
              <dd>{dashboard.focus.telemetry_samples}</dd>
            </div>
            <div>
              <dt>DTC rows</dt>
              <dd>{dashboard.focus.dtc_count}</dd>
            </div>
            <div>
              <dt>Metric penalty</dt>
              <dd>{dashboard.focus.metric_penalty_points}</dd>
            </div>
          </dl>
        </article>

        <article className="panel sessionsPanel flowIn delayedTwo">
          <div className="panelHead">
            <p>Seeded drives</p>
            <h2>SQL output</h2>
          </div>
          <div className="sessionList">
            {dashboard.sessions.map((session) => (
              <div className="sessionRow" key={session.session_id}>
                <div>
                  <span>Session {session.session_id}</span>
                  <strong>{session.vehicle}</strong>
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
            <p>Fuel trim</p>
            <h2>Windowed LTFT</h2>
          </div>
          <div className="barChart" aria-label="Fuel trim drift">
            {dashboard.drift.map((point) => (
              <span
                key={point.ts}
                className="bar"
                title={`${point.ts}: ${point.ltft_30s}`}
                style={{ "--bar-height": point.height_pct } as Vars}
              />
            ))}
          </div>
          <p className="microCopy">
            SQL window function over logged LTFT rows. Current focus ends at{" "}
            {dashboard.drift.at(-1)?.ltft_30s}.
          </p>
        </article>

        <article className="panel flowIn delayedFour">
          <div className="panelHead">
            <p>DTC evidence</p>
            <h2>{dashboard.dtcEvidence[0]?.code}</h2>
          </div>
          <div className="evidenceTable" role="table" aria-label="DTC telemetry window">
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
          <p className="microCopy">{dashboard.dtcEvidence[0]?.description}</p>
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
            <h2>Read path</h2>
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
  );
}
