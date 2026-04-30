-- Metrics endpoint and edge bucket analysis support.
-- Canonical CLV: closing_line - market_line_at_prediction for OVER,
-- and market_line_at_prediction - closing_line for UNDER.

CREATE OR REPLACE VIEW public.metrics_summary AS
SELECT
    COALESCE(SUM(CASE WHEN should_bet THEN 1 ELSE 0 END), 0)::INTEGER AS bet_count,
    COALESCE(SUM(pnl), 0) AS pnl,
    COALESCE(SUM(stake), 0) AS total_staked,
    CASE
        WHEN COALESCE(SUM(stake), 0) > 0 THEN COALESCE(SUM(pnl), 0) / SUM(stake)
        ELSE 0
    END AS roi,
    COALESCE(AVG(clv), 0) AS avg_clv,
    CASE
        WHEN COUNT(*) FILTER (WHERE should_bet AND clv IS NOT NULL) > 0
        THEN COUNT(*) FILTER (WHERE should_bet AND clv > 0)::NUMERIC / COUNT(*) FILTER (WHERE should_bet AND clv IS NOT NULL)
        ELSE 0
    END AS clv_win_rate,
    CASE
        WHEN COUNT(*) FILTER (WHERE should_bet AND pnl IS NOT NULL) > 0
        THEN COUNT(*) FILTER (WHERE should_bet AND pnl > 0)::NUMERIC / COUNT(*) FILTER (WHERE should_bet AND pnl IS NOT NULL)
        ELSE 0
    END AS win_rate,
    COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
    COALESCE(MAX(EXTRACT(EPOCH FROM (NOW() - market_snapshot_timestamp))), 0) AS data_lag_seconds
FROM public.predictions_log
WHERE should_bet = true
  AND truth_status = 'READY';

CREATE OR REPLACE VIEW public.edge_bucket_analysis AS
SELECT
    CASE
        WHEN ABS(edge_runs) >= 0.2 AND ABS(edge_runs) < 0.4 THEN '0.2-0.4'
        WHEN ABS(edge_runs) >= 0.4 AND ABS(edge_runs) < 0.6 THEN '0.4-0.6'
        WHEN ABS(edge_runs) >= 0.6 THEN '0.6+'
        ELSE '<0.2'
    END AS edge_bucket,
    COUNT(*)::INTEGER AS bet_count,
    COALESCE(AVG(clv), 0) AS avg_clv,
    COALESCE(SUM(pnl), 0) AS pnl,
    COALESCE(SUM(stake), 0) AS total_staked,
    CASE
        WHEN COALESCE(SUM(stake), 0) > 0 THEN COALESCE(SUM(pnl), 0) / SUM(stake)
        ELSE 0
    END AS roi,
    CASE
        WHEN COUNT(*) FILTER (WHERE clv IS NOT NULL) > 0
        THEN COUNT(*) FILTER (WHERE clv > 0)::NUMERIC / COUNT(*) FILTER (WHERE clv IS NOT NULL)
        ELSE 0
    END AS clv_win_rate
FROM public.predictions_log
WHERE should_bet = true
  AND truth_status = 'READY'
  AND ABS(edge_runs) >= 0.2
GROUP BY 1
ORDER BY
    CASE
        WHEN CASE
            WHEN ABS(edge_runs) >= 0.2 AND ABS(edge_runs) < 0.4 THEN '0.2-0.4'
            WHEN ABS(edge_runs) >= 0.4 AND ABS(edge_runs) < 0.6 THEN '0.4-0.6'
            WHEN ABS(edge_runs) >= 0.6 THEN '0.6+'
            ELSE '<0.2'
        END = '0.2-0.4' THEN 1
        WHEN CASE
            WHEN ABS(edge_runs) >= 0.2 AND ABS(edge_runs) < 0.4 THEN '0.2-0.4'
            WHEN ABS(edge_runs) >= 0.4 AND ABS(edge_runs) < 0.6 THEN '0.4-0.6'
            WHEN ABS(edge_runs) >= 0.6 THEN '0.6+'
            ELSE '<0.2'
        END = '0.4-0.6' THEN 2
        WHEN CASE
            WHEN ABS(edge_runs) >= 0.2 AND ABS(edge_runs) < 0.4 THEN '0.2-0.4'
            WHEN ABS(edge_runs) >= 0.4 AND ABS(edge_runs) < 0.6 THEN '0.4-0.6'
            WHEN ABS(edge_runs) >= 0.6 THEN '0.6+'
            ELSE '<0.2'
        END = '0.6+' THEN 3
        ELSE 4
    END;

DROP POLICY IF EXISTS "dashboard_read_metrics_summary" ON public.predictions_log;
-- Views rely on underlying predictions_log SELECT policy created in migration 006.
