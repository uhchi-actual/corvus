"use client";

import { useMemo, useState } from "react";

import type { DashboardData, CssVars, DtcRow } from "../../types/dashboard";
import { trendChartAxes } from "../../lib/format";
import { DrivePicker } from "./DrivePicker";
import { HealthScorePanel } from "./HealthScorePanel";
import { HealthMatrix } from "./HealthMatrix";
import { SourceProvenanceTabs } from "./SourceProvenanceTabs";

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
  const flagLines = view.performanceConcerns
    .filter((concern) => concern.level !== "ok")
    .slice(0, 2);
  const airflowAxes = trendChartAxes(view.trend);

  return (
    <main className="dashboard" aria-label="Corvus dashboard">
      <section className="heroSurface flowIn" aria-labelledby="corvus-title">
        <div className="heroCopy">
          <div className="topLine">
            <span>{data.version}</span>
            <span>Real public telemetry</span>
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
        </div>
        <figure className="inspirationPlate" aria-label={data.inspiration.label}>
          <img src={data.inspiration.image} alt={data.inspiration.label} />
          <figcaption>{data.inspiration.label}</figcaption>
        </figure>
      </section>

      <section className="grid twoCol">
        <HealthScorePanel focus={focus} />

        <DrivePicker
          sessions={data.sessions}
          activeSessionId={activeSessionId}
          onSelect={setActiveSessionId}
        />
      </section>

      <section className="grid">
        <article className="panel flowIn delayedTwo" key={`profile-${activeSessionId}`}>
          <div className="panelHead">
            <p>Five SQL Metrics</p>
            <h2>Performance Profile</h2>
          </div>
          <div className="panelSwap">
            <HealthMatrix axes={view.healthMatrix} score={focus.health_score} />
            {flagLines.length > 0 ? (
              <ul className="matrixFlags">
                {flagLines.map((line) => (
                  <li key={line.text}>{line.text}</li>
                ))}
              </ul>
            ) : null}
          </div>
        </article>
      </section>

      <section className="grid twoCol evidenceGrid">
        <article className="panel flowIn delayedThree" key={`airflow-${activeSessionId}`}>
          <div className="panelHead airflowHead">
            <h2>Airflow Data</h2>
          </div>
          <div className="panelSwap">
            <div className="barChartFrame">
              <div className="barChartAxisY" aria-hidden>
                <span className="barChartTick">{airflowAxes.maxG}</span>
                <span className="barChartUnit">g/s</span>
              </div>
              <div className="barChartPlot">
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
                <div className="barChartAxisX" aria-hidden>
                  <span className="barChartTick">{airflowAxes.start}</span>
                  <span className="barChartUnit">Time into drive</span>
                  <span className="barChartTick">{airflowAxes.end}</span>
                </div>
              </div>
            </div>
            <p className="guideCopy">{data.trendGuide.body}</p>
            <p className="microCopy">Last rolling average: {view.trend.at(-1)?.maf_30s} g/s</p>
          </div>
        </article>

        <article className="panel flowIn delayedFour" key={`faults-${activeSessionId}`}>
          <div className="panelHead">
            <p>{data.faultGuide.title}</p>
            <h2>{showFaultRows ? diagnosticCode?.code : "None logged"}</h2>
          </div>
          <div className="panelSwap">
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
          </div>
        </article>
      </section>

      <section className="grid" key={`source-${activeSessionId}`}>
        <SourceProvenanceTabs
          records={data.dataSource.records}
          trace={view.agentTrace}
          traceId={view.agentTraceId}
        />
      </section>

      <footer className="footer flowIn delayedSix">
        <span>{data.disclaimer}</span>
      </footer>
    </main>
  );
}
