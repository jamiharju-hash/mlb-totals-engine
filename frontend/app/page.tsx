'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from 'recharts';

type DashboardPayload = {
  summary?: {
    activeProjections?: number;
    betSignals?: number;
    strongBets?: number;
    avgEdgePct?: number | null;
    maxEdgePct?: number | null;
    totalStakeUnits?: number | null;
    positiveEdgeRate?: number | null;
    realizedRoiPct?: number | null;
    currentBankrollUnits?: number | null;
    clv?: { avgClvLast30d?: number | null; clvPositiveRate?: number | null; settledBets?: number };
    bestTeamValue?: { team: string; valueScore: number } | null;
  };
  topPicks?: Projection[];
  projections?: Projection[];
  teamMarket?: TeamMarket[];
  modelMetrics?: Record<string, unknown> | null;
  manualOverrides?: Override[];
  legacyDiagnostics?: { predictionsLogRows?: number; dailyMetricsRows?: number; oddsSnapshotsRows?: number };
  dataState?: {
    latestProjectionDate?: string | null;
    isStale?: boolean;
    isDemo?: boolean;
    warnings?: string[];
  };
};

type Projection = {
  id?: string | number;
  game_id?: string;
  team?: string;
  market?: string;
  selection?: string;
  edge_pct?: number;
  edge?: number;
  stake_units?: number;
  stake?: number;
  confidence?: string;
  model_total?: number;
  market_total?: number;
  bet_signal?: boolean;
};

type TeamMarket = { team?: string; market?: string; roi_pct?: number; value_score?: number };
type Override = { id?: string | number; reason?: string; active?: boolean; created_at?: string };

const KpiCard = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
    <div className="text-xs text-slate-400">{label}</div>
    <div className="mt-1 text-xl font-semibold text-white">{value}</div>
  </div>
);

const Skeleton = ({ className }: { className?: string }) => <div className={`animate-pulse rounded bg-slate-800 ${className ?? 'h-24'}`} />;

const fmtPct = (v?: number | null) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`);
const fmt = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(2));

export default function DashboardPage() {
  const [data, setData] = useState<DashboardPayload>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      if (!mounted) return;
      setLoading((prev) => (hasLoadedRef.current ? prev : true));
      try {
        const response = await fetch('/api/mlb-dashboard', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = (await response.json()) as DashboardPayload;
        if (!mounted) return;
        setData(payload ?? {});
        setError(null);
        setUpdatedAt(new Date());
        hasLoadedRef.current = true;
      } catch (e) {
        if (!mounted) return;
        setError(`Could not load dashboard. Check NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY and API route wiring. (${e instanceof Error ? e.message : 'unknown'})`);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();
    const id = setInterval(load, 30000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  const latestDate = data.dataState?.latestProjectionDate;
  const staleAge = useMemo(() => {
    if (!latestDate) return 0;
    const days = (Date.now() - new Date(latestDate).getTime()) / (1000 * 60 * 60 * 24);
    return days;
  }, [latestDate]);

  const topPicks = data.topPicks ?? [];
  const projections = data.projections ?? [];
  const teamMarket = data.teamMarket ?? [];
  const overrides = data.manualOverrides ?? [];

  const unavailable = (label: string) => <div className="text-sm text-amber-300">{label} unavailable in API payload.</div>;

  return (
    <main className="min-h-screen px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl space-y-6">
        {data.dataState?.isDemo ? <div className="rounded border border-rose-700 bg-rose-950/50 p-3 text-rose-200">Demo data — do not use for betting decisions.</div> : null}
        {staleAge >= 2 ? <div className="rounded border border-rose-700 bg-rose-950/50 p-3 text-rose-200">Data is stale (&gt;2 days old).</div> : null}
        {staleAge >= 1 && staleAge < 2 ? <div className="rounded border border-amber-600 bg-amber-950/40 p-3 text-amber-200">Data is stale (1+ day old).</div> : null}
        {error ? <div className="rounded border border-rose-700 bg-rose-950/50 p-3 text-rose-200">{error}</div> : null}

        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <h1 className="text-3xl font-semibold text-white">MLB Totals Engine</h1>
          <div className="mt-2 text-sm text-slate-300">Latest slate: {latestDate ?? 'Unknown'} • Model: {String(data.modelMetrics?.['model_version'] ?? 'Unknown')}</div>
          <div className="text-xs text-slate-400">Updated: {updatedAt ? updatedAt.toLocaleTimeString() : 'Loading...'}</div>
        </section>

        <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
          {loading && !data.summary
            ? Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} />)
            : [
                ['Active projections', String(data.summary?.activeProjections ?? '—')],
                ['Bet signals', String(data.summary?.betSignals ?? '—')],
                ['Strong bets', String(data.summary?.strongBets ?? '—')],
                ['Avg edge', fmtPct(data.summary?.avgEdgePct)],
                ['Max edge', fmtPct(data.summary?.maxEdgePct)],
                ['Total stake', fmt(data.summary?.totalStakeUnits)],
                ['Edge rate', fmtPct(data.summary?.positiveEdgeRate)],
                ['Realized ROI', fmtPct(data.summary?.realizedRoiPct)],
              ].map(([label, value]) => <KpiCard key={label} label={label} value={value} />)}
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Top opportunities</h2>{topPicks.length ? <div className="text-sm text-slate-300">{topPicks.slice(0, 3).map((p) => p.game_id ?? p.team).join(', ')}</div> : <div className="text-sm text-slate-400">No opportunities found.</div>}</div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Fade candidates</h2><div className="text-sm text-slate-400">No fade candidates found.</div></div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Operational warnings</h2>{data.dataState?.warnings?.length ? <ul className="list-disc pl-4 text-sm text-amber-300">{data.dataState.warnings.map((w) => <li key={w}>{w}</li>)}</ul> : <div className="text-sm text-slate-400">No operational warnings found.</div>}</div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          {['EdgeDistribution', 'ModelVsMarketScatter', 'StakeByMarket', 'SignalsByMarket'].map((name, i) => (
            <div key={name} className="h-72 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <h3 className="text-white">{name}</h3>
              {projections.length === 0 ? <div className="mt-6 text-sm text-slate-400">No {name} data found.</div> : <ResponsiveContainer width="100%" height="90%"><BarChart data={projections.slice(0, 10)}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis dataKey="team" stroke="#94a3b8" /><YAxis stroke="#94a3b8" /><Tooltip /><Bar dataKey={i % 2 === 0 ? 'edge_pct' : 'stake_units'} fill="#38bdf8" /></BarChart></ResponsiveContainer>}
            </div>
          ))}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-white">Projections table</h2>
          {loading && projections.length === 0 ? <Skeleton className="mt-3 h-40" /> : projections.length === 0 ? <div className="mt-3 text-sm text-slate-400">No projections found.</div> : <div className="mt-3 overflow-x-auto"><table className="w-full text-sm"><thead className="text-slate-400"><tr><th>Game</th><th>Team</th><th>Market</th><th>Selection</th><th>Edge</th><th>Stake</th></tr></thead><tbody>{projections.map((p, idx) => <tr key={p.id ?? idx} className="border-t border-slate-800 text-slate-200"><td>{p.game_id ?? '—'}</td><td>{p.team ?? '—'}</td><td>{p.market ?? '—'}</td><td>{p.selection ?? '—'}</td><td>{fmtPct(p.edge_pct ?? p.edge)}</td><td>{fmt(p.stake_units ?? p.stake)}</td></tr>)}</tbody></table></div>}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Team market value leaderboard</h2>{teamMarket.length ? <ol className="mt-2 list-decimal pl-5 text-slate-200">{teamMarket.slice(0, 5).map((t, i) => <li key={`${t.team}-${i}`}>{t.team ?? 'Unknown'} ({fmtPct(t.value_score)})</li>)}</ol> : <div className="text-sm text-slate-400">No team market values found.</div>}</div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Team market value table</h2>{teamMarket.length ? <div className="text-sm text-slate-300">{teamMarket.length} rows</div> : <div className="text-sm text-slate-400">No team market table rows found.</div>}</div>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Model health panel</h2>{data.modelMetrics ? <pre className="mt-2 overflow-x-auto text-xs text-slate-300">{JSON.stringify(data.modelMetrics, null, 2)}</pre> : unavailable('Model health')}</section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h2 className="text-white">Manual override audit</h2>{overrides.length ? <div className="text-sm text-slate-300">{overrides.length} overrides</div> : <div className="text-sm text-slate-400">No manual overrides found.</div>}</section>

        <details className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <summary className="cursor-pointer text-white">Legacy diagnostics</summary>
          {data.legacyDiagnostics ? <div className="mt-2 text-sm text-slate-300">predictions_log: {data.legacyDiagnostics.predictionsLogRows ?? 0}, daily_metrics: {data.legacyDiagnostics.dailyMetricsRows ?? 0}, odds_snapshots: {data.legacyDiagnostics.oddsSnapshotsRows ?? 0}</div> : <div className="mt-2 text-sm text-slate-400">No legacy diagnostics found.</div>}
        </details>
      </div>
    </main>
  );
}
