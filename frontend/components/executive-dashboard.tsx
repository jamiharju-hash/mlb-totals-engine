'use client';

import { useEffect, useMemo, useState } from 'react';
import type { DashboardPayload, DbRow } from '../lib/dashboard-data';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type SortDirection = 'asc' | 'desc';
type ProjectionSortKey =
  | 'game_date'
  | 'bet_signal'
  | 'team'
  | 'opponent'
  | 'home_away'
  | 'market'
  | 'selection'
  | 'decimal_odds'
  | 'final_probability'
  | 'market_probability'
  | 'edge_pct'
  | 'model_confidence'
  | 'stake_units'
  | 'manual_override_flag';

type ChartPoint = {
  team: string;
  opponent: string;
  market: string;
  selection: string;
  signal: string;
  marketProbability: number;
  modelProbability: number;
  edge: number;
  stake: number;
  color: string;
};

const SIGNAL_COLORS: Record<string, string> = {
  BET_STRONG: '#10b981',
  BET_SMALL: '#38bdf8',
  BET: '#22c55e',
  ACTIONABLE: '#22c55e',
  PASS: '#64748b',
  NO_BET: '#64748b',
  FADE: '#f43f5e',
  UNKNOWN: '#64748b',
};

const MARKETS = ['moneyline', 'runline', 'total'];
const SIGNALS = ['BET_STRONG', 'BET_SMALL', 'PASS', 'FADE'];
const PROJECTION_CSV_FIELDS = [
  'game_date',
  'team',
  'opponent',
  'market',
  'selection',
  'decimal_odds',
  'market_probability',
  'final_probability',
  'edge_pct',
  'stake_units',
  'bet_signal',
];

function isRecord(value: unknown): value is DbRow {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function num(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function str(value: unknown): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  return '';
}

function pickNumber(row: DbRow | null | undefined, ...keys: string[]): number | null {
  if (!row) return null;
  for (const key of keys) {
    const value = num(row[key]);
    if (value !== null) return value;
  }
  return null;
}

function pickString(row: DbRow | null | undefined, ...keys: string[]): string {
  if (!row) return '';
  for (const key of keys) {
    const value = str(row[key]);
    if (value) return value;
  }
  return '';
}

function nested(row: DbRow | null | undefined, key: string): DbRow | null {
  const value = row?.[key];
  return isRecord(value) ? value : null;
}

function valueOrDash(value: string | null | undefined): string {
  return value && value !== 'undefined' && value !== 'null' && value !== 'NaN' ? value : '—';
}

function fmtNumber(value: unknown, decimals = 0): string {
  const parsed = num(value);
  if (parsed === null) return '—';
  return parsed.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtUnits(value: unknown): string {
  const parsed = num(value);
  return parsed === null ? '—' : `${parsed.toFixed(2)}u`;
}

function fmtSignedUnits(value: unknown): string {
  const parsed = num(value);
  if (parsed === null) return '—';
  return `${parsed >= 0 ? '+' : ''}${parsed.toFixed(2)}u`;
}

function fmtPct(value: unknown, decimals = 2, signed = false): string {
  const parsed = num(value);
  if (parsed === null) return '—';
  const pct = parsed * 100;
  const sign = signed && pct > 0 ? '+' : '';
  return `${sign}${pct.toFixed(decimals)}%`;
}

function fmtProbability(value: unknown, decimals = 1): string {
  return fmtPct(value, decimals, false);
}

function fmtOdds(value: unknown): string {
  const parsed = num(value);
  return parsed === null ? '—' : parsed.toFixed(2);
}

function formatSlateDate(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const parsed = new Date(`${raw}T12:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'America/New_York',
  }).format(parsed);
}

function formatShortDate(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const parsed = new Date(`${raw}T12:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'America/New_York',
  }).format(parsed);
}

function formatDateTime(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/New_York',
  }).format(parsed);
}

function daysOld(latestProjectionDate: string | null | undefined): number | null {
  if (!latestProjectionDate) return null;
  const latest = new Date(`${latestProjectionDate}T12:00:00Z`);
  if (Number.isNaN(latest.getTime())) return null;
  const now = new Date();
  const diffMs = now.getTime() - latest.getTime();
  return Math.max(0, Math.floor(diffMs / 86_400_000));
}

function projectionSignal(row: DbRow): string {
  return pickString(row, 'bet_signal', 'betSignal', 'signal').toUpperCase() || 'UNKNOWN';
}

function projectionMarket(row: DbRow): string {
  return pickString(row, 'market').toLowerCase() || 'unknown';
}

function projectionEdge(row: DbRow): number {
  return pickNumber(row, 'edge_pct', 'edgePct', 'edge') ?? 0;
}

function projectionStake(row: DbRow): number {
  return pickNumber(row, 'stake_units', 'stakeUnits', 'stake') ?? 0;
}

function projectionId(row: DbRow): string {
  return [row.id, row.game_id, row.team, row.opponent, row.market, row.selection]
    .map(str)
    .filter(Boolean)
    .join('-');
}

function isBetSignal(row: DbRow): boolean {
  return ['BET_STRONG', 'BET_SMALL', 'BET', 'ACTIONABLE'].includes(projectionSignal(row));
}

function signalColor(signal: string): string {
  return SIGNAL_COLORS[signal.toUpperCase()] ?? SIGNAL_COLORS.UNKNOWN;
}

function signalBadgeClasses(signal: string): string {
  const normalized = signal.toUpperCase();
  if (normalized === 'BET_STRONG') return 'border-emerald-700 bg-emerald-950/70 text-emerald-200';
  if (normalized === 'BET_SMALL') return 'border-sky-700 bg-sky-950/70 text-sky-200';
  if (normalized === 'FADE') return 'border-rose-700 bg-rose-950/70 text-rose-200';
  return 'border-slate-700 bg-slate-950 text-slate-300';
}

function SignalBadge({ value }: { value: string }) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${signalBadgeClasses(value)}`}>{value}</span>;
}

function Dot({ color, label }: { color: string; label: string }) {
  return <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{label}</span>;
}

function EmptyState({ children }: { children: string }) {
  return <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">{children}</div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="mb-4 text-lg font-semibold text-white">{title}</h2>{children}</section>;
}

function KpiCard({ label, value, tone = 'neutral', sub }: { label: string; value: string; tone?: 'neutral' | 'good' | 'bad'; sub?: string }) {
  const toneClass = tone === 'good' ? 'text-emerald-300' : tone === 'bad' ? 'text-rose-300' : 'text-white';
  return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">{label}</div><div className={`mt-3 text-3xl font-semibold tracking-tight ${toneClass}`}>{value}</div>{sub ? <div className="mt-2 text-xs text-slate-400">{sub}</div> : null}</div>;
}

function Header({ payload }: { payload: DashboardPayload }) {
  const staleDays = daysOld(payload.dataState.latestProjectionDate);
  const stale = payload.dataState.isStale;
  const freshness = !payload.dataState.latestProjectionDate
    ? <Dot color="#64748b" label="Unknown" />
    : stale && (staleDays ?? 0) > 1
      ? <Dot color="#f43f5e" label="Stale" />
      : stale
        ? <Dot color="#f59e0b" label="1 day old" />
        : <Dot color="#10b981" label="Fresh" />;
  const modelVersion = pickString(payload.modelMetrics, 'model_version', 'modelVersion') || '—';

  return <header className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"><div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-sm uppercase tracking-[0.3em] text-slate-500">MLB Totals Engine</p><h1 className="mt-2 text-4xl font-semibold text-white">Executive Dashboard</h1><p className="mt-3 text-sm text-slate-400">Latest slate: {formatSlateDate(payload.dataState.latestProjectionDate)}</p></div><div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-2"><div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">Model version</div><div className="mt-2 text-lg font-semibold text-white">{modelVersion}</div></div><div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">Freshness</div><div className="mt-2 text-lg font-semibold text-white">{freshness}</div></div></div></div></header>;
}

function KpiStrip({ payload }: { payload: DashboardPayload }) {
  const summary = payload.summary;
  const diagnostics = payload.legacyDiagnostics;
  const best = nested(summary, 'bestTeamValue');
  const strongBets = pickNumber(summary, 'strongBets') ?? 0;
  const avgEdge = pickNumber(summary, 'avgEdgePct');
  const maxEdge = pickNumber(summary, 'maxEdgePct');
  const predictionsLogRows = pickNumber(diagnostics, 'predictionsLogRows') ?? 0;
  const realized = pickNumber(summary, 'realizedRoiPct');
  const record = nested(summary, 'record');
  const dataLag = predictionsLogRows === 0 ? 'No settled data' : `${fmtPct(realized, 2, true)} ROI`;
  const recordSub = record ? 'Settled record available' : undefined;

  return <div className="grid grid-cols-2 gap-4 lg:grid-cols-4"><KpiCard label="Projections" value={fmtNumber(summary.activeProjections)} /><KpiCard label="Bet signals" value={fmtNumber(summary.betSignals)} /><KpiCard label="Strong bets" value={fmtNumber(strongBets)} tone={strongBets > 0 ? 'good' : 'neutral'} /><KpiCard label="Avg edge" value={fmtPct(avgEdge, 2, true)} tone={(avgEdge ?? 0) > 0 ? 'good' : 'neutral'} /><KpiCard label="Max edge" value={fmtPct(maxEdge, 2, true)} tone={(maxEdge ?? 0) > 0 ? 'good' : 'neutral'} /><KpiCard label="Total stake" value={fmtUnits(summary.totalStakeUnits)} /><KpiCard label="Best team value" value={best ? `${pickString(best, 'team')} ${(pickNumber(best, 'valueScore', 'value_score') ?? 0).toFixed(3)}` : '—'} /><KpiCard label="Data lag" value={dataLag} sub={recordSub} /></div>;
}

function ActionRow({ row }: { row: DbRow }) {
  return <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3"><div className="flex items-start justify-between gap-3"><div><div className="font-medium text-white">{pickString(row, 'team')} vs {pickString(row, 'opponent')}</div><div className="mt-1 text-xs text-slate-400">{projectionMarket(row)} · {pickString(row, 'selection') || '—'}</div></div><SignalBadge value={projectionSignal(row)} /></div><div className={`mt-2 text-sm font-semibold ${projectionEdge(row) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>{fmtPct(projectionEdge(row), 2, true)}</div></div>;
}

function ActionPanel({ payload }: { payload: DashboardPayload }) {
  const top = [...payload.projections].filter(isBetSignal).sort((a, b) => projectionEdge(b) - projectionEdge(a)).slice(0, 3);
  const fades = [...payload.projections].filter((row) => projectionSignal(row) === 'FADE' || projectionEdge(row) < 0).sort((a, b) => projectionEdge(a) - projectionEdge(b)).slice(0, 3);
  return <div className="grid gap-4 lg:grid-cols-3"><Section title="Top opportunities">{top.length ? <div className="space-y-3">{top.map((row) => <ActionRow key={projectionId(row)} row={row} />)}</div> : <EmptyState>No top opportunities.</EmptyState>}</Section><Section title="Fade candidates">{fades.length ? <div className="space-y-3">{fades.map((row) => <ActionRow key={projectionId(row)} row={row} />)}</div> : <EmptyState>No fade candidates.</EmptyState>}</Section><Section title="Operational warnings">{payload.dataState.warnings.length ? <div className="space-y-2">{payload.dataState.warnings.map((warning) => <div key={warning} className="rounded-lg border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-100">▲ {warning}</div>)}</div> : <p className="text-sm text-slate-400">No warnings</p>}</Section></div>;
}

function edgeBuckets(rows: DbRow[]) {
  const buckets = [
    { bucket: '≤-5%', min: -Infinity, max: -0.05, count: 0, color: '#f43f5e' },
    { bucket: '-5 to -2%', min: -0.05, max: -0.02, count: 0, color: '#fb7185' },
    { bucket: '-2 to 0%', min: -0.02, max: 0, count: 0, color: '#94a3b8' },
    { bucket: '0 to +2%', min: 0, max: 0.02, count: 0, color: '#64748b' },
    { bucket: '+2 to +5%', min: 0.02, max: 0.05, count: 0, color: '#34d399' },
    { bucket: '+5%+', min: 0.05, max: Infinity, count: 0, color: '#10b981' },
  ];
  rows.forEach((row) => {
    const value = projectionEdge(row);
    const bucket = buckets.find((item) => value >= item.min && value < item.max);
    if (bucket) bucket.count += 1;
  });
  return buckets;
}

function scatterData(rows: DbRow[]): ChartPoint[] {
  return rows.flatMap((row) => {
    const marketProbability = pickNumber(row, 'market_probability', 'marketProbability');
    const modelProbability = pickNumber(row, 'final_probability', 'finalProbability', 'estimated_probability');
    if (marketProbability === null || modelProbability === null) return [];
    const signal = projectionSignal(row);
    return [{ team: pickString(row, 'team'), opponent: pickString(row, 'opponent'), market: projectionMarket(row), selection: pickString(row, 'selection'), signal, marketProbability, modelProbability, edge: projectionEdge(row), stake: projectionStake(row), color: signalColor(signal) }];
  });
}

function stakeByMarket(rows: DbRow[]) {
  return MARKETS.map((market) => ({ market, stake: rows.filter((row) => projectionMarket(row) === market).reduce((sum, row) => sum + projectionStake(row), 0) })).filter((row) => row.stake > 0);
}

function signalsByMarket(rows: DbRow[]) {
  return MARKETS.map((market) => {
    const entry: DbRow = { market };
    rows.filter((row) => projectionMarket(row) === market).forEach((row) => {
      const sig = projectionSignal(row);
      entry[sig] = (pickNumber(entry, sig) ?? 0) + 1;
    });
    return entry;
  });
}

function ChartCard({ title, empty, children }: { title: string; empty: boolean; children: React.ReactNode }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h3 className="mb-4 text-lg font-semibold text-white">{title}</h3>{empty ? <EmptyState>No chart data available.</EmptyState> : <div className="h-72">{children}</div>}</div>;
}

function scatterShape(props: { cx?: number; cy?: number; payload?: ChartPoint }) {
  const cx = props.cx ?? 0;
  const cy = props.cy ?? 0;
  const payload = props.payload;
  const radius = Math.max(4, Math.min(12, 4 + (payload?.stake ?? 0) * 2));
  return <circle cx={cx} cy={cy} r={radius} fill={payload?.color ?? '#64748b'} opacity={0.9} />;
}

function ChartsGrid({ projections }: { projections: DbRow[] }) {
  const edges = edgeBuckets(projections);
  const points = scatterData(projections);
  const stakes = stakeByMarket(projections);
  const signalBars = signalsByMarket(projections);
  const totalStake = stakes.reduce((sum, item) => sum + item.stake, 0);
  const maxStake = stakes.reduce((max, item) => Math.max(max, item.stake), 0);
  const concentration = totalStake > 0 && maxStake / totalStake > 0.7 ? stakes.find((item) => item.stake === maxStake) : null;

  return <div className="grid gap-4 xl:grid-cols-2"><ChartCard title="Edge distribution" empty={projections.length === 0}><ResponsiveContainer width="100%" height="100%"><BarChart data={edges}><CartesianGrid stroke="#1e293b" strokeDasharray="3 3" /><XAxis dataKey="bucket" stroke="#94a3b8" /><YAxis stroke="#94a3b8" allowDecimals={false} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155', color: '#fff' }} /><Bar dataKey="count">{edges.map((entry) => <Cell key={entry.bucket} fill={entry.color} />)}</Bar></BarChart></ResponsiveContainer></ChartCard><ChartCard title="Model vs market probability" empty={points.length === 0}><ResponsiveContainer width="100%" height="100%"><ScatterChart><CartesianGrid stroke="#1e293b" strokeDasharray="3 3" /><XAxis type="number" dataKey="marketProbability" name="Market" stroke="#94a3b8" domain={[0, 1]} tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`} /><YAxis type="number" dataKey="modelProbability" name="Model" stroke="#94a3b8" domain={[0, 1]} tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`} /><ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#64748b" strokeDasharray="4 4" /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155', color: '#fff' }} formatter={(value, name) => [fmtProbability(value), name]} labelFormatter={(_, data) => { const p = data?.[0]?.payload as ChartPoint | undefined; return p ? `${p.team} vs ${p.opponent} · ${p.market} · ${p.selection} · ${fmtPct(p.edge, 2, true)}` : ''; }} /><Scatter data={points} shape={scatterShape} /></ScatterChart></ResponsiveContainer></ChartCard><ChartCard title="Stake by market" empty={stakes.length === 0}><div className="h-full"><ResponsiveContainer width="100%" height="85%"><PieChart><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155', color: '#fff' }} formatter={(value) => fmtUnits(value)} /><Pie data={stakes} dataKey="stake" nameKey="market" innerRadius={55} outerRadius={95} label>{stakes.map((entry, index) => <Cell key={entry.market} fill={['#10b981', '#38bdf8', '#f59e0b'][index % 3]} />)}</Pie></PieChart></ResponsiveContainer>{concentration ? <p className="text-sm text-amber-300">⚠ {concentration.market} is {((concentration.stake / totalStake) * 100).toFixed(0)}% of total exposure</p> : null}</div></ChartCard><ChartCard title="Signals by market" empty={projections.length === 0}><ResponsiveContainer width="100%" height="100%"><BarChart data={signalBars}><CartesianGrid stroke="#1e293b" strokeDasharray="3 3" /><XAxis dataKey="market" stroke="#94a3b8" /><YAxis stroke="#94a3b8" allowDecimals={false} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155', color: '#fff' }} /><Legend />{SIGNALS.map((sig) => <Bar key={sig} dataKey={sig} stackId="signals" fill={signalColor(sig)} />)}</BarChart></ResponsiveContainer></ChartCard></div>;
}

function projectionSortValue(row: DbRow, key: ProjectionSortKey): string | number {
  if (key === 'edge_pct') return projectionEdge(row);
  if (key === 'stake_units') return projectionStake(row);
  if (key === 'decimal_odds' || key === 'final_probability' || key === 'market_probability' || key === 'model_confidence') return pickNumber(row, key) ?? 0;
  if (key === 'bet_signal') return projectionSignal(row);
  if (key === 'market') return projectionMarket(row);
  return pickString(row, key);
}

function csvEscape(value: unknown): string {
  return `"${String(value ?? '').replaceAll('"', '""')}"`;
}

function exportRows(rows: DbRow[]) {
  const lines = [PROJECTION_CSV_FIELDS.join(','), ...rows.map((row) => PROJECTION_CSV_FIELDS.map((field) => csvEscape(row[field])).join(','))];
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `mlb_projections_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function ProjectionsTable({ rows }: { rows: DbRow[] }) {
  const [query, setQuery] = useState('');
  const [marketFilter, setMarketFilter] = useState('All');
  const [signalFilter, setSignalFilter] = useState('All');
  const [positiveOnly, setPositiveOnly] = useState(false);
  const [signalsOnly, setSignalsOnly] = useState(false);
  const [sortKey, setSortKey] = useState<ProjectionSortKey>('edge_pct');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [selected, setSelected] = useState<DbRow | null>(null);

  useEffect(() => {
    if (!selected) return undefined;
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelected(null);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selected]);

  const filtered = useMemo(() => {
    const text = query.trim().toLowerCase();
    return [...rows]
      .filter((row) => {
        const haystack = [pickString(row, 'team'), pickString(row, 'opponent'), pickString(row, 'selection')].join(' ').toLowerCase();
        return (!text || haystack.includes(text))
          && (marketFilter === 'All' || projectionMarket(row) === marketFilter)
          && (signalFilter === 'All' || projectionSignal(row) === signalFilter)
          && (!positiveOnly || projectionEdge(row) > 0)
          && (!signalsOnly || isBetSignal(row));
      })
      .sort((a, b) => {
        const left = projectionSortValue(a, sortKey);
        const right = projectionSortValue(b, sortKey);
        const multiplier = sortDirection === 'asc' ? 1 : -1;
        if (typeof left === 'number' && typeof right === 'number') return (left - right) * multiplier;
        return String(left).localeCompare(String(right)) * multiplier;
      });
  }, [marketFilter, positiveOnly, query, rows, signalFilter, signalsOnly, sortDirection, sortKey]);

  const setSort = (key: ProjectionSortKey) => {
    if (sortKey === key) setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    else {
      setSortKey(key);
      setSortDirection('desc');
    }
  };

  const headers: Array<[ProjectionSortKey, string]> = [['game_date', 'Date'], ['bet_signal', 'Signal'], ['team', 'Team'], ['opponent', 'Opponent'], ['home_away', 'H/A'], ['market', 'Market'], ['selection', 'Selection'], ['decimal_odds', 'Odds'], ['final_probability', 'Model%'], ['market_probability', 'Market%'], ['edge_pct', 'Edge%'], ['model_confidence', 'Confidence'], ['stake_units', 'Stake'], ['manual_override_flag', 'Override']];

  return <div className="space-y-4"><div className="grid gap-3 lg:grid-cols-[1.4fr_auto_auto_auto]"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search team, opponent, selection" className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-sky-500" /><FilterPills values={['All', ...MARKETS]} value={marketFilter} setValue={setMarketFilter} /><FilterPills values={['All', ...SIGNALS]} value={signalFilter} setValue={setSignalFilter} /><button type="button" onClick={() => exportRows(filtered)} className="rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800">Export CSV</button></div><div className="flex flex-wrap gap-4 text-sm text-slate-300"><label className="inline-flex items-center gap-2"><input type="checkbox" checked={positiveOnly} onChange={(event) => setPositiveOnly(event.target.checked)} />Positive edge only</label><label className="inline-flex items-center gap-2"><input type="checkbox" checked={signalsOnly} onChange={(event) => setSignalsOnly(event.target.checked)} />Bet signals only</label></div><div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="bg-slate-950/70 text-xs uppercase text-slate-500"><tr>{headers.map(([key, label]) => <th key={key} className="whitespace-nowrap px-4 py-3"><button type="button" onClick={() => setSort(key)}>{label}{sortKey === key ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>)}</tr></thead><tbody>{filtered.map((row) => <tr key={projectionId(row)} onClick={() => setSelected(row)} className="cursor-pointer border-t border-slate-800 text-slate-300 hover:bg-slate-800/40"><td className="px-4 py-3">{formatShortDate(row.game_date)}</td><td className="px-4 py-3"><SignalBadge value={projectionSignal(row)} /></td><td className="px-4 py-3 font-medium text-white">{pickString(row, 'team')}</td><td className="px-4 py-3">{pickString(row, 'opponent')}</td><td className="px-4 py-3">{pickString(row, 'home_away') || '—'}</td><td className="px-4 py-3">{projectionMarket(row)}</td><td className="px-4 py-3">{pickString(row, 'selection') || '—'}</td><td className="px-4 py-3">{fmtOdds(row.decimal_odds)}</td><td className="px-4 py-3">{fmtProbability(row.final_probability)}</td><td className="px-4 py-3">{fmtProbability(row.market_probability)}</td><td className={`px-4 py-3 font-semibold ${projectionEdge(row) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>{fmtPct(projectionEdge(row), 2, true)}</td><td className="px-4 py-3">{fmtProbability(row.model_confidence, 0)}</td><td className={`px-4 py-3 ${projectionStake(row) === 0 ? 'text-slate-500' : ''}`}>{fmtUnits(projectionStake(row))}</td><td className="px-4 py-3">{row.manual_override_flag ? <span className="text-amber-300">✓</span> : '—'}</td></tr>)}{filtered.length === 0 ? <tr><td colSpan={14} className="px-4 py-8 text-center text-slate-400">No projections match the current filters.</td></tr> : null}</tbody></table></div>{selected ? <ProjectionDrawer row={selected} close={() => setSelected(null)} /> : null}</div>;
}

function FilterPills({ values, value, setValue }: { values: string[]; value: string; setValue: (value: string) => void }) {
  return <div className="flex flex-wrap gap-2">{values.map((item) => <button key={item} type="button" onClick={() => setValue(item)} className={`rounded-full border px-3 py-2 text-xs ${value === item ? 'border-sky-500 bg-sky-950/50 text-sky-200' : 'border-slate-700 text-slate-400 hover:bg-slate-800'}`}>{item}</button>)}</div>;
}

function DetailLine({ label, value, adjustment = false }: { label: string; value: unknown; adjustment?: boolean }) {
  return <div className="flex justify-between gap-4 border-b border-slate-800 py-2 text-sm"><span className="text-slate-400">{label}</span><span className="text-white">{adjustment ? fmtPct(value, 2, true) : fmtProbability(value)}</span></div>;
}

function ProjectionDrawer({ row, close }: { row: DbRow; close: () => void }) {
  return <div className="fixed inset-0 z-50 bg-black/60" onClick={close}><aside className="ml-auto h-full w-full max-w-md overflow-y-auto border-l border-slate-800 bg-slate-950 p-6" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><div><h3 className="text-xl font-semibold text-white">Projection detail</h3><p className="mt-1 text-sm text-slate-400">{pickString(row, 'team')} vs {pickString(row, 'opponent')}</p></div><button type="button" onClick={close} className="rounded-lg border border-slate-700 px-3 py-1 text-sm text-slate-300">Close</button></div><div className="mt-6"><DetailLine label="Base probability" value={row.base_probability} /><DetailLine label="Pitcher adjustment" value={row.pitcher_adjustment} adjustment /><DetailLine label="Lineup adjustment" value={row.lineup_adjustment} adjustment /><DetailLine label="Handedness adjustment" value={row.handedness_adjustment} adjustment /><DetailLine label="Weather adjustment" value={row.weather_adjustment} adjustment /><DetailLine label="Bullpen adjustment" value={row.bullpen_adjustment} adjustment /><DetailLine label="Manual override" value={row.manual_override} adjustment /><DetailLine label="Final probability" value={row.final_probability} /><DetailLine label="Market probability" value={row.market_probability} /><DetailLine label="Edge" value={row.edge_pct} adjustment /><div className="flex justify-between gap-4 py-2 text-sm"><span className="text-slate-400">Stake</span><span className="text-white">{fmtUnits(row.stake_units)}</span></div></div></aside></div>;
}

function TeamMarketValue({ rows }: { rows: DbRow[] }) {
  const sorted = [...rows].sort((a, b) => (pickNumber(b, 'value_score', 'valueScore') ?? 0) - (pickNumber(a, 'value_score', 'valueScore') ?? 0));
  if (sorted.length === 0) return <EmptyState>No team market value rows.</EmptyState>;
  return <div className="space-y-4"><div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={sorted} margin={{ left: 20, right: 40 }}><CartesianGrid stroke="#1e293b" strokeDasharray="3 3" /><XAxis type="number" stroke="#94a3b8" /><YAxis type="category" dataKey="team" stroke="#94a3b8" width={60} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155', color: '#fff' }} formatter={(value) => (num(value) ?? 0).toFixed(3)} /><Bar dataKey="value_score" label={{ position: 'right', fill: '#cbd5e1', formatter: (value: unknown) => (num(value) ?? 0).toFixed(3) }}>{sorted.map((row) => <Cell key={pickString(row, 'team')} fill={(pickNumber(row, 'value_score', 'valueScore') ?? 0) >= 0 ? '#10b981' : '#f43f5e'} />)}</Bar></BarChart></ResponsiveContainer></div><div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="bg-slate-950/70 text-xs uppercase text-slate-500"><tr>{['Team', 'Value score', 'ML ROI', 'RL ROI', 'O/U ROI', 'ML profit', 'RL profit', 'O/U profit'].map((header) => <th key={header} className="px-4 py-3">{header}</th>)}</tr></thead><tbody>{sorted.map((row) => <tr key={pickString(row, 'team')} className="border-t border-slate-800 text-slate-300"><td className="px-4 py-3 font-medium text-white">{pickString(row, 'team')}</td><td className="px-4 py-3">{(pickNumber(row, 'value_score', 'valueScore') ?? 0).toFixed(3)}</td><RoiCell value={pickNumber(row, 'ml_roi_ytd')} /><RoiCell value={pickNumber(row, 'rl_roi_ytd')} /><RoiCell value={pickNumber(row, 'ou_roi_ytd')} /><ProfitCell value={pickNumber(row, 'ml_profit_ytd')} /><ProfitCell value={pickNumber(row, 'rl_profit_ytd')} /><ProfitCell value={pickNumber(row, 'ou_profit_ytd')} /></tr>)}</tbody></table></div></div>;
}

function RoiCell({ value }: { value: number | null }) {
  return <td className={`px-4 py-3 ${value !== null && value > 0 ? 'text-emerald-300' : value !== null && value < 0 ? 'text-rose-300' : 'text-slate-300'}`}>{fmtPct(value, 1, true)}</td>;
}

function ProfitCell({ value }: { value: number | null }) {
  return <td className={`px-4 py-3 ${value !== null && value > 0 ? 'text-emerald-300' : value !== null && value < 0 ? 'text-rose-300' : 'text-slate-300'}`}>{fmtSignedUnits(value)}</td>;
}

function ModelHealth({ metrics }: { metrics: DbRow | null }) {
  if (!metrics) return <EmptyState>No model metrics available.</EmptyState>;
  return <div className="space-y-4"><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-7"><KpiCard label="Model version" value={valueOrDash(pickString(metrics, 'model_version', 'modelVersion'))} /><KpiCard label="As of date" value={formatShortDate(pickString(metrics, 'as_of'))} /><KpiCard label="MAE" value={fmtNumber(pickNumber(metrics, 'test_mae_start_score'), 2)} /><KpiCard label="AUC runline" value={fmtNumber(pickNumber(metrics, 'test_auc_runline'), 3)} /><KpiCard label="AUC moneyline" value={fmtNumber(pickNumber(metrics, 'test_auc_moneyline'), 3)} /><KpiCard label="Sim ROI" value={fmtPct(pickNumber(metrics, 'simulated_roi_last_250'), 2, true)} /><KpiCard label="Avg CLV" value={fmtPct(pickNumber(metrics, 'avg_clv_last_250'), 2, true)} /></div>{pickString(metrics, 'notes') ? <p className="text-sm italic text-slate-400">{pickString(metrics, 'notes')}</p> : null}</div>;
}

function ManualOverrides({ rows }: { rows: DbRow[] }) {
  if (rows.length === 0) return <EmptyState>No active manual overrides.</EmptyState>;
  return <div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="bg-slate-950/70 text-xs uppercase text-slate-500"><tr>{['Game', 'Team', 'Market', 'Field', 'Override value', 'Reason', 'Created at'].map((header) => <th key={header} className="px-4 py-3">{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${pickString(row, 'game_id')}-${index}`} className="border-t border-slate-800 text-slate-300"><td className="px-4 py-3">{pickString(row, 'game_id') || '—'}</td><td className="px-4 py-3">{pickString(row, 'team') || '—'}</td><td className="px-4 py-3">{pickString(row, 'market') || '—'}</td><td className="px-4 py-3">{pickString(row, 'field_name', 'field') || '—'}</td><td className="px-4 py-3">{valueOrDash(pickString(row, 'override_value', 'adjustment_value'))}</td><td className="px-4 py-3">{pickString(row, 'reason') || '—'}</td><td className="px-4 py-3">{formatDateTime(pickString(row, 'created_at'))}</td></tr>)}</tbody></table></div>;
}

function LegacyDiagnostics({ payload }: { payload: DashboardPayload }) {
  const diagnostics = payload.legacyDiagnostics;
  const warnings = payload.dataState.warnings;
  const rows = [
    ['predictions_log', pickNumber(diagnostics, 'predictionsLogRows') ?? 0],
    ['daily_metrics', pickNumber(diagnostics, 'dailyMetricsRows') ?? 0],
    ['odds_snapshots', pickNumber(diagnostics, 'oddsSnapshotsRows') ?? 0],
  ] as const;
  return <details className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><summary className="cursor-pointer text-lg font-semibold text-white">Legacy diagnostics — {rows.length} sources</summary><div className="mt-4 space-y-3">{rows.map(([name, count]) => { const related = warnings.filter((warning) => warning.toLowerCase().includes(name)); return <div key={name} className="rounded-xl border border-slate-800 bg-slate-950/50 p-3"><div className="flex justify-between text-sm"><span className="text-slate-200">{name}</span><span className="text-slate-400">{count} rows</span></div>{count === 0 ? <p className="mt-1 text-xs text-slate-500">Empty — not a system error. Populate via pipeline.</p> : null}{related.map((warning) => <p key={warning} className="mt-1 text-xs text-rose-300">{warning}</p>)}</div>; })}</div></details>;
}

export default function ExecutiveDashboard({ payload }: { payload: DashboardPayload }) {
  const staleDays = daysOld(payload.dataState.latestProjectionDate);
  return <main className="min-h-screen bg-slate-950 text-slate-100"><div className="mx-auto max-w-7xl space-y-8 px-6 py-8">{payload.dataState.isDemo ? <div className="rounded-2xl border border-rose-800 bg-rose-950/60 p-4 text-rose-100">Demo data active — do not use for betting decisions.</div> : null}<Header payload={payload} />{payload.dataState.isStale && payload.projections.length > 0 ? <div className="rounded-2xl border border-amber-800 bg-amber-950/50 p-4 text-amber-100">Data is {staleDays ?? 'unknown'} days old — verify before placing bets.</div> : null}<KpiStrip payload={payload} /><ActionPanel payload={payload} /><ChartsGrid projections={payload.projections} /><Section title="Projections"><ProjectionsTable rows={payload.projections} /></Section><Section title="Team market value"><TeamMarketValue rows={payload.teamMarket} /></Section><Section title="Model health"><ModelHealth metrics={payload.modelMetrics} /></Section><Section title="Manual override audit"><ManualOverrides rows={payload.manualOverrides} /></Section><LegacyDiagnostics payload={payload} /></div></main>;
}
