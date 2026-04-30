-- 010_metrics_worker_support
-- Applied to Supabase project ohykyscckijbphenugkb on 2026-04-30.
-- Adds operational columns and indexes needed by odds ingestion and post-game metrics workers.

ALTER TABLE public.odds_snapshots
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_time
    ON public.odds_snapshots(game_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_log_pending_truth
    ON public.predictions_log(truth_status, should_bet, prediction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_log_truth_time
    ON public.predictions_log(truth_status, prediction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_games_id_datetime
    ON public.games(id, game_datetime);
