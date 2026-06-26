-- Showcase C: DTC-to-telemetry correlation.
-- Pulls the telemetry window around each diagnostic event. The timestamps are
-- joined in SQL; downstream agents may explain these rows but must not compute
-- the window themselves.
SELECT
  d.code,
  d.status,
  d.description,
  d.ts AS fault_ts,
  t.ts,
  t.rpm,
  t.engine_load_pct,
  t.coolant_temp_c
FROM dtc_events d
JOIN telemetry_samples t
  ON t.session_id = d.session_id
 AND datetime(t.ts) BETWEEN datetime(d.ts, '-5 seconds') AND datetime(d.ts, '+5 seconds')
WHERE d.session_id = :session_id
ORDER BY d.code, t.ts;
