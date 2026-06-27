-- Showcase A: baseline deviation per metric for this session.
-- Uses the same metric list and vehicle baselines as session_health_score.sql.
-- Null readings are ignored, not treated as failures.
WITH metric_samples AS (
  SELECT
    b.metric,
    b.context,
    b.healthy_min,
    b.healthy_max,
    CASE b.metric
      WHEN 'coolant_temp_c' THEN t.coolant_temp_c
      WHEN 'ltft_b1_pct' THEN t.ltft_b1_pct
      WHEN 'stft_b1_pct' THEN t.stft_b1_pct
      WHEN 'engine_load_pct' THEN t.engine_load_pct
      WHEN 'timing_adv_deg' THEN t.timing_adv_deg
    END AS observed_value
  FROM telemetry_samples t
  JOIN drive_sessions s
    ON s.session_id = t.session_id
  JOIN baselines b
    ON b.vehicle_id = s.vehicle_id
   AND b.metric IN (
     'coolant_temp_c',
     'ltft_b1_pct',
     'stft_b1_pct',
     'engine_load_pct',
     'timing_adv_deg'
   )
  WHERE t.session_id = :session_id
),
metric_deviation AS (
  SELECT
    metric,
    context,
    COUNT(observed_value) AS sample_count,
    SUM(
      CASE
        WHEN observed_value NOT BETWEEN healthy_min AND healthy_max THEN 1
        ELSE 0
      END
    ) AS out_of_range_samples
  FROM metric_samples
  WHERE observed_value IS NOT NULL
  GROUP BY metric, context
)
SELECT
  metric,
  context,
  sample_count,
  out_of_range_samples,
  ROUND(
    100.0 * out_of_range_samples / NULLIF(sample_count, 0),
    1
  ) AS pct_out_of_range
FROM metric_deviation
ORDER BY metric, context;
