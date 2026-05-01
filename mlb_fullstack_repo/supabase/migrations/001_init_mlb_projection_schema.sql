create extension if not exists pgcrypto;

create table if not exists public.projections (
  id uuid primary key default gen_random_uuid(),
  game_id text not null,
  game_date date not null,
  team text not null,
  opponent text not null,
  home_away text not null check (home_away in ('home', 'away')),
  market text not null check (market in ('moneyline', 'runline', 'total')),
  selection text not null,
  decimal_odds numeric,
  american_odds numeric,
  market_probability numeric,
  base_probability numeric,
  final_probability numeric,
  edge_pct numeric,
  stake_units numeric,
  stake_pct_bankroll numeric,
  bet_signal text not null check (bet_signal in ('BET_STRONG', 'BET_SMALL', 'NO_BET', 'FADE')),
  model_confidence numeric,
  pitcher_adjustment numeric default 0,
  lineup_adjustment numeric default 0,
  handedness_adjustment numeric default 0,
  weather_adjustment numeric default 0,
  bullpen_adjustment numeric default 0,
  manual_override numeric default 0,
  manual_override_flag boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (game_id, team, market, selection)
);

create table if not exists public.team_market_features (
  id uuid primary key default gen_random_uuid(),
  as_of_date date not null,
  team text not null,
  ml_roi_ytd numeric default 0,
  rl_roi_ytd numeric default 0,
  ou_roi_ytd numeric default 0,
  ml_profit_ytd numeric default 0,
  rl_profit_ytd numeric default 0,
  ou_profit_ytd numeric default 0,
  value_score numeric default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (as_of_date, team)
);

create table if not exists public.model_metrics (
  id uuid primary key default gen_random_uuid(),
  as_of timestamptz not null,
  model_version text not null,
  test_mae_start_score numeric,
  test_auc_runline numeric,
  test_auc_moneyline numeric,
  simulated_roi_last_250 numeric,
  avg_clv_last_250 numeric,
  notes text,
  created_at timestamptz default now()
);

create table if not exists public.manual_overrides (
  id uuid primary key default gen_random_uuid(),
  game_id text not null,
  team text not null,
  market text not null,
  field text not null,
  original_value numeric,
  override_value numeric not null,
  reason text not null,
  analyst text,
  active boolean default true,
  created_at timestamptz default now()
);

alter table public.projections enable row level security;
alter table public.team_market_features enable row level security;
alter table public.model_metrics enable row level security;
alter table public.manual_overrides enable row level security;

drop policy if exists "Public read projections" on public.projections;
create policy "Public read projections" on public.projections for select using (true);

drop policy if exists "Public read team market features" on public.team_market_features;
create policy "Public read team market features" on public.team_market_features for select using (true);

drop policy if exists "Public read model metrics" on public.model_metrics;
create policy "Public read model metrics" on public.model_metrics for select using (true);

drop policy if exists "Public read manual overrides" on public.manual_overrides;
create policy "Public read manual overrides" on public.manual_overrides for select using (true);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists projections_set_updated_at on public.projections;
create trigger projections_set_updated_at before update on public.projections
for each row execute procedure public.set_updated_at();

drop trigger if exists team_market_features_set_updated_at on public.team_market_features;
create trigger team_market_features_set_updated_at before update on public.team_market_features
for each row execute procedure public.set_updated_at();

create index if not exists projections_game_date_idx on public.projections(game_date desc);
create index if not exists projections_signal_idx on public.projections(bet_signal);
create index if not exists team_market_as_of_idx on public.team_market_features(as_of_date desc);
create index if not exists model_metrics_as_of_idx on public.model_metrics(as_of desc);
