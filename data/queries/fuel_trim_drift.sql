-- Showcase B: sustained fuel-trim drift.
-- Uses a SQL window function over prior rows to separate sustained drift from
-- point noise. The sample rate determines the exact time span represented by
-- the 30 preceding rows.
SELECT
  ts,
  ltft_b1_pct,
  ROUND(
    AVG(ltft_b1_pct) OVER (
      ORDER BY ts
      ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
    ),
    2
  ) AS ltft_30s
FROM telemetry_samples
WHERE session_id = :session_id
ORDER BY ts;
