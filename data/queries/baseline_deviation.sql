-- Showcase A: baseline deviation.
-- Computes the share of this session's coolant samples outside the
-- per-vehicle healthy range. All percentages are calculated in SQL.
SELECT
  b.metric,
  b.context,
  COUNT(*) AS sample_count,
  SUM(
    CASE
      WHEN t.coolant_temp_c NOT BETWEEN b.healthy_min AND b.healthy_max THEN 1
      ELSE 0
    END
  ) AS out_of_range_samples,
  ROUND(
    100.0 * SUM(
      CASE
        WHEN t.coolant_temp_c NOT BETWEEN b.healthy_min AND b.healthy_max THEN 1
        ELSE 0
      END
    ) / COUNT(*),
    1
  ) AS pct_out_of_range
FROM telemetry_samples t
JOIN drive_sessions s
  ON s.session_id = t.session_id
JOIN baselines b
  ON b.vehicle_id = s.vehicle_id
 AND b.metric = 'coolant_temp_c'
WHERE t.session_id = :session_id
GROUP BY b.metric, b.context
ORDER BY b.metric, b.context;
