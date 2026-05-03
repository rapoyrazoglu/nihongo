-- Exam sessions + per-question history. Supabase-portable.
-- Every row carries uuid + user_id + device_id + synced_at so a future
-- sync engine can push these straight to Postgres without translation.

CREATE TABLE IF NOT EXISTS exam_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id TEXT,                     -- populated after v2.0.0 auth
    device_id TEXT NOT NULL,
    exam_kind TEXT NOT NULL,          -- 'jlpt' | 'genki'
    exam_scope TEXT NOT NULL,         -- 'N5' for jlpt, 'genki1:L3' for genki
    level TEXT NOT NULL,              -- N5/N4/...
    started_at TEXT NOT NULL,         -- ISO-8601
    finished_at TEXT,
    score_correct INTEGER,
    score_total INTEGER,
    duration_seconds INTEGER,
    synced_at TEXT
);

CREATE TABLE IF NOT EXISTS exam_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    session_uuid TEXT NOT NULL,
    user_id TEXT,
    device_id TEXT NOT NULL,
    section TEXT NOT NULL,            -- 'vocabulary' | 'grammar'
    question_subtype TEXT NOT NULL,   -- kanji_to_reading, reading_to_kanji,
                                      -- meaning_to_word, word_to_meaning,
                                      -- pattern_to_meaning, bun_kumitate
    item_type TEXT NOT NULL,          -- vocabulary | grammar
    item_id INTEGER NOT NULL,
    question_signature TEXT NOT NULL, -- (item_type, item_id, question_subtype)
                                      -- — used for "don't show same q again"
    correct INTEGER,                  -- 0/1; NULL if skipped
    asked_at TEXT NOT NULL,
    synced_at TEXT,
    FOREIGN KEY (session_uuid) REFERENCES exam_sessions(uuid)
);

CREATE INDEX IF NOT EXISTS idx_exam_q_signature
    ON exam_questions(question_signature, asked_at DESC);
CREATE INDEX IF NOT EXISTS idx_exam_q_session
    ON exam_questions(session_uuid);
CREATE INDEX IF NOT EXISTS idx_exam_s_kind_scope
    ON exam_sessions(exam_kind, exam_scope, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_exam_s_sync
    ON exam_sessions(synced_at);
CREATE INDEX IF NOT EXISTS idx_exam_q_sync
    ON exam_questions(synced_at);
