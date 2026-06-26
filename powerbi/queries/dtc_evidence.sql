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
ORDER BY d.session_id, d.code, t.ts;
