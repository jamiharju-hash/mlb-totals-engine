import React from 'react';

export function KpiCard({
  label,
  value,
  sub,
  alert,
  trend,
}: {
  label: string;
  value: string;
  sub?: string;
  alert?: boolean;
  trend?: 'up' | 'down' | 'neutral';
}) {
  const trendSymbol = trend === 'up' ? '▲' : trend === 'down' ? '▼' : trend === 'neutral' ? '●' : null;
  const trendColor = trend === 'up' ? 'text-signal-positive' : trend === 'down' ? 'text-signal-negative' : 'text-chart-neutral';

  return (
    <article className="rounded-xl border border-border-primary bg-surface-card p-4 shadow-sm backdrop-blur-sm">
      <p className="text-xs uppercase tracking-brand text-slate-300">{label}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className={`text-3xl font-semibold ${alert ? 'text-rose-400' : 'text-slate-100'}`}>{value}</p>
        {trendSymbol ? (
          <span className={`text-xs font-medium ${trendColor}`} aria-label={`trend-${trend}`}>
            {trendSymbol}
          </span>
        ) : null}
      </div>
      {sub ? <p className="mt-1 text-xs text-slate-400">{sub}</p> : null}
    </article>
  );
}
