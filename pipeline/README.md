# Pipeline

## Run

```bash
python -m src.run_pipeline
```

## What it writes

```text
../web/public/data/dashboard.json
data/features/projections_today.parquet
data/features/team_market_value_daily_latest.parquet
data/features/model_metrics.json
```

## Replace demo data with real data

Add these files before running `src.run_pipeline`:

```text
data/features/projections_today.parquet
data/features/team_market_value_daily_latest.parquet
data/features/model_metrics.json
```

Expected `projections_today.parquet` columns:

```text
game_id
date
team
opponent
home_away
market
selection
decimal_odds
market_probability
base_probability
pitcher_adjustment
lineup_adjustment
handedness_adjustment
weather_adjustment
bullpen_adjustment
manual_override
manual_override_flag
model_confidence
```

The pipeline computes:

```text
final_probability
edge_pct
bet_signal
stake_pct_bankroll
stake_units
```
