-- Adaptive mastery / Elo-style ranking. Supabase-portable.
-- Bu sistem mevcut SRS (reviews) ile paraleldir; SRS schedule belirler,
-- mastery zorluk + kullanici becerisi + tekrar oncelıği belirler.

-- Per-item mastery rating (kullanicinin bu ogeyi ne kadar bildigi).
CREATE TABLE IF NOT EXISTS mastery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id TEXT,                       -- v2.0 auth sonrasi dolacak
    device_id TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('vocabulary','kanji','grammar')),
    entity_id INTEGER NOT NULL,
    rating REAL NOT NULL DEFAULT 1400,
    rating_deviation REAL NOT NULL DEFAULT 350,  -- Glicko-2 hazirligi
    reviews_count INTEGER NOT NULL DEFAULT 0,
    last_review_at TEXT,                -- ISO-8601, NULL = henuz hic gorulmedi
    synced_at TEXT,
    UNIQUE(entity_type, entity_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_mastery_lookup
    ON mastery(entity_type, entity_id, device_id);
CREATE INDEX IF NOT EXISTS idx_mastery_rating
    ON mastery(entity_type, rating);
CREATE INDEX IF NOT EXISTS idx_mastery_last_review
    ON mastery(last_review_at);

-- Skill bazli rating (vocab, kanji, grammar genel; ya da theme:shopping vb).
-- Item etkileşimleri toplu olarak skill'e küçük katsayıyla yansır.
CREATE TABLE IF NOT EXISTS skill_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id TEXT,
    device_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,           -- 'vocab'|'kanji'|'grammar'|'theme:shopping'|'lesson:genki1:L4'
    rating REAL NOT NULL DEFAULT 1400,
    updated_at TEXT NOT NULL,
    synced_at TEXT,
    UNIQUE(skill_name, device_id)
);

CREATE INDEX IF NOT EXISTS idx_skill_ratings_lookup
    ON skill_ratings(skill_name, device_id);

-- Cevap gecmisi: her tek soru-cevap interaction kaydı. Kullanılır:
--  - Wrong-pattern analizi (Phase 2'de Gemini icin)
--  - Tekrar zamanlamasi (uzun zaman gormedigi item'lar)
--  - Audit / istatistik
CREATE TABLE IF NOT EXISTS answer_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id TEXT,
    device_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    question_subtype TEXT,              -- mc | typing | flashcard | exam ...
    correct INTEGER NOT NULL,           -- 0|1
    confidence INTEGER,                 -- 1=guess, 2=unsure, 3=knew, 4=easy (NULL=sorulmadi)
    rating_before REAL,
    rating_after REAL,
    asked_at TEXT NOT NULL,
    synced_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_answer_log_entity
    ON answer_log(entity_type, entity_id, asked_at DESC);
CREATE INDEX IF NOT EXISTS idx_answer_log_recent
    ON answer_log(asked_at DESC);
CREATE INDEX IF NOT EXISTS idx_answer_log_sync
    ON answer_log(synced_at);
