import type { CssVars, FocusRow, HealthAxis } from "../../types/dashboard";
import { cleanSourceFile } from "../../lib/format";
import { scoreColor } from "../../lib/score";

const AXIS_CODES: Record<string, string> = {
  drive_health: "DH",
  baseline_fit: "BF",
  airflow: "AF",
  fault_clearance: "FC",
  sensor_balance: "SB",
};

type Props = {
  focus: FocusRow;
  axes: HealthAxis[];
};

export function HealthScorePanel({ focus, axes }: Props) {
  const metricPenalty = Number(focus.metric_penalty_points);
  const dtcPenalty = Number(focus.dtc_penalty_points);
  const penaltyTotal = Math.max(metricPenalty + dtcPenalty, 1);
  const baselineDrift = Number(focus.pct_out_of_range);
  const baselineFit = Math.max(0, Math.min(100, 100 - baselineDrift));

  return (
    <article className="panel scorePanel flowIn delayedOne">
      <div className="panelHead">
        <p>Drive health score</p>
        <h2>{focus.vehicle}</h2>
      </div>

      <div className="healthScoreHero">
        <div
          className="scoreRing scoreRingLarge"
          style={{ "--score-width": focus.health_score_width } as CssVars}
          aria-label={`Drive health ${focus.health_score} out of 100`}
        >
          <span className="scoreRingValue">{focus.health_score}</span>
          <span className="scoreRingCap">of 100</span>
        </div>

        <div className="healthScoreBreakdown">
          <p className="healthScoreLead">{focus.drive_label}</p>
          <ul className="axisMiniBars" aria-label="Score breakdown by axis">
            {axes.map((axis) => {
              const value = Number(axis.value);
              const color = scoreColor(value);
              return (
                <li key={axis.id} className="axisMiniRow">
                  <span className="axisMiniCode">{AXIS_CODES[axis.id] ?? axis.label}</span>
                  <div className="axisMiniTrack" aria-hidden>
                    <span
                      className="axisMiniFill"
                      style={
                        {
                          "--bar-width": axis.width_pct,
                          "--bar-color": color,
                        } as CssVars
                      }
                    />
                  </div>
                  <span className="axisMiniValue">{axis.value}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      <div className="healthScoreGauges">
        <div className="gaugeCard">
          <span className="gaugeLabel">Baseline band fit</span>
          <div className="gaugeTrack">
            <span
              className="gaugeFill"
              style={
                {
                  "--gauge-width": `${baselineFit.toFixed(1)}%`,
                  "--gauge-color": scoreColor(baselineFit),
                } as CssVars
              }
            />
          </div>
          <span className="gaugeMeta">{baselineFit.toFixed(1)}% inside band</span>
        </div>

        <div className="gaugeCard">
          <span className="gaugeLabel">Penalty split</span>
          <div className="penaltySplit" aria-hidden>
            <span
              className="penaltyMetric"
              style={{ flexGrow: metricPenalty }}
            />
            <span
              className="penaltyDtc"
              style={{ flexGrow: dtcPenalty }}
            />
          </div>
          <span className="gaugeMeta">
            Metric {focus.metric_penalty_points} · Fault {focus.dtc_penalty_points}
          </span>
        </div>

        <div className="gaugeCard gaugeCardStat">
          <span className="gaugeLabel">Telemetry rows</span>
          <strong className="gaugeStat">{focus.telemetry_samples}</strong>
          <span className="gaugeMeta">{focus.dtc_count} fault codes logged</span>
        </div>
      </div>

      <dl className="factGrid factGridCompact">
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
          <dd className="factFile">{cleanSourceFile(focus.source_file)}</dd>
        </div>
      </dl>
    </article>
  );
}
