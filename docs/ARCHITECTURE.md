# Architecture

Corvus follows the handoff split:

1. Deterministic ingest normalizes OBD-II data into tidy rows.
2. SQL stores the relational model and computes every numeric result.
3. Huginn explains present-session facts.
4. Muninn recalls baseline and prior-session context.
5. Reports and dashboards present evidence, recommendations, and trace IDs.

Phase 2 includes deterministic SQL for baseline deviation, fuel-trim drift,
DTC-to-telemetry correlation, and session health scoring. Later phases must not
bypass SQL for numeric analysis.

## SQL Core

The showcase queries live in `data/queries/`:

- `baseline_deviation.sql`
- `fuel_trim_drift.sql`
- `dtc_telemetry_correlation.sql`
- `session_health_score.sql`

`session_health_score.sql` receives editable directional defaults from
`data/health_score_config.json`. Python only loads parameters and executes SQL;
it does not calculate vehicle-health numbers.

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
