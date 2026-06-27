import type { CssVars, SessionRow } from "../../types/dashboard";
import { cleanSourceFile } from "../../lib/format";

type Props = {
  sessions: SessionRow[];
  activeSessionId: number;
  onSelect: (sessionId: number) => void;
};

export function DrivePicker({ sessions, activeSessionId, onSelect }: Props) {
  return (
    <article className="panel sessionsPanel flowIn delayedTwo">
      <div className="panelHead">
        <p>Public source data</p>
        <h2>Engine list</h2>
      </div>
      <p className="guideCopy">Select a vehicle to load its panels.</p>
      <div className="sessionList">
        {sessions.map((session) => {
          const isActive = session.session_id === activeSessionId;
          return (
            <button
              type="button"
              className={`sessionRow sessionButton${isActive ? " isActive" : ""}`}
              key={session.session_id}
              onClick={() => onSelect(session.session_id)}
              aria-pressed={isActive}
            >
              <div className="sessionMeta">
                <span className="sessionEyebrow">{session.drive_label}</span>
                <strong className="sessionVehicle">{session.vehicle}</strong>
                <span className="sessionFile">{cleanSourceFile(session.source_file)}</span>
              </div>
              <div className="miniMeters">
                <span>{session.health_score}</span>
                <div className="meterTrack">
                  <span
                    className="meterFill"
                    style={{ "--score-width": session.health_score_width } as CssVars}
                  />
                </div>
                <small>{session.telemetry_samples} rows</small>
              </div>
            </button>
          );
        })}
      </div>
    </article>
  );
}
