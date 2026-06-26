SELECT
  s.session_id,
  v.make,
  v.model,
  s.source,
  s.started_at,
  s.ended_at,
  COUNT(t.sample_id) AS telemetry_samples,
  COUNT(DISTINCT d.dtc_id) AS dtc_events
FROM drive_sessions s
JOIN vehicles v
  ON v.vehicle_id = s.vehicle_id
LEFT JOIN telemetry_samples t
  ON t.session_id = s.session_id
LEFT JOIN dtc_events d
  ON d.session_id = s.session_id
GROUP BY s.session_id, v.make, v.model, s.source, s.started_at, s.ended_at
ORDER BY s.session_id;
