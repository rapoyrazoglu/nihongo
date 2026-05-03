# Migrations

Sequential SQL migrations for the Nihongo SQLite database.
Each file is applied exactly once and tracked in `schema_migrations`.

## Conventions
- Filenames: `NNNN_short_name.sql` (zero-padded 4-digit prefix).
- One migration = one logical change. Never edit a merged migration; add a new one.
- All schemas designed to be **Supabase-portable**: every user-owned row carries
  `uuid TEXT UNIQUE`, `user_id TEXT NULL`, `device_id TEXT`, `synced_at TEXT NULL`.
  When v2.0.0 lands, these tables sync straight to Postgres without re-modeling.

## Runner
`src/db.py:run_migrations()` reads `schema_migrations`, applies any new file in
lexical order inside a single transaction per file.

## Files
- `0001_init.sql` — base schema (vocabulary, kanji, grammar, reviews, stats, lessons, lesson_items)
- `0002_exam_history.sql` — exam_sessions + exam_questions (sync-ready)
