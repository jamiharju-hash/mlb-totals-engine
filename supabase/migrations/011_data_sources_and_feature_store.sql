-- Data source provenance, entity dimensions, feature store, and market context tables.

CREATE TABLE IF NOT EXISTS public.data_sources (
  id BIGSERIAL PRIMARY KEY,
  source_key TEXT UNIQUE NOT NULL,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  cost_type TEXT NOT NULL CHECK (cost_type IN ('free','free_tier','manual_free')),
  base_url TEXT,
  auth_type TEXT NOT NULL DEFAULT 'none',
  license_notes TEXT,
  reliability_tier INT NOT NULL CHECK (reliability_tier BETWEEN 1 AND 5),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.source_runs (
  id BIGSERIAL PRIMARY KEY,
  source_key TEXT NOT NULL REFERENCES public.data_sources(source_key),
  run_type TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('running','success','failed','partial')),
  rows_inserted INT DEFAULT 0,
  rows_updated INT DEFAULT 0,
  error_message TEXT,
  request_url TEXT,
  request_params JSONB,
  response_metadata JSONB
);

CREATE TABLE IF NOT EXISTS public.raw_ingestion_payloads (
  id BIGSERIAL PRIMARY KEY,
  source_run_id BIGINT REFERENCES public.source_runs(id),
  source_key TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  payload JSONB NOT NULL,
  payload_hash TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (source_key, entity_type, entity_id, payload_hash)
);

CREATE TABLE IF NOT EXISTS public.teams (
  team_id TEXT PRIMARY KEY,
  mlbam_team_id INT UNIQUE,
  name TEXT NOT NULL,
  abbreviation TEXT,
  league TEXT,
  division TEXT,
  active_from INT,
  active_to INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.venues (
  venue_id TEXT PRIMARY KEY,
  mlbam_venue_id INT UNIQUE,
  name TEXT NOT NULL,
  city TEXT,
  state TEXT,
  country TEXT,
  latitude NUMERIC,
  longitude NUMERIC,
  elevation_m NUMERIC,
  roof_type TEXT CHECK (roof_type IN ('open','retractable','dome','unknown')),
  surface TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS public.players (
  player_id TEXT PRIMARY KEY,
  mlbam_id INT UNIQUE,
  full_name TEXT NOT NULL,
  birth_date DATE,
  bats TEXT CHECK (bats IN ('L','R','S','unknown')),
  throws TEXT CHECK (throws IN ('L','R','unknown')),
  primary_position TEXT,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.player_id_map (
  id BIGSERIAL PRIMARY KEY,
  player_id TEXT REFERENCES public.players(player_id),
  mlbam_id INT,
  retrosheet_id TEXT,
  bbref_id TEXT,
  fangraphs_id TEXT,
  chadwick_key TEXT,
  source_key TEXT NOT NULL DEFAULT 'chadwick_register',
  valid_from DATE,
  valid_to DATE,
  UNIQUE (player_id, source_key)
);

CREATE TABLE IF NOT EXISTS public.statcast_pitches (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT REFERENCES public.games(game_id),
  mlbam_game_pk INT,
  game_date DATE NOT NULL,
  at_bat_number INT,
  pitch_number INT,
  inning INT,
  inning_topbot TEXT CHECK (inning_topbot IN ('Top','Bot')),
  batter_id TEXT REFERENCES public.players(player_id),
  pitcher_id TEXT REFERENCES public.players(player_id),
  batter_stand TEXT CHECK (batter_stand IN ('L','R')),
  pitcher_throws TEXT CHECK (pitcher_throws IN ('L','R')),
  home_team_id TEXT REFERENCES public.teams(team_id),
  away_team_id TEXT REFERENCES public.teams(team_id),
  pitch_type TEXT,
  release_speed NUMERIC,
  release_spin_rate NUMERIC,
  pfx_x NUMERIC,
  pfx_z NUMERIC,
  plate_x NUMERIC,
  plate_z NUMERIC,
  zone INT,
  balls INT,
  strikes INT,
  outs_when_up INT,
  on_1b TEXT,
  on_2b TEXT,
  on_3b TEXT,
  events TEXT,
  description TEXT,
  launch_speed NUMERIC,
  launch_angle NUMERIC,
  estimated_ba_using_speedangle NUMERIC,
  estimated_woba_using_speedangle NUMERIC,
  woba_value NUMERIC,
  xwoba_value NUMERIC,
  hit_distance_sc NUMERIC,
  bb_type TEXT,
  source_key TEXT NOT NULL DEFAULT 'baseball_savant_statcast',
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (mlbam_game_pk, at_bat_number, pitch_number)
);

CREATE INDEX IF NOT EXISTS idx_statcast_pitcher_date ON public.statcast_pitches (pitcher_id, game_date);
CREATE INDEX IF NOT EXISTS idx_statcast_batter_date ON public.statcast_pitches (batter_id, game_date);
CREATE INDEX IF NOT EXISTS idx_statcast_handedness ON public.statcast_pitches (batter_stand, pitcher_throws);
CREATE INDEX IF NOT EXISTS idx_statcast_game ON public.statcast_pitches (game_id);

CREATE TABLE IF NOT EXISTS public.player_daily_batting_features (
  id BIGSERIAL PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES public.players(player_id),
  as_of_date DATE NOT NULL,
  split_pitcher_throws TEXT CHECK (split_pitcher_throws IN ('L','R','ALL')),
  rolling_window_days INT NOT NULL,
  pa INT,
  ab INT,
  k_rate NUMERIC,
  bb_rate NUMERIC,
  avg NUMERIC,
  obp NUMERIC,
  slg NUMERIC,
  iso NUMERIC,
  woba NUMERIC,
  xwoba NUMERIC,
  xba NUMERIC,
  xslg NUMERIC,
  barrel_rate NUMERIC,
  hard_hit_rate NUMERIC,
  avg_exit_velocity NUMERIC,
  avg_launch_angle NUMERIC,
  source_key TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (player_id, as_of_date, split_pitcher_throws, rolling_window_days)
);

CREATE TABLE IF NOT EXISTS public.player_daily_pitching_features (
  id BIGSERIAL PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES public.players(player_id),
  as_of_date DATE NOT NULL,
  split_batter_stand TEXT CHECK (split_batter_stand IN ('L','R','ALL')),
  rolling_window_days INT NOT NULL,
  batters_faced INT,
  innings_pitched NUMERIC,
  pitch_count INT,
  k_rate NUMERIC,
  bb_rate NUMERIC,
  hr_rate NUMERIC,
  groundball_rate NUMERIC,
  flyball_rate NUMERIC,
  whiff_rate NUMERIC,
  csw_rate NUMERIC,
  xwoba_allowed NUMERIC,
  xba_allowed NUMERIC,
  xslg_allowed NUMERIC,
  barrel_rate_allowed NUMERIC,
  hard_hit_rate_allowed NUMERIC,
  avg_release_speed NUMERIC,
  release_speed_delta NUMERIC,
  pitch_mix JSONB,
  source_key TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (player_id, as_of_date, split_batter_stand, rolling_window_days)
);

CREATE TABLE IF NOT EXISTS public.batter_pitcher_matchup_features (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT REFERENCES public.games(game_id),
  batter_id TEXT NOT NULL REFERENCES public.players(player_id),
  pitcher_id TEXT NOT NULL REFERENCES public.players(player_id),
  as_of_date DATE NOT NULL,
  batter_vs_hand_pa INT,
  batter_vs_hand_xwoba NUMERIC,
  batter_vs_pitch_mix_score NUMERIC,
  pitcher_vs_hand_bf INT,
  pitcher_vs_hand_xwoba_allowed NUMERIC,
  pitcher_pitch_mix JSONB,
  matchup_k_probability NUMERIC,
  matchup_bb_probability NUMERIC,
  matchup_hit_probability NUMERIC,
  matchup_hr_probability NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (game_id, batter_id, pitcher_id)
);

CREATE TABLE IF NOT EXISTS public.park_factors (
  id BIGSERIAL PRIMARY KEY,
  venue_id TEXT NOT NULL REFERENCES public.venues(venue_id),
  season INT NOT NULL,
  factor_type TEXT NOT NULL,
  bat_side TEXT CHECK (bat_side IN ('L','R','ALL')),
  condition TEXT DEFAULT 'ALL',
  factor_value NUMERIC NOT NULL,
  rolling_years INT DEFAULT 3,
  source_key TEXT NOT NULL DEFAULT 'baseball_savant_park_factors',
  observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (venue_id, season, factor_type, bat_side, condition, rolling_years)
);

CREATE TABLE IF NOT EXISTS public.weather_snapshots (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT REFERENCES public.games(game_id),
  venue_id TEXT REFERENCES public.venues(venue_id),
  source_key TEXT NOT NULL,
  forecast_for TIMESTAMPTZ NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  temperature_c NUMERIC,
  humidity_pct NUMERIC,
  wind_speed_kph NUMERIC,
  wind_direction_deg NUMERIC,
  precipitation_mm NUMERIC,
  pressure_hpa NUMERIC,
  cloud_cover_pct NUMERIC,
  weather_code TEXT,
  roof_status TEXT CHECK (roof_status IN ('open','closed','dome','unknown')) DEFAULT 'unknown',
  is_forecast BOOLEAN NOT NULL DEFAULT TRUE,
  raw_payload JSONB,
  UNIQUE (game_id, source_key, forecast_for, observed_at)
);

CREATE TABLE IF NOT EXISTS public.sportsbooks (
  sportsbook_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  region TEXT,
  source_key TEXT,
  active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS public.historical_closing_odds (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT REFERENCES public.games(game_id),
  source_key TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  season INT NOT NULL,
  game_date DATE NOT NULL,
  home_team_id TEXT REFERENCES public.teams(team_id),
  away_team_id TEXT REFERENCES public.teams(team_id),
  home_open_decimal NUMERIC,
  away_open_decimal NUMERIC,
  home_close_decimal NUMERIC,
  away_close_decimal NUMERIC,
  total_open NUMERIC,
  total_close NUMERIC,
  over_close_decimal NUMERIC,
  under_close_decimal NUMERIC,
  home_run_line NUMERIC,
  away_run_line NUMERIC,
  home_run_line_close_decimal NUMERIC,
  away_run_line_close_decimal NUMERIC,
  raw_payload JSONB,
  UNIQUE (dataset_name, game_date, home_team_id, away_team_id)
);

CREATE TABLE IF NOT EXISTS public.pitcher_game_usage (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT NOT NULL REFERENCES public.games(game_id),
  player_id TEXT NOT NULL REFERENCES public.players(player_id),
  team_id TEXT NOT NULL REFERENCES public.teams(team_id),
  game_date DATE NOT NULL,
  role TEXT CHECK (role IN ('starter','reliever','opener','bulk','unknown')),
  pitches_thrown INT,
  batters_faced INT,
  innings_pitched NUMERIC,
  high_leverage_flag BOOLEAN DEFAULT FALSE,
  source_key TEXT NOT NULL,
  UNIQUE (game_id, player_id)
);

CREATE TABLE IF NOT EXISTS public.team_rest_travel_features (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT NOT NULL REFERENCES public.games(game_id),
  team_id TEXT NOT NULL REFERENCES public.teams(team_id),
  as_of_date DATE NOT NULL,
  rest_days INT,
  games_last_7 INT,
  games_last_14 INT,
  road_games_last_10 INT,
  previous_game_date DATE,
  previous_venue_id TEXT REFERENCES public.venues(venue_id),
  timezone_shift_hours NUMERIC,
  travel_distance_km NUMERIC,
  eastward_travel_flag BOOLEAN,
  day_after_night_flag BOOLEAN,
  doubleheader_recent_flag BOOLEAN,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (game_id, team_id)
);

CREATE TABLE IF NOT EXISTS public.bullpen_fatigue_features (
  id BIGSERIAL PRIMARY KEY,
  game_id TEXT NOT NULL REFERENCES public.games(game_id),
  team_id TEXT NOT NULL REFERENCES public.teams(team_id),
  as_of_date DATE NOT NULL,
  bullpen_pitches_last_1d INT,
  bullpen_pitches_last_2d INT,
  bullpen_pitches_last_3d INT,
  relievers_used_last_1d INT,
  relievers_used_last_2d INT,
  relievers_used_last_3d INT,
  back_to_back_relievers INT,
  closer_available_probability NUMERIC,
  setup_available_probability NUMERIC,
  projected_bullpen_quality NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (game_id, team_id)
);
