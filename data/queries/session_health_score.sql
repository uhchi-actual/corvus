-- Phase 2: deterministic session health score.
-- All score math happens in SQL. The penalty values are directional defaults
-- passed in from data/health_score_config.json so an analyst can edit them
-- without changing application code.
WITH metric_samples AS (
  SELECT
    t.session_id,
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
    COUNT(observed_value) AS checked_samples,
    SUM(
      CASE
        WHEN observed_value NOT BETWEEN healthy_min AND healthy_max THEN 1
        ELSE 0
      END
    ) AS out_of_range_samples,
    1.0 * SUM(
      CASE
        WHEN observed_value NOT BETWEEN healthy_min AND healthy_max THEN 1
        ELSE 0
      END
    ) / NULLIF(COUNT(observed_value), 0) AS out_of_range_rate
  FROM metric_samples
  WHERE observed_value IS NOT NULL
  GROUP BY metric, context
),
metric_penalty AS (
  SELECT
    COALESCE(SUM(out_of_range_rate * :metric_penalty_points), 0.0) AS points
  FROM metric_deviation
),
dtc_penalty AS (
  SELECT
    COUNT(*) AS dtc_count,
    COALESCE(
      SUM(
        CASE status
          WHEN 'permanent' THEN :permanent_dtc_penalty
          WHEN 'stored' THEN :stored_dtc_penalty
          WHEN 'pending' THEN :pending_dtc_penalty
          ELSE :pending_dtc_penalty
        END
      ),
      0.0
    ) AS points
  FROM dtc_events
  WHERE session_id = :session_id
),
sample_summary AS (
  SELECT
    COUNT(*) AS telemetry_samples,
    MIN(ts) AS started_at,
    MAX(ts) AS ended_at
  FROM telemetry_samples
  WHERE session_id = :session_id
),
raw_score AS (
  SELECT
    :score_ceiling - metric_penalty.points - dtc_penalty.points AS value,
    metric_penalty.points AS metric_penalty_points,
    dtc_penalty.points AS dtc_penalty_points,
    dtc_penalty.dtc_count,
    sample_summary.telemetry_samples,
    sample_summary.started_at,
    sample_summary.ended_at
  FROM metric_penalty
  CROSS JOIN dtc_penalty
  CROSS JOIN sample_summary
)
SELECT
  :session_id AS session_id,
  ROUND(
    CASE
      WHEN value < :score_floor THEN :score_floor
      WHEN value > :score_ceiling THEN :score_ceiling
      ELSE value
    END,
    1
  ) AS health_score,
  ROUND(metric_penalty_points, 1) AS metric_penalty_points,
  ROUND(dtc_penalty_points, 1) AS dtc_penalty_points,
  dtc_count,
  telemetry_samples,
  started_at,
  ended_at,
  :score_basis AS score_basis
FROM raw_score;
