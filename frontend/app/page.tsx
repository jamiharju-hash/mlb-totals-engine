'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { supabase } from '../lib/supabase';

type Summary = {
  todays_games: number;
  active_signals: number;
  avg_clv_7d: number;
  rolling_roi_30d: number;
  bet_count_today: number;
  data_lag_seconds: number;
};

type Prediction = {
  id: number;
  game_id: string;
  prediction_timestamp: string;
  side: 'OVER' | 'UNDER' | 'PASS';
  should_bet: boolean;
  market_total: number;
  calibrated_model_total: number;
  edge_runs: number;
  expected_value: number;
  stake: number;
  confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  truth_status: 'PENDING' | 'READY' | 'VOID';
  clv: number | null;
  roi: number | null;
};

type DailyMetric = {
  metric_date: string;
  avg_clv: number;
  roi: number;
  bets: number;
  p95_latency_ms: number;
  max_data_lag_seconds: number;
  success_criteria_pass: boolean;
};

function formatPct(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatNumber(value: number, decimals = 2) {
  return Number(value ?? 0).toFixed(decimals);
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-sm">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight text-white">{value}</div>
      {sub ? <div className="mt-1 text-xs text-slate-500">{sub}</div> : null}
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [signals, setSignals] = useState<Prediction[]>([]);
  const [metrics, setMetrics] = useState<DailyMetric[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      const [summaryResult, signalsResult, metricsResult] = await Promise.all([
        supabase.from('dashboard_summary').select('*').single(),
        supabase
          .from('predictions_log')
          .select('id,game_id,prediction_timestamp,side,should_bet,market_total,calibrated_model_total,edge_runs,expected_value,stake,confidence,truth_status,clv,roi')
          .eq('should_bet', true)
          .order('prediction_timestamp', { ascending: false })
          .limit(20),
        supabase
          .from('daily_metrics')
          .select('metric_date,avg_clv,roi,bets,p95_latency_ms,max_data_lag_seconds,success_criteria_pass')
          .order('metric_date', { ascending: true })
          .limit(30),
      ]);

      const firstError = summaryResult.error || signalsResult.error || metricsResult.error;
      if (firstError) {
        setError(firstError.message);
      } else {
        setSummary(summaryResult.data as Summary);
        setSignals((signalsResult.data ?? []) as Prediction[]);
        setMetrics((metricsResult.data ?? []) as DailyMetric[]);
        setError(null);
      }
      setLoading(false);
    }

    loadDashboard();
  }, []);

  const successGate = useMemo(() => {
    const latest = metrics.at(-1);
    if (!latest) return 'No metrics yet';
    return latest.success_criteria_pass ? 'PASS' : 'FAIL';
  }, [metrics]);

  return (
    <main className="min-h-screen px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-slate-500">MLB Totals Engine</p>
            <h1 className="mt-2 text-4xl font-semibold text-white">CLV-first betting intelligence</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">
              Internal operator dashboard for predictions, active +EV signals, CLV validation, ROI and data freshness.
            </p>
          </div>
          <div className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
            Success criteria: <span className={successGate === 'PASS' ? 'text-emerald-400' : 'text-rose-400'}>{successGate}</span>
          </div>
        </div>

        {loading ? <div className="text-slate-400">Loading dashboard...</div> : null}
        {error ? <div className="rounded-xl border border-rose-900 bg-rose-950/40 p-4 text-rose-200">{error}</div> : null}

        {summary ? (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
            <StatCard label="Today's games" value={String(summary.todays_games)} />
            <StatCard label="Active signals" value={String(summary.active_signals)} />
            <StatCard label="Avg CLV 7d" value={formatPct(summary.avg_clv_7d)} sub="Target > +1.0%" />
            <StatCard label="Rolling ROI 30d" value={formatPct(summary.rolling_roi_30d)} sub="Target > 3.0%" />
            <StatCard label="Bet count today" value={String(summary.bet_count_today)} />
            <StatCard label="Data lag" value={`${formatNumber(summary.data_lag_seconds, 0)}s`} sub="Target < 60s" />
          </section>
        ) : null}

        <section className="mt-8 grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-lg font-semibold text-white">Avg CLV</h2>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="metric_date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155' }} />
                  <Line type="monotone" dataKey="avg_clv" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-lg font-semibold text-white">Rolling ROI</h2>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="metric_date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155' }} />
                  <Line type="monotone" dataKey="roi" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Active / recent signals</h2>
            <span className="text-xs text-slate-500">Read-only Supabase client</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-3 pr-4">Time</th>
                  <th className="py-3 pr-4">Game</th>
                  <th className="py-3 pr-4">Side</th>
                  <th className="py-3 pr-4">Model</th>
                  <th className="py-3 pr-4">Market</th>
                  <th className="py-3 pr-4">Edge</th>
                  <th className="py-3 pr-4">EV</th>
                  <th className="py-3 pr-4">Stake</th>
                  <th className="py-3 pr-4">CLV</th>
                  <th className="py-3 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((signal) => (
                  <tr key={signal.id} className="border-b border-slate-800/70 text-slate-300">
                    <td className="py-3 pr-4 text-xs text-slate-500">{new Date(signal.prediction_timestamp).toLocaleString()}</td>
                    <td className="py-3 pr-4 font-medium text-white">{signal.game_id}</td>
                    <td className="py-3 pr-4">{signal.side}</td>
                    <td className="py-3 pr-4">{formatNumber(signal.calibrated_model_total)}</td>
                    <td className="py-3 pr-4">{formatNumber(signal.market_total)}</td>
                    <td className="py-3 pr-4">{formatNumber(signal.edge_runs)}</td>
                    <td className="py-3 pr-4">{formatPct(signal.expected_value)}</td>
                    <td className="py-3 pr-4">{formatNumber(signal.stake)}</td>
                    <td className="py-3 pr-4">{signal.clv === null ? '—' : formatNumber(signal.clv)}</td>
                    <td className="py-3 pr-4">{signal.truth_status}</td>
                  </tr>
                ))}
                {signals.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-6 text-center text-slate-500">
                      No logged signals yet.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
