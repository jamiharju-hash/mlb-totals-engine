-- Dashboard and closing-line support.
-- Adds market phase metadata to odds snapshots and read-only dashboard policies.

ALTER TABLE public.odds_snapshots
    ADD COLUMN IF NOT EXISTS market_phase TEXT NOT NULL DEFAULT 'unknown'
        CHECK (market_phase IN ('opening', 'pre_lineup', 'post_lineup', 'closing', 'unknown'));

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_phase_time
    ON public.odds_snapshots(game_id, market_phase, timestamp DESC);

-- Read-only policies for internal dashboard using Supabase publishable key.
-- No insert/update/delete policies are created.

DROP POLICY IF EXISTS "dashboard_read_games" ON public.games;
CREATE POLICY "dashboard_read_games"
ON public.games
FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "dashboard_read_odds_snapshots" ON public.odds_snapshots;
CREATE POLICY "dashboard_read_odds_snapshots"
ON public.odds_snapshots
FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "dashboard_read_predictions_log" ON public.predictions_log;
CREATE POLICY "dashboard_read_predictions_log"
ON public.predictions_log
FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "dashboard_read_game_results" ON public.game_results;
CREATE POLICY "dashboard_read_game_results"
ON public.game_results
FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "dashboard_read_daily_metrics" ON public.daily_metrics;
CREATE POLICY "dashboard_read_daily_metrics"
ON public.daily_metrics
FOR SELECT
TO anon, authenticated
USING (true);

CREATE OR REPLACE VIEW public.dashboard_summary AS
SELECT
    CURRENT_DATE AS metric_date,
    COALESCE((SELECT COUNT(*) FROM public.games WHERE game_date = CURRENT_DATE), 0) AS todays_games,
    COALESCE((SELECT COUNT(*) FROM public.predictions_log WHERE should_bet = true AND truth_status = 'PENDING'), 0) AS active_signals,
    COALESCE((SELECT AVG(clv) FROM public.predictions_log WHERE should_bet = true AND clv IS NOT NULL AND prediction_timestamp >= NOW() - INTERVAL '7 days'), 0) AS avg_clv_7d,
    COALESCE((SELECT AVG(roi) FROM public.daily_metrics WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'), 0) AS rolling_roi_30d,
    COALESCE((SELECT COUNT(*) FROM public.predictions_log WHERE should_bet = true AND prediction_timestamp >= CURRENT_DATE), 0) AS bet_count_today,
    COALESCE((SELECT MAX(EXTRACT(EPOCH FROM (NOW() - timestamp))) FROM public.odds_snapshots), 0) AS data_lag_seconds;
