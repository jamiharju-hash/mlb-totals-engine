# Evaluation and Prediction Logging Contract

This document defines canonical CLV, immutable prediction logging, data lifecycle, metrics API expectations, edge bucket analysis, no-hidden-state rules, and Odds API limitations.

## 1. Canonical CLV Definition

CLV compares the market line available at prediction time against the final valid closing line.

For OVER decisions:

```text
CLV = closing_line - market_line_at_prediction
```

For UNDER decisions:

```text
CLV = market_line_at_prediction - closing_line
```

The following are invalid definitions:

```text
closing_line - predicted_line
predicted_line - closing_line
```

A positive CLV means the decision beat the closing market.

CLV must never be calculated from model predicted total. The model prediction is used to create the decision. The market line at prediction time and the reconstructed closing line are used to evaluate market-beating quality.

## 2. Prediction Logging Contract

Every logged prediction must include:

```text
game_id
predicted_total
market_line_at_prediction
over_price
under_price
edge
decision
created_at UTC
```

In this repository, the canonical table is:

```text
predictions_log
```

Field mapping:

```text
predicted_total              -> calibrated_model_total
market_line_at_prediction    -> market_total
edge                          -> edge_runs
decision                      -> side
created_at UTC               -> prediction_timestamp / created_at
```

Required additional integrity fields:

```text
raw_model_total
estimated_probability
break_even_probability
expected_value
stake
market_snapshot_id
market_snapshot_timestamp
feature_timestamp
closing_snapshot_id
closing_snapshot_timestamp
result_finalized_at
truth_status
```

## 3. Immutability Rule

A logged prediction record is immutable with respect to the original decision inputs and outputs.

After insertion, do not mutate:

```text
game_id
prediction_timestamp
feature_timestamp
market_snapshot_id
market_snapshot_timestamp
market_total
over_price
under_price
raw_model_total
calibrated_model_total
edge_runs
side
estimated_probability
break_even_probability
expected_value
stake
confidence
reason
calibration
features
payload
```

Allowed post-game updates are restricted to evaluation fields:

```text
closing_snapshot_id
closing_snapshot_timestamp
closing_total
total_runs
clv
pnl
roi
truth_status
updated_at
```

## 4. Data Lifecycle

### T-24h: Opening Odds Snapshot

- Start collecting odds snapshots.
- Tag earliest available market as `opening` where possible.
- Do not assume this is stable or final.

### T-3h: Lineup Confirmation and Pre-Game Prediction Window

- Ingest probable pitchers and lineup confirmation flags.
- Build features only from data known at the feature timestamp.
- Generate predictions during the approved pre-game window.
- Log decisions to `predictions_log` if `log_decision = true`.

### T-0h: Closing Line Captured

- Closing line is reconstructed from odds snapshots.
- Canonical closing line is the last available valid line before game start.
- Do not rely on a single fetch.
- Do not use a snapshot after game start.

### T+Game: Results Ingested

- Ingest final score and total runs.
- Store final ground truth in `game_results`.

### Post-Game: CLV and ROI Calculated

- Attach closing snapshot to predictions.
- Attach result.
- Calculate CLV, PnL, ROI.
- Mark record `READY` only if the Time Integrity Contract is satisfied.
- Mark record `VOID` if timestamps are invalid or required data is missing.

## 5. GET /metrics Contract

Endpoint:

```text
GET /metrics
```

Returns:

```text
ROI
CLV
CLV win rate
bet count
win rate
total staked
PnL
average latency
current data lag
edge bucket analysis
```

The dashboard should use this endpoint or equivalent Supabase read models.

Metrics must include only records where:

```text
truth_status = READY
should_bet = true
```

VOID and PENDING records must be excluded from production performance claims.

## 6. Edge Bucket Analysis View

Purpose:

Identify where real edge exists by grouping realized performance by model edge size.

Canonical buckets:

```text
0.2-0.4
0.4-0.6
0.6+
```

Metrics per bucket:

```text
CLV
ROI
bet count
CLV win rate
PnL
total staked
```

Database view:

```text
edge_bucket_analysis
```

Use this to detect whether small edges are noise and whether larger edges actually produce better CLV and ROI.

## 7. No Hidden State Rule

The system must be reproducible from explicit inputs and database records.

Rules:

- No global mutable prediction state.
- No cached predictions reused across games.
- No undocumented in-memory overrides.
- No silent fallback to future market data.
- All outputs must be reproducible from logged input data.
- Every production decision must be traceable to a model version, feature version, feature timestamp, and market snapshot.

Allowed caches:

- Read-through caches for static config or model artifacts.
- Database query caching only when it cannot change the selected historical snapshot.

Forbidden caches:

- Reusing a previous prediction for another game.
- Reusing a stale market snapshot when a newer valid pre-prediction snapshot exists.
- Caching closing lines without storing the referenced snapshot ID.

## 8. Odds API Limitation

The Odds API free tier does not guarantee real closing lines and may have latency.

System requirements:

- Reconstruct closing line from stored snapshots.
- Do not rely on one fetch near game start.
- Store every odds snapshot with timestamp.
- Tag market phase where possible.
- Treat missing or late snapshots as evaluation risk.
- Mark CLV as PENDING or VOID if closing line cannot be reconstructed reliably.

Production implication:

A CLV result is only credible if the system can prove the closing snapshot was captured before game start and was not backfilled from post-start or post-game data.
