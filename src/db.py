"""Veritabanı işlemleri - SQLite3 ile JLPT öğrenme veritabanı."""

import sqlite3
import os
import shutil
from datetime import datetime, date

from paths import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Veritabanı tablolarını oluştur."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
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

        CREATE INDEX IF NOT EXISTS idx_reviews_next ON reviews(next_review);
        CREATE INDEX IF NOT EXISTS idx_reviews_type ON reviews(card_type);
        CREATE INDEX IF NOT EXISTS idx_vocab_level ON vocabulary(level);
        CREATE INDEX IF NOT EXISTS idx_kanji_level ON kanji(level);
        CREATE INDEX IF NOT EXISTS idx_grammar_level ON grammar(level);
    """)

    # Migration: weak_kanji kolonu (okuma biliyor ama kanji bilmiyor)
    try:
        conn.execute("ALTER TABLE reviews ADD COLUMN weak_kanji INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # zaten var

    conn.commit()
    conn.close()


# --- Vocabulary ---

def get_vocabulary(level=None, limit=None):
    conn = get_connection()
    query = "SELECT * FROM vocabulary"
    params = []
    if level:
        query += " WHERE level = ?"
        params.append(level)
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_vocab_by_id(vocab_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM vocabulary WHERE id = ?", (vocab_id,)).fetchone()
    conn.close()
    return row


def count_vocabulary(level=None):
    conn = get_connection()
    if level:
        row = conn.execute("SELECT COUNT(*) as cnt FROM vocabulary WHERE level = ?", (level,)).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as cnt FROM vocabulary").fetchone()
    conn.close()
    return row["cnt"]


# --- Kanji ---

def get_kanji(level=None, limit=None):
    conn = get_connection()
    query = "SELECT * FROM kanji"
    params = []
    if level:
        query += " WHERE level = ?"
        params.append(level)
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_kanji_by_id(kanji_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM kanji WHERE id = ?", (kanji_id,)).fetchone()
    conn.close()
    return row


def count_kanji(level=None):
    conn = get_connection()
    if level:
        row = conn.execute("SELECT COUNT(*) as cnt FROM kanji WHERE level = ?", (level,)).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as cnt FROM kanji").fetchone()
    conn.close()
    return row["cnt"]


# --- Grammar ---

def get_grammar(level=None, limit=None):
    conn = get_connection()
    query = "SELECT * FROM grammar"
    params = []
    if level:
        query += " WHERE level = ?"
        params.append(level)
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_grammar_by_id(grammar_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM grammar WHERE id = ?", (grammar_id,)).fetchone()
    conn.close()
    return row


def count_grammar(level=None):
    conn = get_connection()
    if level:
        row = conn.execute("SELECT COUNT(*) as cnt FROM grammar WHERE level = ?", (level,)).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as cnt FROM grammar").fetchone()
    conn.close()
    return row["cnt"]


# --- Reviews (SRS) ---

def get_due_reviews(card_type=None, limit=50):
    """Bugün veya öncesinde tekrarlanması gereken kartları getir.
    weak_kanji=1 olanlar önce gelir."""
    conn = get_connection()
    today = date.today().isoformat()
    query = "SELECT * FROM reviews WHERE next_review <= ?"
    params = [today]
    if card_type:
        query += " AND card_type = ?"
        params.append(card_type)
    query += " ORDER BY weak_kanji DESC, next_review ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_review(card_type, card_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM reviews WHERE card_type = ? AND card_id = ?",
        (card_type, card_id)
    ).fetchone()
    conn.close()
    return row


def upsert_review(card_type, card_id, ease_factor, interval, repetitions, next_review, weak_kanji=None):
    conn = get_connection()
    if weak_kanji is not None:
        conn.execute("""
            INSERT INTO reviews (card_type, card_id, ease_factor, interval, repetitions, next_review, last_review, weak_kanji)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_type, card_id) DO UPDATE SET
                ease_factor = excluded.ease_factor,
                interval = excluded.interval,
                repetitions = excluded.repetitions,
                next_review = excluded.next_review,
                last_review = excluded.last_review,
                weak_kanji = excluded.weak_kanji
        """, (card_type, card_id, ease_factor, interval, repetitions, next_review, date.today().isoformat(), weak_kanji))
    else:
        conn.execute("""
            INSERT INTO reviews (card_type, card_id, ease_factor, interval, repetitions, next_review, last_review)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_type, card_id) DO UPDATE SET
                ease_factor = excluded.ease_factor,
                interval = excluded.interval,
                repetitions = excluded.repetitions,
                next_review = excluded.next_review,
                last_review = excluded.last_review
        """, (card_type, card_id, ease_factor, interval, repetitions, next_review, date.today().isoformat()))
    conn.commit()
    conn.close()


def get_new_cards(card_type, level, limit=10):
    """Henüz SRS'e eklenmemiş kartları getir."""
    conn = get_connection()
    table = card_type  # vocabulary, kanji, grammar
    rows = conn.execute(f"""
        SELECT t.* FROM {table} t
        LEFT JOIN reviews r ON r.card_type = ? AND r.card_id = t.id
        WHERE r.id IS NULL AND t.level = ?
        LIMIT ?
    """, (card_type, level, limit)).fetchall()
    conn.close()
    return rows


def count_due_reviews(card_type=None):
    conn = get_connection()
    today = date.today().isoformat()
    if card_type:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE next_review <= ? AND card_type = ?",
            (today, card_type)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE next_review <= ?",
            (today,)
        ).fetchone()
    conn.close()
    return row["cnt"]


def count_learned(card_type=None, level=None):
    conn = get_connection()
    if card_type and level:
        table = card_type  # vocabulary, kanji, grammar
        row = conn.execute(f"""
            SELECT COUNT(*) as cnt FROM reviews r
            JOIN {table} t ON t.id = r.card_id
            WHERE r.card_type = ? AND t.level = ?
        """, (card_type, level)).fetchone()
    elif card_type:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE card_type = ?",
            (card_type,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as cnt FROM reviews").fetchone()
    conn.close()
    return row["cnt"]


def count_mastered(card_type=None, level=None):
    """interval >= 21 gun olan (iyi bilinen) kartlari say."""
    conn = get_connection()
    if card_type and level:
        table = card_type
        row = conn.execute(f"""
            SELECT COUNT(*) as cnt FROM reviews r
            JOIN {table} t ON t.id = r.card_id
            WHERE r.card_type = ? AND t.level = ? AND r.interval >= 21
        """, (card_type, level)).fetchone()
    elif card_type:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE card_type = ? AND interval >= 21",
            (card_type,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) as cnt FROM reviews WHERE interval >= 21").fetchone()
    conn.close()
    return row["cnt"]


# --- Stats ---

def update_stats(reviewed=0, correct=0, new=0, seconds=0):
    conn = get_connection()
    today = date.today().isoformat()
    conn.execute("""
        INSERT INTO stats (date, cards_reviewed, cards_correct, cards_new, study_seconds)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            cards_reviewed = cards_reviewed + excluded.cards_reviewed,
            cards_correct = cards_correct + excluded.cards_correct,
            cards_new = cards_new + excluded.cards_new,
            study_seconds = study_seconds + excluded.study_seconds
    """, (today, reviewed, correct, new, seconds))
    conn.commit()
    conn.close()


def get_stats(days=7):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM stats ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    conn.close()
    return rows


def get_today_stats():
    conn = get_connection()
    today = date.today().isoformat()
    row = conn.execute("SELECT * FROM stats WHERE date = ?", (today,)).fetchone()
    conn.close()
    return row


def get_streak():
    """Ard arda calisilan gun sayisini hesapla."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT date FROM stats WHERE cards_reviewed > 0 ORDER BY date DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return 0

    from datetime import timedelta
    streak = 0
    expected = date.today()

    for row in rows:
        d = date.fromisoformat(row["date"])
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif d < expected:
            break

    return streak


# --- Arama ---

def search_all(query):
    """3 tabloda LIKE araması yap. Sonuçları dict olarak döndür."""
    conn = get_connection()
    q = f"%{query}%"

    vocab = conn.execute("""
        SELECT * FROM vocabulary
        WHERE word LIKE ? OR reading LIKE ? OR meaning_tr LIKE ? OR meaning_en LIKE ?
    """, (q, q, q, q)).fetchall()

    kanji = conn.execute("""
        SELECT * FROM kanji
        WHERE kanji LIKE ? OR on_yomi LIKE ? OR kun_yomi LIKE ?
              OR meaning_tr LIKE ? OR meaning_en LIKE ?
    """, (q, q, q, q, q)).fetchall()

    grammar = conn.execute("""
        SELECT * FROM grammar
        WHERE pattern LIKE ? OR meaning_tr LIKE ? OR meaning_en LIKE ?
    """, (q, q, q)).fetchall()

    conn.close()
    return {
        "vocabulary": [dict(r) for r in vocab],
        "kanji": [dict(r) for r in kanji],
        "grammar": [dict(r) for r in grammar],
    }


# --- Export / Import ---

def export_anki_tsv(card_type, filepath):
    """Anki uyumlu front\\tback TSV dosyası oluştur."""
    conn = get_connection()

    if card_type == "vocabulary":
        rows = conn.execute("SELECT word, reading, meaning_tr, meaning_en FROM vocabulary").fetchall()
        lines = [f"{r['word']} ({r['reading']})\t{r['meaning_tr']} / {r['meaning_en']}" for r in rows]
    elif card_type == "kanji":
        rows = conn.execute("SELECT kanji, on_yomi, kun_yomi, meaning_tr, meaning_en FROM kanji").fetchall()
        lines = [f"{r['kanji']}\t{r['meaning_tr']} / {r['meaning_en']} (On: {r['on_yomi']}, Kun: {r['kun_yomi']})" for r in rows]
    elif card_type == "grammar":
        rows = conn.execute("SELECT pattern, meaning_tr, meaning_en, example_jp FROM grammar").fetchall()
        lines = [f"{r['pattern']}\t{r['meaning_tr']} / {r['meaning_en']}" for r in rows]
    else:
        conn.close()
        return 0

    conn.close()

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return len(lines)


def backup_db(dest_path):
    """Veritabanını yedekle."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(DB_PATH, dest_path)


def restore_db(src_path):
    """Yedekten veritabanını geri yükle."""
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Yedek dosyası bulunamadı: {src_path}")
    shutil.copy2(src_path, DB_PATH)
