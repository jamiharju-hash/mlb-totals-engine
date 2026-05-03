import React from 'react';

export type StatusType = 'fresh' | 'yellow' | 'red' | 'demo' | 'unknown';

const statusStyles: Record<StatusType, string> = {
  fresh: 'bg-emerald-400',
  yellow: 'bg-amber-400',
  red: 'bg-rose-400',
  demo: 'bg-rose-400',
  unknown: 'bg-slate-400',
};

export function StatusBadge({ status, label }: { status: StatusType; label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-slate-200">
      <span className={`size-2 rounded-full ${statusStyles[status]}`} aria-hidden="true" />
      <span>{label ?? status}</span>
    </span>
  );
}
