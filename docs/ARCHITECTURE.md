# Architecture

Corvus follows the handoff split:

1. Deterministic ingest normalizes OBD-II data into tidy rows.
2. SQL stores the relational model and computes every numeric result.
3. Huginn explains present-session facts.
4. Muninn recalls baseline and prior-session context.
5. Reports and dashboards present evidence, recommendations, and trace IDs.

Phase 3 includes the Huginn and Muninn LangGraph flow. The graph consumes SQL
rows, writes traced findings, and returns the mandatory disclaimer on every
response path. It must not bypass SQL for numeric analysis.

## SQL Core

The showcase queries live in `data/queries/`:

- `baseline_deviation.sql`
- `fuel_trim_drift.sql`
- `dtc_telemetry_correlation.sql`
- `session_health_score.sql`

`session_health_score.sql` receives editable directional defaults from
`data/health_score_config.json`. Python only loads parameters and executes SQL;
it does not calculate vehicle-health numbers.

## Agent Layer

Huginn handles the current session:

- `ingest_normalizer`
- `sql_deviation`
- `dtc_interpreter`

Muninn handles memory and comparison:

- `baseline_recall`
- `correlation`
- `recommendation`

`report_writer` writes `findings.agent_trace_id`. API responses include
`agent_trace_id`, `agent_trace`, and the mandatory disclaimer whether analysis
succeeds or fails.

The analysis route is `POST /analysis/session/{session_id}` because it writes a
finding row.

## Read-Only OBD-II Scope

Allowed modes:

- Mode 01 - current live data
- Mode 02 - freeze-frame data
- Mode 03 - stored trouble codes
- Mode 07 - pending trouble codes
- Mode 09 - vehicle information

Mode 04 and ECU writes are excluded by design.

## OBD-II Verification

Before implementing any command, PID, mode, or threshold, verify it against the
`brendan-w/python-OBD` source. Do not use model memory as the source of truth.
