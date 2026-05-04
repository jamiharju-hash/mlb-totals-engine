CREATE TABLE IF NOT EXISTS public.pipeline_runs (
  id              bigserial primary key,
  started_at      timestamptz not null default now(),
  completed_at    timestamptz,
  status          text not null default 'running'
                    check (status in ('running','success','partial','failed')),
  triggered_by    text,
  git_sha         text,
  rows_written    integer,
  sources_ok      text[],
  sources_failed  text[],
  error           text,
  notes           text
);
