export type BetSignal = "BET_STRONG" | "BET_SMALL" | "NO_BET" | "FADE";

export type Projection = {
  id?: string;
  game_id: string;
  game_date: string;
  team: string;
  opponent: string;
  home_away: "home" | "away";
  market: "moneyline" | "runline" | "total";
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
};

export type TeamMarket = {
  id?: string;
  as_of_date: string;
  team: string;
  ml_roi_ytd: number | null;
  rl_roi_ytd: number | null;
  ou_roi_ytd: number | null;
  ml_profit_ytd: number | null;
  rl_profit_ytd: number | null;
  ou_profit_ytd: number | null;
  value_score: number | null;
};

export type ModelMetrics = {
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
