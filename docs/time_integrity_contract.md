# Time Integrity Contract

This contract is mandatory for every prediction, backtest, CLV calculation, and model evaluation in MLB Totals Engine.

Any violation invalidates the affected record and excludes it from production performance metrics.

## Core Rule

All data used in predictions must be time-consistent relative to the prediction timestamp.

```text
feature_timestamp <= prediction_timestamp
market_snapshot_timestamp <= prediction_timestamp
prediction_timestamp <= closing_snapshot_timestamp <= game_start_timestamp
result_finalized_at >= game_start_timestamp
```

No post-game data may be used in features, model inputs, calibration inputs, or market inputs.

## Required Invariants

### 1. Feature Timestamp

Every feature row must have a `feature_timestamp`.

Allowed:

```text
feature_timestamp <= prediction_timestamp
```

Forbidden:

```text
feature_timestamp > prediction_timestamp
```

Examples of forbidden leakage:

- final score
- post-game boxscore
- post-game bullpen usage
- lineup information not yet confirmed at prediction time
- pitcher stats updated after the prediction timestamp
- weather data observed after first pitch, unless explicitly modeled as pre-game forecast only

## 2. Market Line Used for Prediction

The market line used by the model and EV engine must be the line available at prediction time.

Allowed:

```text
market_snapshot_timestamp <= prediction_timestamp
```

Selection rule:

```text
market_snapshot = latest odds snapshot where timestamp <= prediction_timestamp
```

Forbidden:

- using a later line movement snapshot
- using closing line as the prediction-time market line
- replacing the logged market line after prediction
- backfilling missing market line with a future snapshot

## 3. Closing Line Reconstruction

Closing line must be reconstructed as the last available valid market line before game start.

Allowed:

```text
closing_snapshot_timestamp <= game_start_timestamp
```

Selection rule:

```text
closing_snapshot = latest odds snapshot where timestamp <= game_start_timestamp
```

Preferred additional rule:

```text
closing_snapshot_timestamp >= prediction_timestamp
```

If no valid closing snapshot exists before game start, the prediction must remain unevaluated for CLV.

Forbidden:

- using any snapshot after game start
- using any post-game line
- using latest available snapshot without a game-start cutoff
- calculating CLV when game start timestamp is missing or unreliable

## 4. No Post-Game Data in Features

Feature engineering must exclude all post-game and future-known information.

Forbidden feature examples:

- final score
- total runs
- post-game win/loss information
- boxscore outcomes
- actual bullpen usage from the predicted game
- final confirmed result metadata
- closing line movement if prediction occurred earlier
- any data created or updated after prediction timestamp

Allowed feature examples, if timestamped correctly:

- probable pitchers known before prediction
- confirmed lineups only if confirmed before prediction
- pre-game park factor
- pre-game weather forecast
- team rolling stats calculated only from previous completed games
- bullpen fatigue calculated only from games completed before prediction
- market total available at prediction time

## Invalidated Outputs

If any rule is violated, the following outputs are invalid for the affected prediction:

- CLV
- backtest result
- ROI
- model evaluation metrics
- edge bucket analysis
- calibration analysis
- success criteria reporting

Invalid records must not contribute to:

- `daily_metrics.avg_clv`
- `daily_metrics.clv_win_rate`
- `daily_metrics.roi`
- `model_runs.clv_avg`
- production readiness claims

## Database Fields That Must Preserve the Contract

Canonical table:

```text
predictions_log
```

Required fields:

```text
prediction_timestamp
feature_timestamp
market_snapshot_id
market_snapshot_timestamp
closing_snapshot_id
closing_snapshot_timestamp
result_finalized_at
truth_status
```

Supporting tables:

```text
features
odds_snapshots
games
game_results
prediction_truth_links
daily_metrics
```

## Truth Status Rules

### `PENDING`

Use when:

- prediction has been logged
- result is not finalized
- closing snapshot has not been attached
- time integrity is not yet fully verifiable

### `READY`

Use only when all required links are valid:

```text
feature_timestamp <= prediction_timestamp
market_snapshot_timestamp <= prediction_timestamp
prediction_timestamp <= closing_snapshot_timestamp <= game_start_timestamp
result_finalized_at >= game_start_timestamp
```

### `VOID`

Use when:

- market snapshot is missing
- closing snapshot is missing
- game start timestamp is missing or unreliable
- game was postponed/cancelled
- any timestamp invariant is violated
- post-game leakage is detected

VOID records must remain auditable but excluded from performance metrics.

## Implementation Requirements

### Prediction Logging

When `/predict` is called with `log_decision = true`, the service must:

1. capture `request_received_at`
2. set `prediction_timestamp = request_received_at`
3. select the latest market snapshot where `timestamp <= prediction_timestamp`
4. store `market_snapshot_id` and `market_snapshot_timestamp`
5. store feature timestamp if available
6. write the record to `predictions_log` with `truth_status = PENDING`

### Closing Line Worker

The post-game metrics worker must:

1. fetch game start timestamp from `games.game_datetime`
2. select latest odds snapshot where `timestamp <= game_datetime`
3. attach that snapshot as closing line
4. refuse CLV calculation if no valid closing snapshot exists
5. attach final result only after game is final
6. mark record `READY` only if all timestamp checks pass

### Metrics Worker

The metrics worker must exclude records where:

```text
truth_status != 'READY'
```

or where any of these are missing:

```text
closing_total
total_runs
clv
pnl
```

### Backtesting

Backtests must reconstruct the historical state as if running live.

For each historical prediction:

```text
features = latest feature set where feature_timestamp <= prediction_timestamp
market_line = latest odds snapshot where timestamp <= prediction_timestamp
closing_line = latest odds snapshot where timestamp <= game_start_timestamp
result = final result after game completion
```

Any row that cannot satisfy this reconstruction must be excluded or marked `VOID`.

## Hard Failure Conditions

The system must fail closed rather than silently evaluate invalid records.

Fail closed means:

- do not compute CLV
- do not compute ROI
- do not include in dashboard success criteria
- do not include in model validation
- mark as `VOID` with a reason where possible

## Summary

Time integrity is not a best practice in this project. It is a validity requirement.

A prediction is only evaluable if the system can prove what was known at prediction time and what the true closing market was before game start.
