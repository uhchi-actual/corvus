import type { CssVars, SessionRow } from "../../types/dashboard";

type Props = {
  sessions: SessionRow[];
  activeSessionId: number;
  onSelect: (sessionId: number) => void;
};

export function DrivePicker({ sessions, activeSessionId, onSelect }: Props) {
  return (
    <article className="panel sessionsPanel flowIn delayedTwo">
      <div className="panelHead">
        <p>Three real cars</p>
        <h2>Pick a drive</h2>
      </div>
      <p className="guideCopy">Click a row to reload every panel for that vehicle.</p>
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
