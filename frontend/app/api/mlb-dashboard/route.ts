import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

type DbRow = Record<string, unknown>;

type QueryResponse<T> = {
  data: T | null;
  error: { message?: string } | null;
  count?: number | null;
};

export const dynamic = 'force-dynamic';
const STARTING_BANKROLL_UNITS = Number(process.env.STARTING_BANKROLL_UNITS ?? 100);
const PROJECTIONS_STALE_HOURS = Number(process.env.PROJECTIONS_STALE_HOURS ?? 24);

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function toStringValue(value: unknown): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return '';
}

function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function getNumber(row: DbRow, ...keys: string[]): number {
  for (const key of keys) {
    const value = toNumber(row[key]);
    if (value !== null) return value;
  }
  return 0;
}

function getString(row: DbRow, ...keys: string[]): string {
  for (const key of keys) {
    const value = toStringValue(row[key]);
    if (value) return value;
  }
  return '';
}

function getSignal(row: DbRow): string {
  return getString(row, 'bet_signal', 'betSignal', 'signal').toUpperCase() || 'UNKNOWN';
}

function getEdge(row: DbRow): number {
  return getNumber(row, 'edge_pct', 'edgePct', 'edge');
}

function getStake(row: DbRow): number {
  return getNumber(row, 'stake_units', 'stakeUnits', 'stake');
}

function isActionable(row: DbRow): boolean {
  return ['BET_STRONG', 'BET_SMALL', 'BET', 'ACTIONABLE'].includes(getSignal(row));
}

function sortProjectionRows(rows: DbRow[]): DbRow[] {
  return [...rows].sort((a, b) => {
    const edgeDiff = getEdge(b) - getEdge(a);
    if (edgeDiff !== 0) return edgeDiff;
    const confidenceDiff = getNumber(b, 'model_confidence', 'modelConfidence', 'confidence') - getNumber(a, 'model_confidence', 'modelConfidence', 'confidence');
    if (confidenceDiff !== 0) return confidenceDiff;
    return getStake(b) - getStake(a);
  });
}

function latestDate(rows: DbRow[], key: string): string | null {
  const dates = rows.map((row) => toStringValue(row[key])).filter(Boolean).sort();
  return dates.at(-1) ?? null;
}

function isStale(dateValue: string | null): boolean {
  if (!dateValue) return false;
  const parsed = new Date(dateValue);
  if (Number.isNaN(parsed.getTime())) return false;
  return Date.now() - parsed.getTime() >= PROJECTIONS_STALE_HOURS * 60 * 60 * 1000;
}

function readSettledRecord(rows: DbRow[]) {
  const settled = rows.filter((row) => ['win', 'loss', 'push'].includes(getString(row, 'result', 'truth_status').toLowerCase()));
  if (settled.length === 0) return null;

  const makeBucket = (market: string) => {
    const marketRows = settled.filter((row) => getString(row, 'market')
      ? getString(row, 'market').toLowerCase() === market
      : market === 'total');
    return {
      wins: marketRows.filter((row) => getString(row, 'result', 'truth_status').toLowerCase() === 'win').length,
      losses: marketRows.filter((row) => getString(row, 'result', 'truth_status').toLowerCase() === 'loss').length,
      pushes: marketRows.filter((row) => getString(row, 'result', 'truth_status').toLowerCase() === 'push').length,
    };
  };

  return {
    moneyline: makeBucket('moneyline'),
    runline: makeBucket('runline'),
    total: makeBucket('total'),
  };
}

function countPositiveClv(rows: DbRow[]) {
  const clvRows = rows.map((row) => toNumber(row.clv)).filter((value): value is number => value !== null);
  return {
    avgClvLast30d: average(clvRows),
    clvPositiveRate: clvRows.length === 0 ? null : clvRows.filter((value) => value > 0).length / clvRows.length,
    settledBets: clvRows.length,
  };
}

function buildSummary(projections: DbRow[], teamMarket: DbRow[], settledRows: DbRow[]) {
  const edges = projections.map(getEdge);
  const positiveEdges = edges.filter((edge) => edge > 0);
  const actionable = projections.filter(isActionable);
  const bestTeam = [...teamMarket].sort((a, b) => getNumber(b, 'value_score', 'valueScore') - getNumber(a, 'value_score', 'valueScore'))[0];
  const settled = settledRows.filter((row) => ['win', 'loss', 'push', 'void'].includes(getString(row, 'result', 'truth_status').toLowerCase()));
  const pnl = settled.map((row) => toNumber(row.pnl)).filter((value): value is number => value !== null);
  const stake = settled.map((row) => toNumber(row.stake)).filter((value): value is number => value !== null);
  const totalStake = stake.reduce((sum, value) => sum + value, 0);
  const totalPnl = pnl.reduce((sum, value) => sum + value, 0);

  return {
    activeProjections: projections.length,
    betSignals: actionable.length,
    strongBets: projections.filter((row) => getSignal(row) === 'BET_STRONG').length,
    avgEdgePct: average(edges),
    maxEdgePct: edges.length === 0 ? null : Math.max(...edges),
    totalStakeUnits: projections.reduce((sum, row) => sum + getStake(row), 0),
    positiveEdgeRate: projections.length === 0 ? null : positiveEdges.length / projections.length,
    bestTeamValue: bestTeam
      ? {
          team: getString(bestTeam, 'team'),
          valueScore: getNumber(bestTeam, 'value_score', 'valueScore'),
        }
      : null,
    realizedRoiPct: totalStake > 0 ? totalPnl / totalStake : null,
    currentBankrollUnits: pnl.length > 0 ? STARTING_BANKROLL_UNITS + totalPnl : null,
    record: readSettledRecord(settledRows),
    clv: countPositiveClv(settledRows),
  };
}

function demoPayload(warnings: string[] = []) {
  const today = new Date().toISOString().slice(0, 10);
  const projections: DbRow[] = [
    { id: 1, game_id: 'DEMO-BOS-NYY', game_date: today, team: 'BOS', opponent: 'NYY', market: 'moneyline', selection: 'BOS ML', decimal_odds: 2.1, market_probability: 0.476, final_probability: 0.535, edge_pct: 5.9, stake_units: 1.25, bet_signal: 'BET_STRONG', model_confidence: 0.72, model_version: 'demo_v0' },
    { id: 2, game_id: 'DEMO-LAD-SF', game_date: today, team: 'LAD', opponent: 'SF', market: 'runline', selection: 'LAD -1.5', decimal_odds: 1.95, market_probability: 0.513, final_probability: 0.56, edge_pct: 4.7, stake_units: 0.75, bet_signal: 'BET_SMALL', model_confidence: 0.64, model_version: 'demo_v0' },
    { id: 3, game_id: 'DEMO-ATL-PHI', game_date: today, team: 'ATL', opponent: 'PHI', market: 'total', selection: 'Over 8.5', decimal_odds: 1.91, market_probability: 0.524, final_probability: 0.548, edge_pct: 2.4, stake_units: 0.5, bet_signal: 'BET_SMALL', model_confidence: 0.59, model_version: 'demo_v0' },
    { id: 4, game_id: 'DEMO-HOU-TEX', game_date: today, team: 'TEX', opponent: 'HOU', market: 'moneyline', selection: 'TEX ML', decimal_odds: 1.8, market_probability: 0.556, final_probability: 0.512, edge_pct: -4.4, stake_units: 0, bet_signal: 'FADE', model_confidence: 0.61, model_version: 'demo_v0' },
    { id: 5, game_id: 'DEMO-SEA-OAK', game_date: today, team: 'SEA', opponent: 'OAK', market: 'total', selection: 'Under 7.5', decimal_odds: 1.88, market_probability: 0.532, final_probability: 0.526, edge_pct: -0.6, stake_units: 0, bet_signal: 'NO_BET', model_confidence: 0.51, model_version: 'demo_v0' },
  ];
  const teamMarket: DbRow[] = [
    { id: 1, as_of_date: today, team: 'BOS', ml_roi_ytd: 0.12, rl_roi_ytd: 0.04, ou_roi_ytd: 0.02, ml_profit_ytd: 8.4, rl_profit_ytd: 2.1, ou_profit_ytd: 1.2, value_score: 91 },
    { id: 2, as_of_date: today, team: 'LAD', ml_roi_ytd: 0.08, rl_roi_ytd: 0.1, ou_roi_ytd: -0.01, ml_profit_ytd: 5.5, rl_profit_ytd: 6.8, ou_profit_ytd: -0.5, value_score: 87 },
    { id: 3, as_of_date: today, team: 'ATL', ml_roi_ytd: 0.06, rl_roi_ytd: 0.03, ou_roi_ytd: 0.07, ml_profit_ytd: 3.8, rl_profit_ytd: 1.7, ou_profit_ytd: 4.9, value_score: 82 },
  ];

  return {
    summary: buildSummary(projections, teamMarket, []),
    topPicks: sortProjectionRows(projections.filter(isActionable)).slice(0, 5),
    projections,
    teamMarket,
    modelMetrics: {
      as_of: new Date().toISOString(),
      model_version: 'demo_v0',
      test_mae_start_score: 1.18,
      test_auc_runline: 0.57,
      test_auc_moneyline: 0.61,
      simulated_roi_last_250: 0.043,
      avg_clv_last_250: 0.012,
      notes: 'Demo model health values for UI verification only.',
    },
    manualOverrides: [],
    legacyDiagnostics: {
      predictionsLogRows: 0,
      dailyMetricsRows: 0,
      oddsSnapshotsRows: 0,
    },
    dataState: {
      latestProjectionDate: today,
      isStale: false,
      isDemo: true,
      warnings: ['Demo payload returned because live dashboard data is unavailable.', ...warnings],
    },
  };
}

function settledData<T>(result: PromiseSettledResult<QueryResponse<T>>, fallback: T, label: string, warnings: string[]): T {
  if (result.status === 'rejected') {
    warnings.push(`${label} query failed.`);
    return fallback;
  }
  if (result.value.error) {
    warnings.push(`${label} query failed: ${result.value.error.message ?? 'unknown error'}.`);
    return fallback;
  }
  return result.value.data ?? fallback;
}

function settledCount(result: PromiseSettledResult<QueryResponse<unknown>>, label: string, warnings: string[]): number {
  if (result.status === 'rejected') {
    warnings.push(`${label} count failed.`);
    return 0;
  }
  if (result.value.error) {
    warnings.push(`${label} count failed: ${result.value.error.message ?? 'unknown error'}.`);
    return 0;
  }
  return result.value.count ?? 0;
}

export async function GET() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.json(demoPayload(['Missing Supabase environment variables.']));
  }

  const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: { persistSession: false },
  });

  const warnings: string[] = [];
  const [projectionsResult, teamMarketResult, modelMetricsResult, manualOverridesResult, predictionsLogCount, dailyMetricsCount, oddsSnapshotsCount, predictionsLogSettledResult] = await Promise.allSettled([
    supabase.from('mlb_projections').select('*').order('game_date', { ascending: false }).order('edge_pct', { ascending: false }).limit(250),
    supabase.from('mlb_team_market_value').select('*').order('value_score', { ascending: false }).limit(100),
    supabase.from('mlb_model_metrics').select('*').order('as_of', { ascending: false }).limit(1).maybeSingle(),
    supabase.from('mlb_manual_overrides').select('*').order('created_at', { ascending: false }).limit(100),
    supabase.from('predictions_log').select('id', { count: 'exact', head: true }),
    supabase.from('daily_metrics').select('metric_date', { count: 'exact', head: true }),
    supabase.from('odds_snapshots').select('id', { count: 'exact', head: true }),
    supabase.from('predictions_log').select('truth_status,pnl,stake,clv,settled_at').not('truth_status', 'is', null).limit(2000),
  ]);

  const projections = settledData<DbRow[]>(projectionsResult, [], 'mlb_projections', warnings);
  const teamMarket = settledData<DbRow[]>(teamMarketResult, [], 'mlb_team_market_value', warnings);
  const modelMetrics = settledData<DbRow | null>(modelMetricsResult, null, 'mlb_model_metrics', warnings);
  const manualOverrides = settledData<DbRow[]>(manualOverridesResult, [], 'mlb_manual_overrides', warnings);
  const settledRows = settledData<DbRow[]>(predictionsLogSettledResult, [], 'predictions_log_settled', warnings);
  const latestProjectionDate = latestDate(projections, 'game_date');
  const stale = isStale(latestProjectionDate);
  const today = new Date().toISOString().slice(0, 10);
  const todayRows = projections.filter((row) => toStringValue(row.game_date) === today);
  const latestSlateRows = latestProjectionDate ? projections.filter((row) => toStringValue(row.game_date) === latestProjectionDate) : [];
  const displayRows = todayRows.length > 0 ? todayRows : latestSlateRows;

  if (projections.length === 0) warnings.push('No projections found.');
  if (projections.length > 0 && todayRows.length === 0) warnings.push(`No projections found for ${today}; showing latest available slate ${latestProjectionDate}.`);
  if (teamMarket.length === 0) warnings.push('No team market value rows found.');
  if (!modelMetrics) warnings.push('No model metrics row found.');
  if (stale) warnings.push('Projection data is at least 1 day old.');
  if (settledRows.length === 0) warnings.push('Realized ROI, bankroll, and record unavailable because predictions_log has no settled rows. Team market ROI is a proxy metric.');

  return NextResponse.json({
    summary: buildSummary(displayRows, teamMarket, settledRows),
    topPicks: sortProjectionRows(displayRows.filter(isActionable)).slice(0, 10),
    projections,
    teamMarket,
    modelMetrics,
    manualOverrides,
    legacyDiagnostics: {
      predictionsLogRows: settledCount(predictionsLogCount, 'predictions_log', warnings),
      dailyMetricsRows: settledCount(dailyMetricsCount, 'daily_metrics', warnings),
      oddsSnapshotsRows: settledCount(oddsSnapshotsCount, 'odds_snapshots', warnings),
    },
    dataState: {
      latestProjectionDate,
      isStale: stale,
      isDemo: false,
      warnings,
    },
  });
}
