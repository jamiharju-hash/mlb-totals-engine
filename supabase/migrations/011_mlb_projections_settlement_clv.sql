ALTER TABLE public.mlb_projections
  ADD COLUMN IF NOT EXISTS season integer,
  ADD COLUMN IF NOT EXISTS model_version text,
  ADD COLUMN IF NOT EXISTS odds_source text,
  ADD COLUMN IF NOT EXISTS bookmaker text,
  ADD COLUMN IF NOT EXISTS snapshot_ts timestamptz,
  ADD COLUMN IF NOT EXISTS american_odds numeric,
  ADD COLUMN IF NOT EXISTS stake_pct_bankroll numeric DEFAULT 0,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now(),
  ADD COLUMN IF NOT EXISTS result text CHECK (result IN ('win', 'loss', 'push', 'pending', 'void')),
  ADD COLUMN IF NOT EXISTS settled_at timestamptz,
  ADD COLUMN IF NOT EXISTS pnl_units numeric,
  ADD COLUMN IF NOT EXISTS stake_amount_units numeric,
  ADD COLUMN IF NOT EXISTS closing_decimal_odds numeric,
  ADD COLUMN IF NOT EXISTS closing_american_odds numeric,
  ADD COLUMN IF NOT EXISTS closing_implied_probability numeric,
  ADD COLUMN IF NOT EXISTS clv_pct numeric;

CREATE INDEX IF NOT EXISTS idx_mlb_projections_game_date
  ON public.mlb_projections(game_date DESC);

CREATE INDEX IF NOT EXISTS idx_mlb_projections_edge_pct
  ON public.mlb_projections(edge_pct DESC);

CREATE INDEX IF NOT EXISTS idx_mlb_projections_result
  ON public.mlb_projections(result);

COMMENT ON TABLE public.mlb_projections IS
  'MLB projection rows with settlement and CLV fields. See SPEC.md §13.';
