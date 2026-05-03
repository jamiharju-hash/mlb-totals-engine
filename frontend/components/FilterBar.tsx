import React from 'react';

type Filters = {
  market: string[];
  signal: string[];
  team: string[];
  search: string;
  positiveEdgeOnly: boolean;
  betSignalsOnly: boolean;
};

type FilterBarProps = {
  markets: string[];
  signals: string[];
  teams: string[];
  active: Filters;
  onChange: (filters: Filters) => void;
};

function Pill({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-xs transition ${
        active
          ? 'border-sky-400 bg-sky-500/20 text-sky-200'
          : 'border-border-subtle bg-surface-panel text-slate-300 hover:border-slate-500'
      }`}
    >
      {children}
    </button>
  );
}

const toggleFromList = (list: string[], value: string) => (list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

export function FilterBar({ markets, signals, teams, active, onChange }: FilterBarProps) {
  return (
    <section className="space-y-3 rounded-xl border border-border-primary bg-surface-panel p-3">
      <input
        value={active.search}
        onChange={(e) => onChange({ ...active, search: e.target.value })}
        placeholder="Search team or market"
        className="w-full rounded-md border border-border-subtle bg-slate-950/40 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500"
      />

      <div className="flex flex-wrap gap-2">
        {markets.map((market) => (
          <Pill key={market} active={active.market.includes(market)} onClick={() => onChange({ ...active, market: toggleFromList(active.market, market) })}>
            {market}
          </Pill>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {signals.map((signal) => (
          <Pill key={signal} active={active.signal.includes(signal)} onClick={() => onChange({ ...active, signal: toggleFromList(active.signal, signal) })}>
            {signal}
          </Pill>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {teams.map((team) => (
          <Pill key={team} active={active.team.includes(team)} onClick={() => onChange({ ...active, team: toggleFromList(active.team, team) })}>
            {team}
          </Pill>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Pill active={active.positiveEdgeOnly} onClick={() => onChange({ ...active, positiveEdgeOnly: !active.positiveEdgeOnly })}>
          positive edge only
        </Pill>
        <Pill active={active.betSignalsOnly} onClick={() => onChange({ ...active, betSignalsOnly: !active.betSignalsOnly })}>
          bet signals only
        </Pill>
      </div>
    </section>
  );
}

export type { Filters };
