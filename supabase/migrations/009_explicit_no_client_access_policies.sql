-- 009_explicit_no_client_access_policies
-- Applied to Supabase project ohykyscckijbphenugkb on 2026-04-30.
-- Explicitly deny anon/authenticated access to internal service-role-only tables.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_bets' AND polrelid = 'public.bets'::regclass) THEN
        CREATE POLICY no_client_access_bets ON public.bets FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_bets_v2' AND polrelid = 'public.bets_v2'::regclass) THEN
        CREATE POLICY no_client_access_bets_v2 ON public.bets_v2 FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_features' AND polrelid = 'public.features'::regclass) THEN
        CREATE POLICY no_client_access_features ON public.features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_lineups' AND polrelid = 'public.lineups'::regclass) THEN
        CREATE POLICY no_client_access_lineups ON public.lineups FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_model_runs' AND polrelid = 'public.model_runs'::regclass) THEN
        CREATE POLICY no_client_access_model_runs ON public.model_runs FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_pitcher_stats' AND polrelid = 'public.pitcher_stats'::regclass) THEN
        CREATE POLICY no_client_access_pitcher_stats ON public.pitcher_stats FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_prediction_truth_links' AND polrelid = 'public.prediction_truth_links'::regclass) THEN
        CREATE POLICY no_client_access_prediction_truth_links ON public.prediction_truth_links FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_predictions' AND polrelid = 'public.predictions'::regclass) THEN
        CREATE POLICY no_client_access_predictions ON public.predictions FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_signal_decisions' AND polrelid = 'public.signal_decisions'::regclass) THEN
        CREATE POLICY no_client_access_signal_decisions ON public.signal_decisions FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_team_metrics' AND polrelid = 'public.team_metrics'::regclass) THEN
        CREATE POLICY no_client_access_team_metrics ON public.team_metrics FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_team_stats_history' AND polrelid = 'public.team_stats_history'::regclass) THEN
        CREATE POLICY no_client_access_team_stats_history ON public.team_stats_history FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
END $$;
