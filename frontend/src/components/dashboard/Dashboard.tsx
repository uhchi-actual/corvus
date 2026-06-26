"use client";

import { useMemo, useState } from "react";

import type { DashboardData, CssVars, DtcRow } from "../../types/dashboard";
import { AgentPanel } from "./AgentPanel";
import { DrivePicker } from "./DrivePicker";
import { PipelineStrip } from "./PipelineStrip";
import { SqlModuleGrid } from "./SqlModuleGrid";

type Props = {
  data: DashboardData;
};

function hasDiagnosticRows(rows: DtcRow[]) {
  return rows[0]?.status !== "none";
}

export function Dashboard({ data }: Props) {
  const [activeSessionId, setActiveSessionId] = useState(data.defaultSessionId);

  const view = useMemo(() => {
    const keyed = data.sessionViews[String(activeSessionId)];
    if (keyed) {
      return keyed;
    }
    return data.sessionViews[String(data.defaultSessionId)];
  }, [activeSessionId, data.defaultSessionId, data.sessionViews]);

  const focus = view.focus;
  const diagnosticRows = view.dtcEvidence;
  const diagnosticCode = diagnosticRows[0];
  const showFaultRows = hasDiagnosticRows(diagnosticRows);
  const huginnSteps = view.agentTrace.filter((step) => step.agent === "huginn");
  const muninnSteps = view.agentTrace.filter((step) => step.agent === "muninn");

  return (
    <main className="dashboard" aria-label="Corvus dashboard">
      <section className="heroSurface flowIn" aria-labelledby="corvus-title">
        <div className="heroCopy">
          <div className="topLine">
            <span>{data.version}</span>
            <span>real public telemetry</span>
          </div>
          <h1 id="corvus-title" className="wordmark" data-text="corvus">
            corvus
          </h1>
          <p className="statement">{data.statement}</p>
          <p className="sourceLine">
            {data.dataSource.sources.map((source, index) => (
              <span key={source.name}>
                {index > 0 ? " / " : "Data: "}
                <a href={source.url}>{source.name}</a>
                {" "}
                <a href={source.licenseUrl}>{source.license}</a>
              </span>
            ))}
          </p>
          <p className="sourceDetail">{data.dataSource.summary}</p>
        </div>
        <figure className="inspirationPlate" aria-label={data.inspiration.label}>
          <img src={data.inspiration.image} alt={data.inspiration.label} />
          <figcaption>{data.inspiration.label}</figcaption>
        </figure>
      </section>

      <PipelineStrip modules={data.pipeline} />

      <section className="grid twoCol">
        <article className="panel scorePanel flowIn delayedOne">
          <div className="panelHead">
            <p>{data.healthGuide.title}</p>
            <h2>{focus.vehicle}</h2>
          </div>
          <div
            className="scoreRing"
            style={{ "--score-width": focus.health_score_width } as CssVars}
            aria-label={`Drive health ${focus.health_score}`}
          >
            <span>{focus.health_score}</span>
          </div>
          <p className="guideCopy">{data.healthGuide.body}</p>
          <div className="meterBlock">
            <div className="meterLabel">
              <span>{focus.drive_label}</span>
              <span>{focus.health_score_width}</span>
            </div>
            <div className="meterTrack">
              <span
                className="meterFill"
                style={{ "--score-width": focus.health_score_width } as CssVars}
              />
            </div>
          </div>
          <dl className="factGrid">
            <div>
              <dt>Data points</dt>
              <dd>{focus.telemetry_samples}</dd>
            </div>
            <div>
              <dt>Fault codes</dt>
              <dd>{focus.dtc_count}</dd>
            </div>
            <div>
              <dt>Metric penalties</dt>
              <dd>{focus.metric_penalty_points}</dd>
            </div>
            <div>
              <dt>Source file</dt>
              <dd className="factFile">{focus.source_file}</dd>
            </div>
          </dl>
        </article>

        <DrivePicker
          sessions={data.sessions}
          activeSessionId={activeSessionId}
          onSelect={setActiveSessionId}
        />
      </section>

      <SqlModuleGrid modules={view.sqlModules} sessionLabel={focus.vehicle} />

      <section className="grid twoCol evidenceGrid">
        <article className="panel flowIn delayedThree">
          <div className="panelHead">
            <p>{data.trendGuide.title}</p>
            <h2>Over this drive</h2>
          </div>
          <div className="barChart" aria-label="Mass air flow rolling trend">
            {view.trend.map((point) => (
              <span
                key={point.ts}
                className="bar"
                title={`${point.ts}: ${point.maf_30s} g/s`}
                style={{ "--bar-height": point.height_pct } as CssVars}
              />
            ))}
          </div>
          <p className="guideCopy">{data.trendGuide.body}</p>
          <p className="microCopy">Last rolling average: {view.trend.at(-1)?.maf_30s} g/s</p>
        </article>

        <article className="panel flowIn delayedFour">
          <div className="panelHead">
            <p>{data.faultGuide.title}</p>
            <h2>{showFaultRows ? diagnosticCode?.code : "None logged"}</h2>
          </div>
          {showFaultRows ? (
            <div className="evidenceTable" role="table" aria-label="Fault code sensor window">
              <div className="tableRow tableHead" role="row">
                <span role="columnheader">RPM</span>
                <span role="columnheader">Load</span>
                <span role="columnheader">Coolant</span>
                <span role="columnheader">Status</span>
              </div>
              {diagnosticRows.map((row) => (
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
          <p className="guideCopy">{data.faultGuide.body}</p>
          {view.dtcSummary ? <p className="microCopy">{view.dtcSummary}</p> : null}
        </article>
      </section>

      <section className="grid twoCol">
        <AgentPanel profile={data.agents.huginn} steps={huginnSteps} />
        <AgentPanel profile={data.agents.muninn} steps={muninnSteps} />
      </section>

      <section className="grid twoCol">
        <article className="panel flowIn delayedSix">
          <div className="panelHead">
            <p>How to read this page</p>
            <h2>Read order</h2>
          </div>
          <ol className="readOrderList">
            {data.readOrder.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <ol className="workflowList">
            {data.workflow.map((step) => (
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
          <p className="guideCopy">{data.dataSource.note}</p>
          <div className="provenanceRecords">
            {data.dataSource.records.map((record) => (
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
          {data.method.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <div className="finding">
          <strong>{view.finding.likely_cause}</strong>
          <p>{view.finding.recommended_fix}</p>
          {view.correlationSummary ? <p>{view.correlationSummary}</p> : null}
          <p className="traceId">Trace id: {view.agentTraceId}</p>
        </div>
      </section>

      <footer className="footer flowIn delayedSix">
        <span>{data.disclaimer}</span>
      </footer>
    </main>
  );
}
