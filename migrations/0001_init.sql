-- Base schema. Mirrors db.init_db() for fresh installs and Supabase port.

CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    reading TEXT NOT NULL,
    meaning_tr TEXT NOT NULL,
    meaning_en TEXT NOT NULL,
    meaning_de TEXT DEFAULT '',
    meaning_fr TEXT DEFAULT '',
    meaning_es TEXT DEFAULT '',
    meaning_pt TEXT DEFAULT '',
    meaning_ko TEXT DEFAULT '',
    meaning_zh TEXT DEFAULT '',
    level TEXT NOT NULL CHECK(level IN ('N5','N4','N3','N2','N1')),
    example_jp TEXT DEFAULT '',
    example_tr TEXT DEFAULT '',
    part_of_speech TEXT DEFAULT '',
    extra_examples TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS kanji (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji TEXT NOT NULL UNIQUE,
    on_yomi TEXT NOT NULL,
    kun_yomi TEXT NOT NULL,
    meaning_tr TEXT NOT NULL,
    meaning_en TEXT NOT NULL,
    meaning_de TEXT DEFAULT '',
    meaning_fr TEXT DEFAULT '',
    meaning_es TEXT DEFAULT '',
    meaning_pt TEXT DEFAULT '',
    meaning_ko TEXT DEFAULT '',
    meaning_zh TEXT DEFAULT '',
    level TEXT NOT NULL CHECK(level IN ('N5','N4','N3','N2','N1')),
    stroke_count INTEGER DEFAULT 0,
    compounds TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS grammar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL UNIQUE,
    meaning_tr TEXT NOT NULL,
    meaning_en TEXT NOT NULL,
    meaning_de TEXT DEFAULT '',
    meaning_fr TEXT DEFAULT '',
    meaning_es TEXT DEFAULT '',
    meaning_pt TEXT DEFAULT '',
    meaning_ko TEXT DEFAULT '',
    meaning_zh TEXT DEFAULT '',
    level TEXT NOT NULL CHECK(level IN ('N5','N4','N3','N2','N1')),
    example_jp TEXT DEFAULT '',
    example_tr TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_type TEXT NOT NULL CHECK(card_type IN ('vocabulary','kanji','grammar')),
    card_id INTEGER NOT NULL,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    interval INTEGER NOT NULL DEFAULT 0,
    repetitions INTEGER NOT NULL DEFAULT 0,
    next_review TEXT NOT NULL,
    last_review TEXT,
    weak_kanji INTEGER DEFAULT 0,
    UNIQUE(card_type, card_id)
);

CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    cards_reviewed INTEGER DEFAULT 0,
    cards_correct INTEGER DEFAULT 0,
    cards_new INTEGER DEFAULT 0,
    study_seconds INTEGER DEFAULT 0,
    UNIQUE(date)
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    textbook TEXT NOT NULL,
    lesson_no INTEGER NOT NULL,
    title TEXT NOT NULL,
    title_ja TEXT DEFAULT '',
    level TEXT NOT NULL,
    UNIQUE(textbook, lesson_no)
);

CREATE TABLE IF NOT EXISTS lesson_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    item_type TEXT NOT NULL CHECK(item_type IN ('vocabulary','kanji','grammar')),
    item_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
    UNIQUE(lesson_id, item_type, item_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_next ON reviews(next_review);
CREATE INDEX IF NOT EXISTS idx_reviews_type ON reviews(card_type);
CREATE INDEX IF NOT EXISTS idx_vocab_level ON vocabulary(level);
CREATE INDEX IF NOT EXISTS idx_kanji_level ON kanji(level);
CREATE INDEX IF NOT EXISTS idx_grammar_level ON grammar(level);
CREATE INDEX IF NOT EXISTS idx_lesson_items_lesson ON lesson_items(lesson_id);
