import React from 'react';

export type SignalType = 'BET_STRONG' | 'BET_SMALL' | 'PASS' | 'FADE';

const signalStyles: Record<SignalType, string> = {
  BET_STRONG: 'bg-signal-strong-bet/20 text-signal-strong-bet ring-signal-strong-bet/50',
  BET_SMALL: 'bg-signal-small-bet/20 text-signal-small-bet ring-signal-small-bet/50',
  PASS: 'bg-signal-pass/20 text-signal-pass ring-signal-pass/50',
  FADE: 'bg-signal-fade/20 text-signal-fade ring-signal-fade/50',
};

export function SignalBadge({ signal }: { signal: SignalType }) {
  return (
    <span
      tabIndex={0}
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold tracking-wide ring-1 ring-inset outline-none transition ${signalStyles[signal]} focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950`}
    >
      {signal.replace('_', ' ')}
    </span>
  );
}
