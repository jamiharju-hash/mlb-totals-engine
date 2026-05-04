-- Follow-up hardening for environments that already applied 011.
ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources FORCE ROW LEVEL SECURITY;
ALTER TABLE public.source_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE public.raw_ingestion_payloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_ingestion_payloads FORCE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams FORCE ROW LEVEL SECURITY;
ALTER TABLE public.venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.venues FORCE ROW LEVEL SECURITY;
ALTER TABLE public.players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.players FORCE ROW LEVEL SECURITY;
ALTER TABLE public.player_id_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_id_map FORCE ROW LEVEL SECURITY;
ALTER TABLE public.statcast_pitches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.statcast_pitches FORCE ROW LEVEL SECURITY;
ALTER TABLE public.player_daily_batting_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_daily_batting_features FORCE ROW LEVEL SECURITY;
ALTER TABLE public.player_daily_pitching_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_daily_pitching_features FORCE ROW LEVEL SECURITY;
ALTER TABLE public.batter_pitcher_matchup_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batter_pitcher_matchup_features FORCE ROW LEVEL SECURITY;
ALTER TABLE public.park_factors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.park_factors FORCE ROW LEVEL SECURITY;
ALTER TABLE public.weather_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weather_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE public.sportsbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sportsbooks FORCE ROW LEVEL SECURITY;
ALTER TABLE public.historical_closing_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.historical_closing_odds FORCE ROW LEVEL SECURITY;
ALTER TABLE public.pitcher_game_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pitcher_game_usage FORCE ROW LEVEL SECURITY;
ALTER TABLE public.team_rest_travel_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_rest_travel_features FORCE ROW LEVEL SECURITY;
ALTER TABLE public.bullpen_fatigue_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bullpen_fatigue_features FORCE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_data_sources' AND polrelid = 'public.data_sources'::regclass) THEN
        CREATE POLICY no_client_access_data_sources ON public.data_sources FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_source_runs' AND polrelid = 'public.source_runs'::regclass) THEN
        CREATE POLICY no_client_access_source_runs ON public.source_runs FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_raw_ingestion_payloads' AND polrelid = 'public.raw_ingestion_payloads'::regclass) THEN
        CREATE POLICY no_client_access_raw_ingestion_payloads ON public.raw_ingestion_payloads FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_teams' AND polrelid = 'public.teams'::regclass) THEN
        CREATE POLICY no_client_access_teams ON public.teams FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_venues' AND polrelid = 'public.venues'::regclass) THEN
        CREATE POLICY no_client_access_venues ON public.venues FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_players' AND polrelid = 'public.players'::regclass) THEN
        CREATE POLICY no_client_access_players ON public.players FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_player_id_map' AND polrelid = 'public.player_id_map'::regclass) THEN
        CREATE POLICY no_client_access_player_id_map ON public.player_id_map FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_statcast_pitches' AND polrelid = 'public.statcast_pitches'::regclass) THEN
        CREATE POLICY no_client_access_statcast_pitches ON public.statcast_pitches FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_player_daily_batting_features' AND polrelid = 'public.player_daily_batting_features'::regclass) THEN
        CREATE POLICY no_client_access_player_daily_batting_features ON public.player_daily_batting_features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_player_daily_pitching_features' AND polrelid = 'public.player_daily_pitching_features'::regclass) THEN
        CREATE POLICY no_client_access_player_daily_pitching_features ON public.player_daily_pitching_features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_batter_pitcher_matchup_features' AND polrelid = 'public.batter_pitcher_matchup_features'::regclass) THEN
        CREATE POLICY no_client_access_batter_pitcher_matchup_features ON public.batter_pitcher_matchup_features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_park_factors' AND polrelid = 'public.park_factors'::regclass) THEN
        CREATE POLICY no_client_access_park_factors ON public.park_factors FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_weather_snapshots' AND polrelid = 'public.weather_snapshots'::regclass) THEN
        CREATE POLICY no_client_access_weather_snapshots ON public.weather_snapshots FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_sportsbooks' AND polrelid = 'public.sportsbooks'::regclass) THEN
        CREATE POLICY no_client_access_sportsbooks ON public.sportsbooks FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_historical_closing_odds' AND polrelid = 'public.historical_closing_odds'::regclass) THEN
        CREATE POLICY no_client_access_historical_closing_odds ON public.historical_closing_odds FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_pitcher_game_usage' AND polrelid = 'public.pitcher_game_usage'::regclass) THEN
        CREATE POLICY no_client_access_pitcher_game_usage ON public.pitcher_game_usage FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_team_rest_travel_features' AND polrelid = 'public.team_rest_travel_features'::regclass) THEN
        CREATE POLICY no_client_access_team_rest_travel_features ON public.team_rest_travel_features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'no_client_access_bullpen_fatigue_features' AND polrelid = 'public.bullpen_fatigue_features'::regclass) THEN
        CREATE POLICY no_client_access_bullpen_fatigue_features ON public.bullpen_fatigue_features FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
END $$;
