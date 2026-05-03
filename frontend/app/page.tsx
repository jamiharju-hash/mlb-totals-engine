'use client';

import { useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type JsonRow = Record<string, unknown>;
type DashboardPayload = Partial<{
  summary: JsonRow;
  topPicks: JsonRow[];
  projections: JsonRow[];
  teamMarket: JsonRow[];
  modelMetrics: JsonRow | null;
  manualOverrides: JsonRow[];
  legacyDiagnostics: JsonRow;
  dataState: {
    latestProjectionDate?: string | null;
    isStale?: boolean;
    isDemo?: boolean;
    warnings?: string[];
  };
}>;

type SortField = 'date' | 'team' | 'market' | 'signal' | 'edge' | 'stake' | 'confidence';
type SortDirection = 'asc' | 'desc';
type Severity = 'warning' | 'danger' | null;

const POLL_MS = 30_000;
const ACTIONABLE = new Set(['BET_STRONG', 'BET_SMALL', 'BET', 'ACTIONABLE']);

function isRecord(value: unknown): value is JsonRow {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asPayload(value: unknown): DashboardPayload {
  return isRecord(value) ? (value as DashboardPayload) : {};
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

function pickNumber(row: JsonRow | undefined | null, ...keys: string[]): number | null {
  if (!row) return null;
  for (const key of keys) {
    const value = num(row[key]);
    if (value !== null) return value;
  }
  return null;
}

function pickString(row: JsonRow | undefined | null, ...keys: string[]): string {
  if (!row) return '';
  for (const key of keys) {
    const value = str(row[key]);
    if (value) return value;
  }
  return '';
}

function pct(value: unknown, decimals = 1): string {
  const parsed = num(value);
  if (parsed === null) return '—';
  const normalized = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
  return `${normalized.toFixed(decimals)}%`;
}

function amount(value: unknown, decimals = 2): string {
  const parsed = num(value);
  if (parsed === null) return '—';
  return parsed.toLocaleString(undefined, { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
}

function dateLabel(value: unknown): string {
  const raw = str(value);
  if (!raw) return 'Unavailable';
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return parsed.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function dateTimeLabel(value: unknown): string {
  const raw = str(value);
  if (!raw) return '—';
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return parsed.toLocaleString();
}

function nested(row: JsonRow | undefined, key: string): JsonRow | undefined {
  const value = row?.[key];
  return isRecord(value) ? value : undefined;
}

function projectionId(row: JsonRow): string {
  return [row.id, row.game_id, row.gameId, row.team, row.market, row.selection].map(str).filter(Boolean).join('-') || JSON.stringify(row).slice(0, 120);
}

function gameDate(row: JsonRow): string {
  return pickString(row, 'game_date', 'gameDate', 'snapshot_ts', 'updated_at', 'created_at');
}

function team(row: JsonRow): string {
  return pickString(row, 'team') || 'Unknown team';
}

function opponent(row: JsonRow): string {
  return pickString(row, 'opponent') || '—';
}

function market(row: JsonRow): string {
  return pickString(row, 'market').toLowerCase() || 'unknown';
}

function signal(row: JsonRow): string {
  return pickString(row, 'bet_signal', 'betSignal', 'signal').toUpperCase() || 'UNKNOWN';
}

function edge(row: JsonRow): number {
  return pickNumber(row, 'edge_pct', 'edgePct', 'edge') ?? 0;
}

function stake(row: JsonRow): number {
  return pickNumber(row, 'stake_units', 'stakeUnits', 'stake', 'stake_pct_bankroll') ?? 0;
}

function confidence(row: JsonRow): number {
  return pickNumber(row, 'model_confidence', 'modelConfidence', 'confidence') ?? 0;
}

function modelProbability(row: JsonRow): number | null {
  return pickNumber(row, 'final_probability', 'finalProbability', 'estimated_probability', 'base_probability', 'baseProbability');
}

function marketProbability(row: JsonRow): number | null {
  return pickNumber(row, 'market_probability', 'marketProbability', 'break_even_probability');
}

function teamValue(row: JsonRow): number {
  return pickNumber(row, 'value_score', 'valueScore') ?? 0;
}

function isActionable(row: JsonRow): boolean {
  return ACTIONABLE.has(signal(row));
}

function staleSeverity(dataState: DashboardPayload['dataState']): Severity {
  const latest = dataState?.latestProjectionDate;
  if (!latest) return dataState?.isStale ? 'warning' : null;
  const parsed = new Date(latest);
  if (Number.isNaN(parsed.getTime())) return dataState?.isStale ? 'warning' : null;
  const ageHours = (Date.now() - parsed.getTime()) / 3_600_000;
  if (ageHours > 48) return 'danger';
  if (ageHours >= 24 || dataState?.isStale) return 'warning';
  return null;
}

function modelVersion(payload: DashboardPayload | null): string {
  return pickString(payload?.modelMetrics ?? undefined, 'model_version', 'modelVersion') || pickString(payload?.projections?.[0], 'model_version', 'modelVersion') || 'Unavailable';
}

function apiErrorMessage(error: string | null): string | null {
  if (!error) return null;
  return `${error}. Check /api/mlb-dashboard and Supabase env vars.`;
}

function sortRows(rows: JsonRow[], field: SortField, direction: SortDirection): JsonRow[] {
  const multiplier = direction === 'asc' ? 1 : -1;
  return [...rows].sort((a, b) => {
    const left = field === 'edge' ? edge(a) : field === 'stake' ? stake(a) : field === 'confidence' ? confidence(a) : field === 'date' ? gameDate(a) : field === 'team' ? team(a) : field === 'market' ? market(a) : signal(a);
    const right = field === 'edge' ? edge(b) : field === 'stake' ? stake(b) : field === 'confidence' ? confidence(b) : field === 'date' ? gameDate(b) : field === 'team' ? team(b) : field === 'market' ? market(b) : signal(b);
    if (typeof left === 'number' && typeof right === 'number') return (left - right) * multiplier;
    return String(left).localeCompare(String(right)) * multiplier;
  });
}

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className="mt-3 text-3xl font-semibold tracking-tight text-white">{value}</div>
      {sub ? <div className="mt-2 text-xs text-slate-400">{sub}</div> : null}
    </div>
  );
}

function SignalBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();
  const className = ACTIONABLE.has(normalized)
    ? 'border-emerald-700 bg-emerald-950/50 text-emerald-200'
    : normalized === 'FADE'
      ? 'border-amber-700 bg-amber-950/50 text-amber-200'
      : 'border-slate-700 bg-slate-950 text-slate-300';
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}>{normalized}</span>;
}

function StatusBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();
  const className = normalized.includes('FRESH') || normalized.includes('OK')
    ? 'border-emerald-700 bg-emerald-950/50 text-emerald-200'
    : normalized.includes('STALE') || normalized.includes('WARN')
      ? 'border-amber-700 bg-amber-950/50 text-amber-200'
      : normalized.includes('DEMO') || normalized.includes('ERROR') || normalized.includes('FAIL')
        ? 'border-rose-700 bg-rose-950/50 text-rose-200'
        : 'border-slate-700 bg-slate-950 text-slate-300';
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}>{value}</span>;
}

function Skeleton({ rows = 4 }: { rows?: number }) {
  return <div className="space-y-3">{Array.from({ length: rows }).map((_, index) => <div key={index} className="h-8 animate-pulse rounded-lg bg-slate-800/80" />)}</div>;
}

function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-sm text-slate-400">{children}</div>;
}

function Alert({ tone, children }: { tone: 'info' | 'warning' | 'danger'; children: ReactNode }) {
  const className = tone === 'danger'
    ? 'border-rose-800 bg-rose-950/50 text-rose-100'
    : tone === 'warning'
      ? 'border-amber-800 bg-amber-950/40 text-amber-100'
      : 'border-slate-800 bg-slate-900/70 text-slate-200';
  return <div className={`rounded-xl border p-3 text-sm ${className}`}>{children}</div>;
}

function Section({ title, description, loading, missing, error, empty, emptyText, severity, demo, children }: {
  title: string;
  description?: string;
  loading: boolean;
  missing: boolean;
  error: string | null;
  empty: boolean;
  emptyText: string;
  severity: Severity;
  demo: boolean;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {description ? <p className="mt-1 text-sm text-slate-400">{description}</p> : null}
      </div>
      <div className="mb-4 space-y-2">
        {demo ? <Alert tone="danger">Demo data — do not use for betting decisions.</Alert> : null}
        {severity ? <Alert tone={severity}>Projection data is stale. Verify ingestion before using stake recommendations.</Alert> : null}
      </div>
      {loading ? <Skeleton /> : null}
      {!loading && error ? <Alert tone="danger">{error}</Alert> : null}
      {!loading && !error && missing ? <Alert tone="warning">Section unavailable in /api/mlb-dashboard payload.</Alert> : null}
      {!loading && !error && !missing && empty ? <Empty>{emptyText}</Empty> : null}
      {!loading && !error && !missing && !empty ? children : null}
    </section>
  );
}

function Header({ payload, loading, error, refreshing }: { payload: DashboardPayload | null; loading: boolean; error: string | null; refreshing: boolean }) {
  const state = payload?.dataState;
  const severity = staleSeverity(state);
  const freshness = state?.isDemo ? 'DEMO' : severity === 'danger' ? 'STALE >2D' : severity === 'warning' ? 'STALE >1D' : state?.latestProjectionDate ? 'FRESH' : 'UNKNOWN';
  return (
    <header className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-sm">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-slate-500">MLB Totals Engine</p>
          <h1 className="mt-2 text-4xl font-semibold text-white">Executive dashboard</h1>
          <p className="mt-3 max-w-3xl text-sm text-slate-400">Projection control plane for actionable bets, team market value, model health, overrides and diagnostics.</p>
        </div>
        <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-3 lg:min-w-[520px]">
          <KpiCard label="Latest slate" value={loading ? 'Loading…' : dateLabel(state?.latestProjectionDate)} />
          <KpiCard label="Model version" value={loading ? 'Loading…' : modelVersion(payload)} />
          <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
            <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">Freshness</div>
            <div className="mt-3 flex items-center gap-2"><StatusBadge value={freshness} />{refreshing ? <span className="text-xs text-slate-500">Refreshing</span> : null}</div>
          </div>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {state?.isDemo ? <Alert tone="danger">Demo data — do not use for betting decisions.</Alert> : null}
        {severity ? <Alert tone={severity}>Latest slate is {dateLabel(state?.latestProjectionDate)}. Confirm freshness before betting.</Alert> : null}
        {error ? <Alert tone="danger">{error}</Alert> : null}
      </div>
    </header>
  );
}

function Kpis({ summary }: { summary: JsonRow }) {
  const bestTeam = nested(summary, 'bestTeamValue');
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <KpiCard label="Active projections" value={amount(summary.activeProjections, 0)} />
      <KpiCard label="Bet signals" value={amount(summary.betSignals, 0)} sub="Actionable picks" />
      <KpiCard label="Strong bets" value={amount(summary.strongBets, 0)} />
      <KpiCard label="Average edge" value={pct(summary.avgEdgePct)} />
      <KpiCard label="Max edge" value={pct(summary.maxEdgePct)} />
      <KpiCard label="Total stake" value={amount(summary.totalStakeUnits)} sub="Recommended units" />
      <KpiCard label="Positive edge rate" value={pct(summary.positiveEdgeRate)} />
      <KpiCard label="Best team value" value={pickString(bestTeam, 'team') || '—'} sub={`Score ${amount(pickNumber(bestTeam, 'valueScore', 'value_score'))}`} />
    </div>
  );
}

function ActionPanel({ topPicks, projections, warnings }: { topPicks: JsonRow[]; projections: JsonRow[]; warnings: string[] }) {
  const opportunities = topPicks.length ? topPicks : sortRows(projections.filter(isActionable), 'edge', 'desc').slice(0, 5);
  const fades = sortRows(projections.filter((row) => signal(row) === 'FADE'), 'edge', 'asc').slice(0, 5);
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <ActionList title="Top opportunities" rows={opportunities} empty="No top opportunities found." />
      <ActionList title="Fade candidates" rows={fades} empty="No fade candidates found." />
      <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Operational warnings</h3>
        <div className="mt-4 space-y-3">{warnings.length ? warnings.map((warning) => <Alert key={warning} tone="warning">{warning}</Alert>) : <Empty>No operational warnings found.</Empty>}</div>
      </div>
    </div>
  );
}

function ActionList({ title, rows, empty }: { title: string; rows: JsonRow[]; empty: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <div className="mt-4 space-y-3">
        {rows.length === 0 ? <Empty>{empty}</Empty> : null}
        {rows.map((row) => (
          <div key={projectionId(row)} className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <div className="flex items-start justify-between gap-3">
              <div><div className="font-medium text-white">{team(row)} {pickString(row, 'selection') ? `— ${pickString(row, 'selection')}` : ''}</div><div className="mt-1 text-xs text-slate-400">{market(row)} vs {opponent(row)}</div></div>
              <SignalBadge value={signal(row)} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-300"><span>Edge {pct(edge(row))}</span><span>Stake {amount(stake(row))}u</span><span>Conf {pct(confidence(row))}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChartCard({ title, empty, emptyText, children }: { title: string; empty: boolean; emptyText: string; children: ReactNode }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4"><h3 className="mb-4 text-sm font-semibold text-white">{title}</h3>{empty ? <Empty>{emptyText}</Empty> : <div className="h-72">{children}</div>}</div>;
}

function edgeDistribution(rows: JsonRow[]) {
  const buckets = [{ bucket: '<0%', min: -Infinity, max: 0, count: 0 }, { bucket: '0–2%', min: 0, max: 2, count: 0 }, { bucket: '2–5%', min: 2, max: 5, count: 0 }, { bucket: '5–10%', min: 5, max: 10, count: 0 }, { bucket: '>10%', min: 10, max: Infinity, count: 0 }];
  rows.forEach((row) => {
    const value = Math.abs(edge(row)) <= 1 ? edge(row) * 100 : edge(row);
    const bucket = buckets.find((item) => value >= item.min && value < item.max);
    if (bucket) bucket.count += 1;
  });
  return buckets.map(({ bucket, count }) => ({ bucket, count })).filter((item) => item.count > 0);
}

function aggregate(rows: JsonRow[], getter: (row: JsonRow) => number) {
  const totals = new Map<string, number>();
  rows.forEach((row) => totals.set(market(row), (totals.get(market(row)) ?? 0) + getter(row)));
  return [...totals.entries()].map(([name, value]) => ({ market: name, value }));
}

function scatter(rows: JsonRow[]) {
  return rows.flatMap((row) => {
    const model = modelProbability(row);
    const marketValue = marketProbability(row);
    if (model === null || marketValue === null) return [];
    return [{ model: Math.abs(model) <= 1 ? model * 100 : model, market: Math.abs(marketValue) <= 1 ? marketValue * 100 : marketValue, team: team(row) }];
  });
}

function signalBars(rows: JsonRow[]) {
  const grouped = new Map<string, JsonRow>();
  rows.forEach((row) => {
    const key = market(row);
    const current = grouped.get(key) ?? { market: key };
    const sig = signal(row);
    current[sig] = (num(current[sig]) ?? 0) + 1;
    grouped.set(key, current);
  });
  return [...grouped.values()];
}

function Charts({ projections }: { projections: JsonRow[] }) {
  const edgeData = edgeDistribution(projections);
  const scatterData = scatter(projections);
  const stakeData = aggregate(projections, stake).filter((item) => item.value > 0);
  const signalData = signalBars(projections);
  const signalKeys = [...new Set(projections.map(signal))].filter(Boolean);
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="EdgeDistribution" empty={edgeData.length === 0} emptyText="No edge distribution found."><ResponsiveContainer width="100%" height="100%"><BarChart data={edgeData}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis dataKey="bucket" stroke="#94a3b8" tick={{ fontSize: 12 }} /><YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155' }} /><Bar dataKey="count" fill="#38bdf8" /></BarChart></ResponsiveContainer></ChartCard>
      <ChartCard title="ModelVsMarketScatter" empty={scatterData.length === 0} emptyText="No model vs market points found."><ResponsiveContainer width="100%" height="100%"><ScatterChart><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis type="number" dataKey="market" name="Market probability" stroke="#94a3b8" tick={{ fontSize: 12 }} /><YAxis type="number" dataKey="model" name="Model probability" stroke="#94a3b8" tick={{ fontSize: 12 }} /><Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: '#020617', border: '1px solid #334155' }} /><Scatter name="Projection" data={scatterData} fill="#38bdf8" /></ScatterChart></ResponsiveContainer></ChartCard>
      <ChartCard title="StakeByMarket" empty={stakeData.length === 0} emptyText="No stake by market found."><ResponsiveContainer width="100%" height="100%"><BarChart data={stakeData}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis dataKey="market" stroke="#94a3b8" tick={{ fontSize: 12 }} /><YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155' }} /><Bar dataKey="value" fill="#22c55e" /></BarChart></ResponsiveContainer></ChartCard>
      <ChartCard title="SignalsByMarket" empty={signalData.length === 0 || signalKeys.length === 0} emptyText="No signals by market found."><ResponsiveContainer width="100%" height="100%"><BarChart data={signalData}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis dataKey="market" stroke="#94a3b8" tick={{ fontSize: 12 }} /><YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} /><Tooltip contentStyle={{ background: '#020617', border: '1px solid #334155' }} /><Legend />{signalKeys.map((key, index) => <Bar key={key} dataKey={key} stackId="signals" fill={['#22c55e', '#f59e0b', '#64748b', '#ef4444'][index % 4]} />)}</BarChart></ResponsiveContainer></ChartCard>
    </div>
  );
}

function ProjectionsTable({ rows }: { rows: JsonRow[] }) {
  const [query, setQuery] = useState('');
  const [selectedMarket, setSelectedMarket] = useState('all');
  const [selectedSignal, setSelectedSignal] = useState('all');
  const [minEdge, setMinEdge] = useState('');
  const [actionableOnly, setActionableOnly] = useState(false);
  const [sortField, setSortField] = useState<SortField>('edge');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [selected, setSelected] = useState<JsonRow | null>(null);
  const markets = useMemo(() => [...new Set(rows.map(market))].sort(), [rows]);
  const signals = useMemo(() => [...new Set(rows.map(signal))].sort(), [rows]);
  const filtered = useMemo(() => {
    const threshold = num(minEdge) ?? -Infinity;
    const q = query.trim().toLowerCase();
    return sortRows(rows.filter((row) => {
      const haystack = [team(row), opponent(row), pickString(row, 'game_id', 'gameId'), pickString(row, 'selection'), market(row), signal(row)].join(' ').toLowerCase();
      return (!q || haystack.includes(q)) && (selectedMarket === 'all' || market(row) === selectedMarket) && (selectedSignal === 'all' || signal(row) === selectedSignal) && edge(row) >= threshold && (!actionableOnly || isActionable(row));
    }), sortField, sortDirection);
  }, [actionableOnly, minEdge, query, rows, selectedMarket, selectedSignal, sortDirection, sortField]);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
        <TextInput label="Search" value={query} setValue={setQuery} placeholder="Team, opponent, game" className="xl:col-span-2" />
        <Select label="Market" value={selectedMarket} setValue={setSelectedMarket} values={markets} />
        <Select label="Signal" value={selectedSignal} setValue={setSelectedSignal} values={signals} />
        <TextInput label="Min edge" value={minEdge} setValue={setMinEdge} placeholder="0" />
        <Select label="Sort" value={sortField} setValue={(value) => setSortField(value as SortField)} values={['edge', 'stake', 'confidence', 'date', 'team', 'market', 'signal']} includeAll={false} />
        <Select label="Direction" value={sortDirection} setValue={(value) => setSortDirection(value as SortDirection)} values={['desc', 'asc']} includeAll={false} />
      </div>
      <label className="inline-flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={actionableOnly} onChange={(event) => setActionableOnly(event.target.checked)} className="h-4 w-4 rounded border-slate-700 bg-slate-950" />Actionable only</label>
      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full text-left text-sm"><thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Date</th><th className="px-4 py-3">Game</th><th className="px-4 py-3">Team</th><th className="px-4 py-3">Market</th><th className="px-4 py-3">Selection</th><th className="px-4 py-3">Signal</th><th className="px-4 py-3">Edge</th><th className="px-4 py-3">Stake</th><th className="px-4 py-3">Confidence</th><th className="px-4 py-3">Odds</th></tr></thead>
          <tbody>{filtered.map((row) => <tr key={projectionId(row)} onClick={() => setSelected(row)} className="cursor-pointer border-b border-slate-800/70 text-slate-300 hover:bg-slate-800/40"><td className="px-4 py-3 text-xs text-slate-500">{dateLabel(gameDate(row))}</td><td className="px-4 py-3">{pickString(row, 'game_id', 'gameId') || '—'}</td><td className="px-4 py-3 font-medium text-white">{team(row)}</td><td className="px-4 py-3">{market(row)}</td><td className="px-4 py-3">{pickString(row, 'selection') || '—'}</td><td className="px-4 py-3"><SignalBadge value={signal(row)} /></td><td className="px-4 py-3">{pct(edge(row))}</td><td className="px-4 py-3">{amount(stake(row))}u</td><td className="px-4 py-3">{pct(confidence(row))}</td><td className="px-4 py-3">{amount(pickNumber(row, 'decimal_odds', 'decimalOdds'), 2)}</td></tr>)}{filtered.length === 0 ? <tr><td colSpan={10} className="px-4 py-8 text-center text-slate-500">No projections found for the active filters.</td></tr> : null}</tbody>
        </table>
      </div>
      {selected ? <DetailDrawer row={selected} close={() => setSelected(null)} /> : null}
    </div>
  );
}

function TextInput({ label, value, setValue, placeholder, className = '' }: { label: string; value: string; setValue: (value: string) => void; placeholder: string; className?: string }) {
  return <label className={className}><span className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</span><input value={value} onChange={(event) => setValue(event.target.value)} placeholder={placeholder} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-sky-500" /></label>;
}

function Select({ label, value, setValue, values, includeAll = true }: { label: string; value: string; setValue: (value: string) => void; values: string[]; includeAll?: boolean }) {
  return <label><span className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</span><select value={value} onChange={(event) => setValue(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">{includeAll ? <option value="all">All</option> : null}{values.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>;
}

function DetailDrawer({ row, close }: { row: JsonRow; close: () => void }) {
  return <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70" onClick={close}><aside className="h-full w-full max-w-xl overflow-y-auto border-l border-slate-800 bg-slate-950 p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><div><h3 className="text-xl font-semibold text-white">Projection detail</h3><p className="mt-1 text-sm text-slate-400">{team(row)} vs {opponent(row)}</p></div><button type="button" onClick={close} className="rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">Close</button></div><div className="mt-6 grid gap-3 sm:grid-cols-2"><KpiCard label="Signal" value={signal(row)} /><KpiCard label="Edge" value={pct(edge(row))} /><KpiCard label="Stake" value={`${amount(stake(row))}u`} /><KpiCard label="Confidence" value={pct(confidence(row))} /></div><dl className="mt-6 grid gap-3 text-sm">{Object.entries(row).map(([key, value]) => <div key={key} className="rounded-xl border border-slate-800 bg-slate-900/50 p-3"><dt className="text-xs uppercase tracking-[0.2em] text-slate-500">{key}</dt><dd className="mt-1 break-words text-slate-200">{typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}</dd></div>)}</dl></aside></div>;
}

function TeamMarket({ rows }: { rows: JsonRow[] }) {
  const sorted = [...rows].sort((a, b) => teamValue(b) - teamValue(a));
  return <div className="space-y-4"><div className="grid gap-4 md:grid-cols-3">{sorted.slice(0, 3).map((row, index) => <div key={`${team(row)}-${index}`} className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">Rank #{index + 1}</div><div className="mt-2 text-2xl font-semibold text-white">{team(row)}</div><div className="mt-1 text-sm text-slate-400">Value score {amount(teamValue(row))}</div></div>)}</div><div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Team</th><th className="px-4 py-3">Value score</th><th className="px-4 py-3">ML ROI</th><th className="px-4 py-3">RL ROI</th><th className="px-4 py-3">OU ROI</th><th className="px-4 py-3">ML profit</th><th className="px-4 py-3">RL profit</th><th className="px-4 py-3">OU profit</th></tr></thead><tbody>{sorted.map((row) => <tr key={`${team(row)}-${str(row.id)}`} className="border-b border-slate-800/70 text-slate-300"><td className="px-4 py-3 font-medium text-white">{team(row)}</td><td className="px-4 py-3">{amount(teamValue(row))}</td><td className="px-4 py-3">{pct(pickNumber(row, 'ml_roi_ytd', 'mlRoiYtd'))}</td><td className="px-4 py-3">{pct(pickNumber(row, 'rl_roi_ytd', 'rlRoiYtd'))}</td><td className="px-4 py-3">{pct(pickNumber(row, 'ou_roi_ytd', 'ouRoiYtd'))}</td><td className="px-4 py-3">{amount(pickNumber(row, 'ml_profit_ytd', 'mlProfitYtd'))}</td><td className="px-4 py-3">{amount(pickNumber(row, 'rl_profit_ytd', 'rlProfitYtd'))}</td><td className="px-4 py-3">{amount(pickNumber(row, 'ou_profit_ytd', 'ouProfitYtd'))}</td></tr>)}</tbody></table></div></div>;
}

function ModelHealth({ metrics }: { metrics: JsonRow }) {
  const hasValues = ['simulated_roi_last_250', 'avg_clv_last_250', 'test_auc_runline', 'test_auc_moneyline'].some((key) => num(metrics[key]) !== null);
  return <div className="grid gap-4 lg:grid-cols-[1fr_2fr]"><div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">Health status</div><div className="mt-3"><StatusBadge value={hasValues ? 'OK' : 'UNKNOWN'} /></div><div className="mt-4 text-sm text-slate-400">As of {dateTimeLabel(pickString(metrics, 'as_of', 'asOf'))}</div><div className="mt-1 text-sm text-slate-400">Version {pickString(metrics, 'model_version', 'modelVersion') || '—'}</div></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5"><KpiCard label="MAE start score" value={amount(pickNumber(metrics, 'test_mae_start_score', 'testMaeStartScore'))} /><KpiCard label="Runline AUC" value={amount(pickNumber(metrics, 'test_auc_runline', 'testAucRunline'), 3)} /><KpiCard label="Moneyline AUC" value={amount(pickNumber(metrics, 'test_auc_moneyline', 'testAucMoneyline'), 3)} /><KpiCard label="Sim ROI last 250" value={pct(pickNumber(metrics, 'simulated_roi_last_250', 'simulatedRoiLast250'))} /><KpiCard label="Avg CLV last 250" value={pct(pickNumber(metrics, 'avg_clv_last_250', 'avgClvLast250'))} /></div>{pickString(metrics, 'notes') ? <div className="lg:col-span-2"><Alert tone="info">{pickString(metrics, 'notes')}</Alert></div> : null}</div>;
}

function ManualOverrides({ rows }: { rows: JsonRow[] }) {
  return <div className="overflow-x-auto rounded-2xl border border-slate-800"><table className="w-full text-left text-sm"><thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Created</th><th className="px-4 py-3">Game</th><th className="px-4 py-3">Team</th><th className="px-4 py-3">Market</th><th className="px-4 py-3">Field</th><th className="px-4 py-3">Original</th><th className="px-4 py-3">Override</th><th className="px-4 py-3">Reason</th><th className="px-4 py-3">Status</th></tr></thead><tbody>{rows.map((row) => <tr key={`${str(row.id)}-${pickString(row, 'created_at', 'createdAt')}`} className="border-b border-slate-800/70 text-slate-300"><td className="px-4 py-3 text-xs text-slate-500">{dateTimeLabel(pickString(row, 'created_at', 'createdAt'))}</td><td className="px-4 py-3">{pickString(row, 'game_id', 'gameId') || '—'}</td><td className="px-4 py-3 font-medium text-white">{team(row)}</td><td className="px-4 py-3">{market(row)}</td><td className="px-4 py-3">{pickString(row, 'field') || '—'}</td><td className="px-4 py-3">{amount(pickNumber(row, 'original_value', 'originalValue'))}</td><td className="px-4 py-3">{amount(pickNumber(row, 'override_value', 'overrideValue'))}</td><td className="px-4 py-3">{pickString(row, 'reason') || '—'}</td><td className="px-4 py-3"><StatusBadge value={row.active === false ? 'Inactive' : 'Active'} /></td></tr>)}</tbody></table></div>;
}

function Legacy({ diagnostics }: { diagnostics: JsonRow }) {
  const rows = [{ label: 'predictions_log', value: pickNumber(diagnostics, 'predictionsLogRows') ?? 0 }, { label: 'daily_metrics', value: pickNumber(diagnostics, 'dailyMetricsRows') ?? 0 }, { label: 'odds_snapshots', value: pickNumber(diagnostics, 'oddsSnapshotsRows') ?? 0 }];
  const total = rows.reduce((sum, row) => sum + row.value, 0);
  return <details className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4"><summary className="cursor-pointer text-sm font-semibold text-white">Show legacy diagnostic row counts</summary><div className="mt-4">{total === 0 ? <Empty>No legacy diagnostics found. Source tables are empty, not broken.</Empty> : null}<div className="mt-4 grid gap-3 md:grid-cols-3">{rows.map((row) => <KpiCard key={row.label} label={row.label} value={amount(row.value, 0)} />)}</div></div></details>;
}

export default function DashboardPage() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDashboard(initial = false) {
      if (initial) setLoading(true);
      if (!initial) setRefreshing(true);
      try {
        const [dashboard] = await Promise.allSettled([fetch('/api/mlb-dashboard', { cache: 'no-store' })]);
        if (dashboard.status === 'rejected') throw dashboard.reason instanceof Error ? dashboard.reason : new Error('Dashboard request failed');
        if (!dashboard.value.ok) throw new Error((await dashboard.value.text()) || `Dashboard API returned HTTP ${dashboard.value.status}`);
        const nextPayload = asPayload(await dashboard.value.json());
        if (!mounted) return;
        setPayload(nextPayload);
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : 'Dashboard load failed');
      } finally {
        if (!mounted) return;
        setLoading(false);
        setRefreshing(false);
      }
    }

    loadDashboard(true);
    const intervalId = window.setInterval(() => loadDashboard(false), POLL_MS);
    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const isInitialLoading = loading && !payload;
  const sectionError = apiErrorMessage(error);
  const severity = staleSeverity(payload?.dataState);
  const demo = Boolean(payload?.dataState?.isDemo);
  const projections = payload?.projections;
  const topPicks = payload?.topPicks;
  const teamMarket = payload?.teamMarket;
  const manualOverrides = payload?.manualOverrides;
  const warnings = payload?.dataState?.warnings ?? [];

  return (
    <main className="min-h-screen px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <Header payload={payload} loading={isInitialLoading} error={sectionError} refreshing={refreshing} />
        <Section title="KPI strip" description="Eight executive summary cards from /api/mlb-dashboard.summary." loading={isInitialLoading} missing={Boolean(payload && !payload.summary)} error={sectionError} empty={!payload?.summary} emptyText="No summary found." severity={severity} demo={demo}><Kpis summary={payload?.summary ?? {}} /></Section>
        <Section title="Action panel" description="Top opportunities, fade candidates and operational warnings." loading={isInitialLoading} missing={Boolean(payload && !topPicks && !projections && !payload.dataState)} error={sectionError} empty={(topPicks ?? []).length === 0 && (projections ?? []).length === 0 && warnings.length === 0} emptyText="No action panel data found." severity={severity} demo={demo}><ActionPanel topPicks={topPicks ?? []} projections={projections ?? []} warnings={warnings} /></Section>
        <Section title="Charts grid" description="EdgeDistribution, ModelVsMarketScatter, StakeByMarket and SignalsByMarket." loading={isInitialLoading} missing={Boolean(payload && !projections)} error={sectionError} empty={(projections ?? []).length === 0} emptyText="No chart data found." severity={severity} demo={demo}><Charts projections={projections ?? []} /></Section>
        <Section title="Projections table" description="Sortable/filterable projection grid with row detail drawer." loading={isInitialLoading} missing={Boolean(payload && !projections)} error={sectionError} empty={(projections ?? []).length === 0} emptyText="No projections found." severity={severity} demo={demo}><ProjectionsTable rows={projections ?? []} /></Section>
        <Section title="Team market value" description="Team inefficiency leaderboard and detailed market-value table." loading={isInitialLoading} missing={Boolean(payload && !teamMarket)} error={sectionError} empty={(teamMarket ?? []).length === 0} emptyText="No team market value found." severity={severity} demo={demo}><TeamMarket rows={teamMarket ?? []} /></Section>
        <Section title="Model health panel" description="Model version, backtest proxy metrics and CLV context." loading={isInitialLoading} missing={Boolean(payload && !('modelMetrics' in payload))} error={sectionError} empty={!payload?.modelMetrics} emptyText="No model health metrics found." severity={severity} demo={demo}>{payload?.modelMetrics ? <ModelHealth metrics={payload.modelMetrics} /> : null}</Section>
        <Section title="Manual override audit" description="Operator override history and active override visibility." loading={isInitialLoading} missing={Boolean(payload && !manualOverrides)} error={sectionError} empty={(manualOverrides ?? []).length === 0} emptyText="No manual overrides found." severity={severity} demo={demo}><ManualOverrides rows={manualOverrides ?? []} /></Section>
        <Section title="Legacy diagnostics" description="Collapsed by default; separates empty source tables from broken diagnostics." loading={isInitialLoading} missing={Boolean(payload && !payload.legacyDiagnostics)} error={sectionError} empty={!payload?.legacyDiagnostics} emptyText="No legacy diagnostics found." severity={severity} demo={demo}><Legacy diagnostics={payload?.legacyDiagnostics ?? {}} /></Section>
      </div>
    </main>
  );
}
