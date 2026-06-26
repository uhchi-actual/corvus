# Methodology

Corvus keeps the work split.

## Data

OBD-II logs become tidy rows:

- vehicle
- drive session
- telemetry samples
- DTC events
- baselines
- findings

## Analysis

SQL does the numeric work:

- baseline deviation
- fuel-trim drift
- DTC telemetry windows
- session health score

The agent layer reads those rows and writes plain-language findings. It does not
calculate sensor values or thresholds.

## Review

Every finding carries:

- SQL evidence
- `agent_trace_id`
- disclaimer
- directional scoring label

This keeps the report auditable.
