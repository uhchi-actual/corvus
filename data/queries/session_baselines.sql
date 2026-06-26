-- Phase 3 support query: baseline recall for Muninn.
-- This returns stored baseline rows only. Any comparison math stays in the
-- showcase and health-score SQL.
SELECT
  b.metric,
  b.context,
  b.healthy_min,
  b.healthy_max,
  b.unit,
  b.source
FROM drive_sessions s
JOIN baselines b
  ON b.vehicle_id = s.vehicle_id
WHERE s.session_id = :session_id
ORDER BY b.metric, b.context;
