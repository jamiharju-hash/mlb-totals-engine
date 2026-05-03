import React, { type ReactNode } from 'react';

export function DataState({ state, message, children }: { state?: 'loading' | 'empty' | 'error'; message?: string; children?: ReactNode }) {
  if (!state || children) {
    return <>{children}</>;
  }

  if (state === 'loading') {
    return <div className="h-24 animate-pulse rounded-lg bg-slate-800" aria-label="loading-skeleton" />;
  }

  if (state === 'empty') {
    return <p className="rounded-lg border border-border-subtle bg-surface-panel p-4 text-sm text-slate-300">{message ?? 'No data available.'}</p>;
  }

  return (
    <p className="rounded-lg border border-rose-900 bg-surface-error p-4 text-sm text-rose-200">
      {message ?? 'Error loading data.'} Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
    </p>
  );
}
