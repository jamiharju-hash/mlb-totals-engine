-- Force Row Level Security for every existing table in the public schema.
--
-- This migration intentionally enables and forces RLS. FORCE RLS makes table
-- owners subject to RLS policies too. Service-role connections can still bypass
-- RLS, so keep SUPABASE_SERVICE_ROLE_KEY strictly backend-only.
--
-- Important: enabling RLS without policies blocks anon/authenticated access by
-- default. Add explicit policies per table after this migration.

DO $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            table_record.schemaname,
            table_record.tablename
        );

        EXECUTE format(
            'ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY',
            table_record.schemaname,
            table_record.tablename
        );
    END LOOP;
END $$;

-- Optional verification query:
-- SELECT
--     n.nspname AS schema_name,
--     c.relname AS table_name,
--     c.relrowsecurity AS rls_enabled,
--     c.relforcerowsecurity AS rls_forced
-- FROM pg_class c
-- JOIN pg_namespace n ON n.oid = c.relnamespace
-- WHERE n.nspname = 'public'
--   AND c.relkind = 'r'
-- ORDER BY c.relname;
