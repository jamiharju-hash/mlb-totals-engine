export type BetSignal = "BET_STRONG" | "BET_SMALL" | "NO_BET" | "FADE";

export type Projection = {
  game_id: string;
  date: string;
  team: string;
  opponent: string;
  home_away: "home" | "away";
  market: "moneyline" | "runline" | "total" | string;
  selection: string;
  decimal_odds: number;
  market_probability: number;
  base_probability: number;
  final_probability: number;
  edge_pct: number;
  stake_units: number;
  bet_signal: BetSignal;
  model_confidence: number;
  manual_override_flag: boolean;
  pitcher_adjustment?: number;
  lineup_adjustment?: number;
  handedness_adjustment?: number;
  weather_adjustment?: number;
  bullpen_adjustment?: number;
  manual_override?: number;
};

export type TeamMarket = {
  team: string;
  ml_roi_ytd: number;
  rl_roi_ytd: number;
  ou_roi_ytd: number;
  ml_profit_ytd: number;
  rl_profit_ytd: number;
  ou_profit_ytd: number;
  value_score: number;
};

export type DashboardPayload = {
  generated_at: string;
  summary: {
    projection_count: number;
    bet_count: number;
    strong_bet_count: number;
    average_edge_pct: number;
    max_edge_pct: number;
    teams_tracked: number;
  };
  projections: Projection[];
  team_market: TeamMarket[];
  model_metrics: {
    as_of: string;
    model_version: string;
    test_mae_start_score: number;
    test_auc_runline: number;
    test_auc_moneyline: number;
    simulated_roi_last_250: number;
    avg_clv_last_250: number;
    notes?: string;
  };
};
