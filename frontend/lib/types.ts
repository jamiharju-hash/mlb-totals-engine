export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH';
export type TruthStatus = 'PENDING' | 'READY' | 'VOID';
export type TotalsSide = 'OVER' | 'UNDER' | 'PASS';
export type BetSignal = 'BET_STRONG' | 'BET_SMALL' | 'NO_BET' | 'FADE';

export type DashboardSummary = {
  todays_games: number;
  active_signals: number;
  avg_clv_7d: number;
  rolling_roi_30d: number;
  bet_count_today: number;
  data_lag_seconds: number;
};

export type PredictionLog = {
  id: number;
  game_id: string;
  prediction_timestamp: string;
  side: TotalsSide;
  should_bet: boolean;
  market_total: number;
  calibrated_model_total: number;
  edge_runs: number;
  expected_value: number;
  stake: number;
  confidence: Confidence;
  truth_status: TruthStatus;
  clv: number | null;
  roi: number | null;
};

export type DailyMetric = {
  metric_date: string;
  avg_clv: number;
  roi: number;
  bets: number;
  p95_latency_ms: number;
  max_data_lag_seconds: number;
  success_criteria_pass: boolean;
};

export type Projection = {
  id?: string;
  game_id: string;
  game_date: string;
  team: string;
  opponent: string;
  home_away: 'home' | 'away';
  market: 'moneyline' | 'runline' | 'total';
  selection: string;
  decimal_odds: number | null;
  american_odds?: number | null;
  market_probability: number | null;
  base_probability: number | null;
  final_probability: number | null;
  edge_pct: number | null;
  stake_units: number | null;
  bet_signal: BetSignal;
  model_confidence: number | null;
  manual_override_flag: boolean;
  model_version?: string | null;
  odds_source?: string | null;
  bookmaker?: string | null;
  snapshot_ts?: string | null;
};

export type TeamMarketFeature = {
  id?: string;
  as_of_date: string;
  season?: number | null;
  team: string;
  ml_roi_ytd: number | null;
  rl_roi_ytd: number | null;
  ou_roi_ytd: number | null;
  ml_profit_ytd: number | null;
  rl_profit_ytd: number | null;
  ou_profit_ytd: number | null;
  value_score: number | null;
};

export type ModelMetric = {
  id?: string;
  as_of: string;
  model_version: string;
  test_mae_start_score: number | null;
  test_auc_runline: number | null;
  test_auc_moneyline: number | null;
  simulated_roi_last_250: number | null;
  avg_clv_last_250: number | null;
  notes?: string | null;
};

export type PipelineRun = {
  id: string;
  status: 'success' | 'failed' | 'running';
  started_at: string;
  finished_at: string | null;
  rows_inserted: number | null;
  error_message: string | null;
};

export type DashboardDiagnostics = {
  generated_at: string;
  data_status: 'ok' | 'stale' | 'empty' | 'error';
  latest_metric_date: string | null;
  latest_projection_date: string | null;
  missing_sources: string[];
  errors: string[];
};

export type AnalyticsPayload = {
  summary: DashboardSummary | null;
  signals: PredictionLog[];
  metrics: DailyMetric[];
  projections: Projection[];
  team_market: TeamMarketFeature[];
  model_metrics: ModelMetric | null;
  pipeline_runs: PipelineRun[];
  diagnostics: DashboardDiagnostics;
};
