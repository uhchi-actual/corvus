-- Showcase A: baseline deviation.
-- Compares coolant samples to the best baseline band for this vehicle:
-- session-derived bands for public logs, warm bands for synthetic demos.
-- Null coolant readings are ignored, not treated as failures.
SELECT
  b.metric,
  b.context,
  SUM(CASE WHEN t.coolant_temp_c IS NOT NULL THEN 1 ELSE 0 END) AS sample_count,
  SUM(
    CASE
      WHEN t.coolant_temp_c IS NULL THEN 0
      WHEN t.coolant_temp_c NOT BETWEEN b.healthy_min AND b.healthy_max THEN 1
      ELSE 0
    END
  ) AS out_of_range_samples,
  ROUND(
    100.0 * SUM(
      CASE
        WHEN t.coolant_temp_c IS NULL THEN 0
        WHEN t.coolant_temp_c NOT BETWEEN b.healthy_min AND b.healthy_max THEN 1
        ELSE 0
      END
    ) / NULLIF(SUM(CASE WHEN t.coolant_temp_c IS NOT NULL THEN 1 ELSE 0 END), 0),
    1
  ) AS pct_out_of_range
FROM telemetry_samples t
JOIN drive_sessions s
  ON s.session_id = t.session_id
JOIN baselines b
  ON b.vehicle_id = s.vehicle_id
 AND b.metric = 'coolant_temp_c'
 AND b.baseline_id = (
   SELECT b2.baseline_id
   FROM baselines b2
   WHERE b2.vehicle_id = s.vehicle_id
     AND b2.metric = 'coolant_temp_c'
   ORDER BY CASE WHEN b2.source = 'derived' THEN 0 WHEN b2.context = 'warm' THEN 1 WHEN b2.context = 'session' THEN 2 ELSE 3 END
   LIMIT 1
 )
WHERE t.session_id = :session_id
GROUP BY b.metric, b.context
ORDER BY b.metric, b.context;
