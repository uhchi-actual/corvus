CREATE TABLE vehicles (
  vehicle_id   INTEGER PRIMARY KEY,
  vin          TEXT,
  make         TEXT,
  model        TEXT,
  year         INTEGER,
  engine       TEXT,
  notes        TEXT
);

CREATE TABLE drive_sessions (
  session_id   INTEGER PRIMARY KEY,
  vehicle_id   INTEGER REFERENCES vehicles(vehicle_id),
  started_at   TIMESTAMP,
  ended_at     TIMESTAMP,
  source       TEXT,
  ambient_c    REAL,
  notes        TEXT
);

CREATE TABLE telemetry_samples (
  sample_id        INTEGER PRIMARY KEY,
  session_id       INTEGER REFERENCES drive_sessions(session_id),
  ts               TIMESTAMP,
  rpm              REAL,
  speed_kph        REAL,
  engine_load_pct  REAL,
  coolant_temp_c   REAL,
  intake_temp_c    REAL,
  maf_gps          REAL,
  throttle_pct     REAL,
  stft_b1_pct      REAL,
  ltft_b1_pct      REAL,
  timing_adv_deg   REAL,
  fuel_press_kpa   REAL,
  o2_b1s1_v        REAL
);

CREATE TABLE dtc_events (
  dtc_id      INTEGER PRIMARY KEY,
  session_id  INTEGER REFERENCES drive_sessions(session_id),
  ts          TIMESTAMP,
  code        TEXT,
  status      TEXT,
  description TEXT
);

CREATE TABLE baselines (
  baseline_id  INTEGER PRIMARY KEY,
  vehicle_id   INTEGER REFERENCES vehicles(vehicle_id),
  metric       TEXT,
  context      TEXT,
  healthy_min  REAL,
  healthy_max  REAL,
  unit         TEXT,
  source       TEXT
);

CREATE TABLE findings (
  finding_id      INTEGER PRIMARY KEY,
  session_id      INTEGER REFERENCES drive_sessions(session_id),
  severity        TEXT,
  category        TEXT,
  metric_or_code  TEXT,
  observed        TEXT,
  expected_range  TEXT,
  likely_cause    TEXT,
  recommended_fix TEXT,
  confidence      REAL,
  evidence_json   TEXT,
  agent_trace_id  TEXT,
  created_at      TIMESTAMP
);
