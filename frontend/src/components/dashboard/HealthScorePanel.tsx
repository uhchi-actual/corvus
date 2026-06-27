import type { CssVars, FocusRow } from "../../types/dashboard";
import { cleanSourceFile, formatDriveWindow, formatHealthScore, formatHealthScoreWidth } from "../../lib/format";

type Props = {
  focus: FocusRow;
};

export function HealthScorePanel({ focus }: Props) {
  const driveWindow = formatDriveWindow(focus.started_at, focus.ended_at);
  const healthScore = formatHealthScore(focus.health_score);
  const samples = Number(focus.telemetry_samples);
  const samplePace =
    samples > 0 && driveWindow.durationSec > 0
      ? `${(driveWindow.durationSec / samples).toFixed(1)}s per row`
      : "—";

  return (
    <article className="panel scorePanel flowIn delayedOne">
      <div className="panelHead">
        <p>Drive health score</p>
        <h2>{focus.vehicle}</h2>
      </div>

      <div className="healthScoreHero">
        <div
          className="scoreRing scoreRingLarge"
          style={{ "--score-width": formatHealthScoreWidth(focus.health_score) } as CssVars}
          aria-label={`Drive health ${healthScore} out of 100`}
        >
          <span className="scoreRingValue">{healthScore}</span>
          <span className="scoreRingCap">of 100</span>
        </div>

        <div className="healthScoreContext">
          <p className="healthScoreLead">{focus.drive_label}</p>
          <dl className="healthScoreFacts">
            <div>
              <dt>Drive window</dt>
              <dd>{driveWindow.clock}</dd>
              <dd className="healthScoreMeta">{driveWindow.duration}</dd>
            </div>
            <div>
              <dt>Telemetry rows</dt>
              <dd>{focus.telemetry_samples}</dd>
              <dd className="healthScoreMeta">{samplePace}</dd>
            </div>
            <div>
              <dt>Source file</dt>
              <dd className="factFile">{cleanSourceFile(focus.source_file)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </article>
  );
}
