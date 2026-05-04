"""Veritabanı işlemleri - SQLite3 ile JLPT öğrenme veritabanı."""

import sqlite3
import os
import shutil
import glob
import json
import difflib
import uuid as uuid_lib
from datetime import datetime, date

from paths import DB_PATH, MIGRATIONS_DIR, LANG_DIR


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _device_id():
    """Stable per-install device id. Used in exam rows for future Supabase sync."""
    from paths import CONFIG_PATH
    import json
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    did = cfg.get("device_id")
    if not did:
        did = str(uuid_lib.uuid4())
        cfg["device_id"] = did
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    return did


def run_migrations():
    """Apply pending SQL migrations from MIGRATIONS_DIR in lexical order.
    Each file runs once; applied filenames stored in schema_migrations."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()

    if not os.path.isdir(MIGRATIONS_DIR):
        conn.close()
        return

    applied = {r["filename"] for r in conn.execute("SELECT filename FROM schema_migrations").fetchall()}
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    for path in files:
        name = os.path.basename(path)
        if name in applied:
            continue
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                (name, datetime.utcnow().isoformat() + "Z"),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            conn.close()
            raise
    conn.close()


def init_db():
    """Veritabanı tablolarını oluştur. Önce migration dosyalarını uygula."""
    run_migrations()

    conn = get_connection()
    c = conn.cursor()

    # Migration sistemi öncesi kalan eski DB'ler için fallback CREATE'ler
    # (yeni kurulumlarda zaten 0001_init.sql çalıştığı için no-op olur).
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


def _search_is_empty(results):
    return not (results["vocabulary"] or results["kanji"] or results["grammar"])


def _load_synonyms(lang):
    path = os.path.join(LANG_DIR, f"synonyms_{lang}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k.strip().lower(): v for k, v in data.items() if not k.startswith("_")}


_VALID_LANGS = {"tr", "en", "de", "fr", "es", "pt", "ko", "zh"}


def _all_meanings(lang):
    """Tüm vocab/grammar/kanji anlamlarını fuzzy match için döner."""
    if lang not in _VALID_LANGS:
        lang = "en"
    field = f"meaning_{lang}"
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT {field} as m FROM vocabulary WHERE {field} != ''
        UNION SELECT {field} FROM grammar WHERE {field} != ''
        UNION SELECT {field} FROM kanji WHERE {field} != ''
    """).fetchall()
    conn.close()
    return [r["m"] for r in rows if r["m"]]


def _merge_results(results_list):
    """Birden fazla arama sonucunu id'ye göre dedup'lı birleştir."""
    merged = {"vocabulary": [], "kanji": [], "grammar": []}
    seen = {"vocabulary": set(), "kanji": set(), "grammar": set()}
    for r in results_list:
        for k in merged:
            for item in r[k]:
                if item["id"] not in seen[k]:
                    seen[k].add(item["id"])
                    merged[k].append(item)
    return merged


def search_smart(query, lang="en"):
    """Aşamalı arama: önce LIKE, boşsa synonym map (anlamsal),
    sonra difflib (typo). Genişletme bilgisini de döner.

    Returns: (results, expansion)
    expansion = None                                                 # direkt eşleşme
              | {"kind": "synonym", "from": q, "to": [terms]}        # anlamsal
              | {"kind": "fuzzy",   "from": q, "to": [matches]}      # yazım hatası
    """
    direct = search_all(query)
    if not _search_is_empty(direct):
        return direct, None

    qlow = (query or "").strip().lower()
    if not qlow:
        return direct, None

    # 1) Anlamsal genişletme (deterministik)
    synonyms = _load_synonyms(lang).get(qlow, [])
    if synonyms:
        merged = _merge_results([search_all(s) for s in synonyms])
        if not _search_is_empty(merged):
            return merged, {"kind": "synonym", "from": query, "to": synonyms}

    # 2) Yazım hatası düzeltme (heuristik)
    meanings_lower = {m.lower(): m for m in _all_meanings(lang)}
    close = difflib.get_close_matches(qlow, list(meanings_lower.keys()), n=3, cutoff=0.75)
    if close:
        merged = _merge_results([search_all(meanings_lower[c]) for c in close])
        if not _search_is_empty(merged):
            return merged, {"kind": "fuzzy", "from": query,
                            "to": [meanings_lower[c] for c in close]}

    return direct, None


# --- Lessons / Textbooks ---

def get_lessons(textbook=None, level=None):
    """Ders listesini sıralı döner. textbook ve/veya level ile filtrele."""
    conn = get_connection()
    where, args = [], []
    if textbook:
        where.append("textbook = ?"); args.append(textbook)
    if level:
        where.append("level = ?"); args.append(level)
    sql = "SELECT * FROM lessons"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY textbook, lesson_no"
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_textbook_levels():
    """Hangi level'larda en az bir ders var, sayısıyla."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT level, COUNT(*) as cnt FROM lessons GROUP BY level"
    ).fetchall()
    conn.close()
    return {r["level"]: r["cnt"] for r in rows}


def get_lesson(lesson_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_lesson_items(lesson_id, item_type=None):
    """Bir derse bağlı item'ları (vocab/kanji/grammar) döner.
    Dönen kayıtlar item tablosundan çekilir, item_type alanı eklenir.
    """
    conn = get_connection()
    types = [item_type] if item_type else ["vocabulary", "kanji", "grammar"]
    result = {"vocabulary": [], "kanji": [], "grammar": []}
    for t in types:
        table = t  # vocabulary/kanji/grammar
        rows = conn.execute(f"""
            SELECT i.*, li.sort_order FROM {table} i
            JOIN lesson_items li ON li.item_id = i.id AND li.item_type = ?
            WHERE li.lesson_id = ?
            ORDER BY li.sort_order, i.id
        """, (t, lesson_id)).fetchall()
        result[t] = [dict(r) for r in rows]
    conn.close()
    return result


def get_lesson_progress(lesson_id):
    """Bir ders için öğrenilen / toplam kart sayısı (vocab+kanji+grammar)."""
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) as c FROM lesson_items WHERE lesson_id = ?", (lesson_id,)
    ).fetchone()["c"]
    learned = conn.execute("""
        SELECT COUNT(*) as c FROM lesson_items li
        JOIN reviews r ON r.card_type = li.item_type AND r.card_id = li.item_id
        WHERE li.lesson_id = ? AND r.repetitions > 0
    """, (lesson_id,)).fetchone()["c"]
    conn.close()
    return {"total": total, "learned": learned}


# --- Mastery / Adaptive Engine ---

def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _days_since(iso_ts):
    if not iso_ts:
        return 999
    from datetime import datetime, timezone
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return 999
    return (datetime.now(timezone.utc) - ts).days


def get_mastery(entity_type, entity_id):
    """Bir item'in mastery row'unu doner. Yoksa None — caller create_or_get kullanır."""
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM mastery
        WHERE entity_type = ? AND entity_id = ? AND device_id = ?
    """, (entity_type, entity_id, _device_id())).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_mastery(entity_type, entity_id, rating, rating_deviation=None, reviews_count=None):
    """Mastery row insert et veya update et."""
    conn = get_connection()
    existing = conn.execute("""
        SELECT id, reviews_count, rating_deviation FROM mastery
        WHERE entity_type = ? AND entity_id = ? AND device_id = ?
    """, (entity_type, entity_id, _device_id())).fetchone()
    now = _now_iso()
    if existing:
        rd = rating_deviation if rating_deviation is not None else existing["rating_deviation"]
        rc = reviews_count if reviews_count is not None else existing["reviews_count"]
        conn.execute("""
            UPDATE mastery SET rating = ?, rating_deviation = ?, reviews_count = ?, last_review_at = ?
            WHERE id = ?
        """, (rating, rd, rc, now, existing["id"]))
    else:
        conn.execute("""
            INSERT INTO mastery (uuid, device_id, entity_type, entity_id, rating, rating_deviation, reviews_count, last_review_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid_lib.uuid4()), _device_id(), entity_type, entity_id, rating,
            rating_deviation if rating_deviation is not None else 350.0,
            reviews_count if reviews_count is not None else 0,
            now,
        ))
    conn.commit()
    conn.close()


def get_skill_rating(skill_name):
    """Skill rating row. Yoksa varsayılan 1400 olarak doner ama yazmaz."""
    conn = get_connection()
    row = conn.execute("""
        SELECT rating FROM skill_ratings WHERE skill_name = ? AND device_id = ?
    """, (skill_name, _device_id())).fetchone()
    conn.close()
    return row["rating"] if row else 1400.0


def upsert_skill_rating(skill_name, rating):
    conn = get_connection()
    existing = conn.execute("""
        SELECT id FROM skill_ratings WHERE skill_name = ? AND device_id = ?
    """, (skill_name, _device_id())).fetchone()
    now = _now_iso()
    if existing:
        conn.execute("UPDATE skill_ratings SET rating = ?, updated_at = ? WHERE id = ?",
                     (rating, now, existing["id"]))
    else:
        conn.execute("""
            INSERT INTO skill_ratings (uuid, device_id, skill_name, rating, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid_lib.uuid4()), _device_id(), skill_name, rating, now))
    conn.commit()
    conn.close()


def log_answer(entity_type, entity_id, correct, confidence, rating_before, rating_after,
               question_subtype=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO answer_log (uuid, device_id, entity_type, entity_id, question_subtype,
                                correct, confidence, rating_before, rating_after, asked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid_lib.uuid4()), _device_id(), entity_type, entity_id, question_subtype,
        1 if correct else 0, confidence, rating_before, rating_after, _now_iso(),
    ))
    conn.commit()
    conn.close()


def record_answer(entity_type, entity_id, correct, confidence=None, question_subtype=None):
    """One-shot helper: cevap sonrasi mastery + skill_rating + answer_log update.

    Returns dict with new ratings for UI feedback.
    """
    import elo
    m = get_mastery(entity_type, entity_id)
    if m:
        item_rating = m["rating"]
        # Item rating: bu kullanicinin skoruna göre değil, herkes için ortak.
        # Şimdilik device-bazlı tutuyoruz; v2.0 backend'de global olur.
        # Burada item_rating "yerel sürüm" olarak başlar 1400'den.
    else:
        item_rating = elo.INITIAL_RATING
    user_item_rating = m["rating"] if m else elo.INITIAL_RATING
    reviews_count = (m["reviews_count"] if m else 0) + 1

    # Tek bir 'rating' alanımız var (mastery.rating) — bunu user-for-this-item olarak
    # kullanıyoruz. Item difficulty'yi şimdilik aynı sayıdan başlatıp ayrı tutmuyoruz;
    # v2.0 sync'te ayrı kolon eklenir. Pratikte bu device-local sistem.
    new_user_rating, new_item_rating = elo.update(
        user_item_rating, item_rating, correct, reviews_count, confidence
    )
    upsert_mastery(entity_type, entity_id, new_user_rating, reviews_count=reviews_count)

    # Skill rating güncelle
    skill_name = entity_type  # 'vocabulary'|'kanji'|'grammar'
    skill_rating = get_skill_rating(skill_name)
    skill_delta = elo.skill_delta(new_user_rating - user_item_rating)
    new_skill = max(800.0, min(2800.0, skill_rating + skill_delta))
    upsert_skill_rating(skill_name, new_skill)

    # Audit
    log_answer(entity_type, entity_id, correct, confidence,
               user_item_rating, new_user_rating, question_subtype)

    return {
        "rating_before": user_item_rating,
        "rating_after": new_user_rating,
        "delta": new_user_rating - user_item_rating,
        "status": elo.status_label(new_user_rating),
        "skill_rating": new_skill,
    }


def get_mastery_summary():
    """Stats ekrani icin: rating dagilimi."""
    conn = get_connection()
    by_type = {}
    for et in ("vocabulary", "kanji", "grammar"):
        rows = conn.execute("""
            SELECT rating FROM mastery WHERE entity_type = ? AND device_id = ?
        """, (et, _device_id())).fetchall()
        ratings = [r["rating"] for r in rows]
        if not ratings:
            by_type[et] = None
            continue
        new_count = sum(1 for r in ratings if r < 1500)
        learning = sum(1 for r in ratings if 1500 <= r < 1800)
        mastered = sum(1 for r in ratings if r >= 1800)
        by_type[et] = {
            "total": len(ratings),
            "avg": sum(ratings) / len(ratings),
            "new": new_count,
            "learning": learning,
            "mastered": mastered,
        }
    skills = {}
    for sk in ("vocabulary", "kanji", "grammar"):
        skills[sk] = get_skill_rating(sk)
    conn.close()
    return {"items": by_type, "skills": skills}


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


# --- Exam history (sync-ready) ---

def question_signature(item_type, item_id, question_subtype):
    """Tek bir soruyu temsil eden imza. Aynı imza = aynı soru,
    distractor seti farklı olsa bile."""
    return f"{item_type}:{item_id}:{question_subtype}"


def start_exam_session(exam_kind, exam_scope, level):
    """Yeni sınav oturumu aç. UUID döner (sonradan referans için)."""
    sid = str(uuid_lib.uuid4())
    conn = get_connection()
    conn.execute("""
        INSERT INTO exam_sessions (uuid, device_id, exam_kind, exam_scope, level, started_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sid, _device_id(), exam_kind, exam_scope, level,
          datetime.utcnow().isoformat() + "Z"))
    conn.commit()
    conn.close()
    return sid


def finish_exam_session(session_uuid, score_correct, score_total, duration_seconds):
    conn = get_connection()
    conn.execute("""
        UPDATE exam_sessions
        SET finished_at = ?, score_correct = ?, score_total = ?, duration_seconds = ?
        WHERE uuid = ?
    """, (datetime.utcnow().isoformat() + "Z",
          score_correct, score_total, duration_seconds, session_uuid))
    conn.commit()
    conn.close()


def record_exam_question(session_uuid, section, question_subtype, item_type, item_id, correct):
    """Sınavda sorulan tek bir soruyu kaydet. correct: 0/1/None (skip)."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO exam_questions
            (uuid, session_uuid, device_id, section, question_subtype,
             item_type, item_id, question_signature, correct, asked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid_lib.uuid4()), session_uuid, _device_id(), section, question_subtype,
        item_type, item_id, question_signature(item_type, item_id, question_subtype),
        correct, datetime.utcnow().isoformat() + "Z",
    ))
    conn.commit()
    conn.close()


def get_recent_question_signatures(exam_kind, exam_scope=None, days=14):
    """Son `days` gün içinde aynı kind/scope sınavda sorulmuş soru imzaları.
    Bunları yeni sınavdan elemek için kullan."""
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    conn = get_connection()
    if exam_scope:
        rows = conn.execute("""
            SELECT DISTINCT q.question_signature
            FROM exam_questions q
            JOIN exam_sessions s ON s.uuid = q.session_uuid
            WHERE s.exam_kind = ? AND s.exam_scope = ? AND q.asked_at >= ?
        """, (exam_kind, exam_scope, cutoff)).fetchall()
    else:
        rows = conn.execute("""
            SELECT DISTINCT q.question_signature
            FROM exam_questions q
            JOIN exam_sessions s ON s.uuid = q.session_uuid
            WHERE s.exam_kind = ? AND q.asked_at >= ?
        """, (exam_kind, cutoff)).fetchall()
    conn.close()
    return {r["question_signature"] for r in rows}


def get_exam_history(exam_kind=None, limit=20):
    conn = get_connection()
    if exam_kind:
        rows = conn.execute("""
            SELECT * FROM exam_sessions WHERE exam_kind = ? AND finished_at IS NOT NULL
            ORDER BY started_at DESC LIMIT ?
        """, (exam_kind, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM exam_sessions WHERE finished_at IS NOT NULL
            ORDER BY started_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def backup_db(dest_path):
    """Veritabanını yedekle."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(DB_PATH, dest_path)


def restore_db(src_path):
    """Yedekten veritabanını geri yükle."""
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Yedek dosyası bulunamadı: {src_path}")
    shutil.copy2(src_path, DB_PATH)
