# Prompt 4 — Rollback Policy

Use **Option B (full rollback)**.

Down migration requirements:
- `DROP INDEX IF EXISTS` for the three indexes added by the up migration.
- Restore the prior table comment; if the prior comment is unknown, clear the table comment.

Do not use a partial rollback strategy for this prompt.
