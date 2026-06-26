-- Phase 3 support query: DTC facts for Huginn.
-- Descriptions come from the logged source or python-OBD response data.
SELECT
  code,
  status,
  description,
  ts
FROM dtc_events
WHERE session_id = :session_id
ORDER BY ts, code;
