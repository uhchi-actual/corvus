import type { CSSProperties } from "react";

export type SessionRow = {
  session_id: number;
  vehicle: string;
  source: string;
  notes: string;
  source_file: string;
  drive_label: string;
  health_score: string;
  health_score_width: string;
  telemetry_samples: string;
  dtc_count: string;
  pct_out_of_range: string;
  baseline_width: string;
};

export type FocusRow = SessionRow & {
  started_at: string;
  ended_at: string;
  metric_penalty_points: string;
  dtc_penalty_points: string;
  score_basis: string;
  out_of_range_samples: string;
  sample_count: string;
};

export type TrendRow = {
  ts: string;
  maf_gps: string;
  maf_30s: string;
  height_pct: string;
};

export type DtcRow = {
  code: string;
  status: string;
  description: string;
  ts: string;
  rpm: string;
  engine_load_pct: string;
  coolant_temp_c: string;
};

export type HealthAxis = {
  id: string;
  label: string;
  value: string;
  width_pct: string;
};

export type PerformanceConcern = {
  level: string;
  text: string;
};

export type TraceStep = {
  agent: string;
  node: string;
  kind: string;
  summary: string;
  title?: string;
  body?: string;
  agent_name?: string;
  agent_tagline?: string;
};

export type GuideBlock = {
  title?: string;
  body: string;
};

export type ProvenanceRecord = {
  vehicle: string;
  drive_label: string;
  source_file: string;
  license: string;
  dataset_name: string;
};

export type SessionView = {
  focus: FocusRow;
  trend: TrendRow[];
  dtcEvidence: DtcRow[];
  healthMatrix: HealthAxis[];
  performanceConcerns: PerformanceConcern[];
  agentTrace: TraceStep[];
  agentTraceId: string;
  dtcSummary: string;
};

export type DashboardData = {
  version: string;
  statement: string;
  defaultSessionId: number;
  sessionViews: Record<string, SessionView>;
  focus: FocusRow;
  sessions: SessionRow[];
  trend: TrendRow[];
  dtcEvidence: DtcRow[];
  agentTraceId: string;
  disclaimer: string;
  healthGuide: GuideBlock;
  trendGuide: GuideBlock;
  faultGuide: GuideBlock;
  dataSource: {
    summary: string;
    sources: Array<{
      name: string;
      license: string;
      licenseUrl: string;
      url: string;
    }>;
    entries: string[];
    note: string;
    records: ProvenanceRecord[];
  };
  inspiration: {
    label: string;
    image: string;
  };
};

export type CssVars = CSSProperties & {
  "--score-width"?: string;
  "--baseline-width"?: string;
  "--bar-height"?: string;
};
