"""Veritabanını oluştur ve başlangıç verilerini yükle."""

import json
import os
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import init_db, get_connection
from paths import DATA_DIR


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


VOCAB_FILES = [
    ("n5_vocab.json", "N5"), ("n4_vocab.json", "N4"), ("n3_vocab.json", "N3"),
    ("n2_vocab.json", "N2"), ("n1_vocab.json", "N1"),
]


def seed_vocabulary():
    conn = get_connection()

    for level_file, level in VOCAB_FILES:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            continue
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM vocabulary WHERE level = ?", (level,)
        ).fetchone()["cnt"]
        if count > 0:
            continue
        data = load_json(level_file)
        for item in data:
            conn.execute("""
                INSERT INTO vocabulary (word, reading, meaning_tr, meaning_en,
                    meaning_de, meaning_fr, meaning_es, meaning_pt, meaning_ko, meaning_zh,
                    level, example_jp, example_tr, part_of_speech)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["word"], item["reading"], item["meaning_tr"], item["meaning_en"],
                item.get("meaning_de", ""), item.get("meaning_fr", ""),
                item.get("meaning_es", ""), item.get("meaning_pt", ""),
                item.get("meaning_ko", ""), item.get("meaning_zh", ""),
                level, item.get("example_jp", ""), item.get("example_tr", ""),
                item.get("part_of_speech", "")
            ))
        print(f"  {level}: {len(data)} kelime yüklendi.")

    conn.commit()
    conn.close()


KANJI_FILES = [
    ("n5_kanji.json", "N5"), ("n4_kanji.json", "N4"), ("n3_kanji.json", "N3"),
    ("n2_kanji.json", "N2"), ("n1_kanji.json", "N1"),
]


def seed_kanji():
    conn = get_connection()

    for level_file, level in KANJI_FILES:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            continue
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM kanji WHERE level = ?", (level,)
        ).fetchone()["cnt"]
        if count > 0:
            continue
        data = load_json(level_file)
        for item in data:
            conn.execute("""
                INSERT OR IGNORE INTO kanji (kanji, on_yomi, kun_yomi, meaning_tr, meaning_en,
                    meaning_de, meaning_fr, meaning_es, meaning_pt, meaning_ko, meaning_zh,
                    level, stroke_count, compounds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["kanji"], item["on_yomi"], item["kun_yomi"],
                item["meaning_tr"], item["meaning_en"],
                item.get("meaning_de", ""), item.get("meaning_fr", ""),
                item.get("meaning_es", ""), item.get("meaning_pt", ""),
                item.get("meaning_ko", ""), item.get("meaning_zh", ""),
                level, item.get("stroke_count", 0), item.get("compounds", "")
            ))
        print(f"  {level}: {len(data)} kanji yüklendi.")

    conn.commit()
    conn.close()


def seed_grammar():
    conn = get_connection()
    before = conn.execute("SELECT COUNT(*) as cnt FROM grammar").fetchone()["cnt"]

    data = load_json("grammar.json")
    # Ek grammar dosyalarini da yukle
    for extra in ["grammar_n4_extra.json", "grammar_n3_extra.json"]:
        extra_path = os.path.join(DATA_DIR, extra)
        if os.path.exists(extra_path):
            with open(extra_path, "r", encoding="utf-8") as f:
                data.extend(json.load(f))

    for item in data:
        conn.execute("""
            INSERT OR IGNORE INTO grammar (pattern, meaning_tr, meaning_en,
                meaning_de, meaning_fr, meaning_es, meaning_pt, meaning_ko, meaning_zh,
                level, example_jp, example_tr, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["pattern"], item["meaning_tr"], item["meaning_en"],
            item.get("meaning_de", ""), item.get("meaning_fr", ""),
            item.get("meaning_es", ""), item.get("meaning_pt", ""),
            item.get("meaning_ko", ""), item.get("meaning_zh", ""),
            item["level"], item.get("example_jp", ""), item.get("example_tr", ""),
            item.get("notes", "")
        ))

    conn.commit()
    after = conn.execute("SELECT COUNT(*) as cnt FROM grammar").fetchone()["cnt"]
    added = after - before
    if added > 0:
        print(f"  Dilbilgisi: {added} yeni kural eklendi (toplam: {after}).")
    else:
        print(f"  Dilbilgisi: zaten güncel ({after} kural).")
    conn.close()


def migrate_extra_examples():
    """Mevcut vocabulary tablosuna extra_examples sutunu ekle."""
    conn = get_connection()
    try:
        conn.execute("ALTER TABLE vocabulary ADD COLUMN extra_examples TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # Column already exists
    conn.close()


def update_extra_examples():
    """JSON'daki extra_examples verilerini DB'ye yaz."""
    conn = get_connection()
    for level_file, level in VOCAB_FILES:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            continue
        data = load_json(level_file)
        for item in data:
            extras = item.get("extra_examples")
            if extras:
                conn.execute(
                    "UPDATE vocabulary SET extra_examples = ? WHERE word = ? AND level = ?",
                    (json.dumps(extras, ensure_ascii=False), item["word"], level)
                )
    conn.commit()
    conn.close()


def migrate_meanings():
    """Mevcut tablolara çoklu dil meaning sütunları ekle."""
    conn = get_connection()
    langs = ["de", "fr", "es", "pt", "ko", "zh"]
    for table in ["vocabulary", "kanji", "grammar"]:
        for lang in langs:
            col = f"meaning_{lang}"
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT ''")
            except Exception:
                pass
    conn.commit()
    conn.close()


def update_meanings():
    """JSON'daki çoklu dil meaning verilerini DB'ye yaz."""
    conn = get_connection()
    langs = ["de", "fr", "es", "pt", "ko", "zh"]

    # Vocabulary
    for level_file, level in VOCAB_FILES:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            continue
        data = load_json(level_file)
        for item in data:
            sets = []
            vals = []
            for lang in langs:
                key = f"meaning_{lang}"
                if item.get(key):
                    sets.append(f"{key} = ?")
                    vals.append(item[key])
            if sets:
                vals.extend([item["word"], level])
                conn.execute(
                    f"UPDATE vocabulary SET {', '.join(sets)} WHERE word = ? AND level = ?",
                    vals
                )

    # Kanji
    for level_file, level in KANJI_FILES:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            continue
        data = load_json(level_file)
        for item in data:
            sets = []
            vals = []
            for lang in langs:
                key = f"meaning_{lang}"
                if item.get(key):
                    sets.append(f"{key} = ?")
                    vals.append(item[key])
            if sets:
                vals.append(item["kanji"])
                conn.execute(
                    f"UPDATE kanji SET {', '.join(sets)} WHERE kanji = ?",
                    vals
                )

    # Grammar
    filepath = os.path.join(DATA_DIR, "grammar.json")
    if os.path.exists(filepath):
        data = load_json("grammar.json")
        for item in data:
            sets = []
            vals = []
            for lang in langs:
                key = f"meaning_{lang}"
                if item.get(key):
                    sets.append(f"{key} = ?")
                    vals.append(item[key])
            if sets:
                vals.append(item["pattern"])
                conn.execute(
                    f"UPDATE grammar SET {', '.join(sets)} WHERE pattern = ?",
                    vals
                )

    conn.commit()
    conn.close()


def migrate_grammar_unique():
    """Mevcut grammar tablosuna UNIQUE kısıtlaması ekle (yoksa)."""
    conn = get_connection()
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_grammar_pattern ON grammar(pattern)")
        conn.commit()
    except Exception:
        pass
    conn.close()


# --- Textbook (Genki) seeding ---

def _find_vocab_id(conn, key):
    """key word veya reading olabilir; eşleşen vocab id'sini döner."""
    row = conn.execute(
        "SELECT id FROM vocabulary WHERE word = ? OR reading = ? LIMIT 1",
        (key, key)
    ).fetchone()
    return row["id"] if row else None


def _find_grammar_id(conn, pattern):
    row = conn.execute(
        "SELECT id FROM grammar WHERE pattern = ? LIMIT 1", (pattern,)
    ).fetchone()
    return row["id"] if row else None


def _find_kanji_id(conn, ch):
    row = conn.execute(
        "SELECT id FROM kanji WHERE kanji = ? LIMIT 1", (ch,)
    ).fetchone()
    return row["id"] if row else None


def _insert_inline_vocab(conn, item, level):
    conn.execute("""
        INSERT INTO vocabulary (word, reading, meaning_tr, meaning_en,
            meaning_de, meaning_fr, meaning_es, meaning_pt, meaning_ko, meaning_zh,
            level, example_jp, example_tr, part_of_speech)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["word"], item["reading"], item["meaning_tr"], item["meaning_en"],
        item.get("meaning_de", ""), item.get("meaning_fr", ""),
        item.get("meaning_es", ""), item.get("meaning_pt", ""),
        item.get("meaning_ko", ""), item.get("meaning_zh", ""),
        level, item.get("example_jp", ""), item.get("example_tr", ""),
        item.get("part_of_speech", "")
    ))
    return conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]


def _insert_inline_grammar(conn, item, level):
    conn.execute("""
        INSERT OR IGNORE INTO grammar (pattern, meaning_tr, meaning_en,
            meaning_de, meaning_fr, meaning_es, meaning_pt, meaning_ko, meaning_zh,
            level, example_jp, example_tr, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["pattern"], item["meaning_tr"], item["meaning_en"],
        item.get("meaning_de", ""), item.get("meaning_fr", ""),
        item.get("meaning_es", ""), item.get("meaning_pt", ""),
        item.get("meaning_ko", ""), item.get("meaning_zh", ""),
        item.get("level", level), item.get("example_jp", ""),
        item.get("example_tr", ""), item.get("notes", "")
    ))
    return _find_grammar_id(conn, item["pattern"])


def _link_lesson_item(conn, lesson_id, item_type, item_id, sort_order):
    if item_id is None:
        return
    conn.execute("""
        INSERT OR IGNORE INTO lesson_items (lesson_id, item_type, item_id, sort_order)
        VALUES (?, ?, ?, ?)
    """, (lesson_id, item_type, item_id, sort_order))


def seed_textbook(filename):
    """Genki gibi ders kitabı JSON'unu yükle.
    Tekrar çalıştırılabilir: zaten var olan dersler atlanır, item linkleri INSERT OR IGNORE.
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return

    book = load_json(filename)
    textbook = book["textbook"]
    level = book.get("level", "N5")

    conn = get_connection()
    linked_v = linked_g = linked_k = 0
    inserted_v = inserted_g = 0
    missing_v = missing_g = missing_k = 0

    for lesson in book.get("lessons", []):
        lesson_no = lesson["lesson_no"]
        title = lesson.get("title_en", f"Lesson {lesson_no}")
        title_ja = lesson.get("title_ja", "")

        conn.execute("""
            INSERT OR IGNORE INTO lessons (textbook, lesson_no, title, title_ja, level)
            VALUES (?, ?, ?, ?, ?)
        """, (textbook, lesson_no, title, title_ja, level))
        lesson_row = conn.execute(
            "SELECT id FROM lessons WHERE textbook = ? AND lesson_no = ?",
            (textbook, lesson_no)
        ).fetchone()
        lesson_id = lesson_row["id"]

        for i, entry in enumerate(lesson.get("vocab", [])):
            if isinstance(entry, str):
                vid = _find_vocab_id(conn, entry)
                if vid is None:
                    missing_v += 1
                    continue
            else:
                vid = _find_vocab_id(conn, entry["word"])
                if vid is None:
                    vid = _insert_inline_vocab(conn, entry, level)
                    inserted_v += 1
            _link_lesson_item(conn, lesson_id, "vocabulary", vid, i)
            linked_v += 1

        for i, entry in enumerate(lesson.get("grammar", [])):
            if isinstance(entry, str):
                gid = _find_grammar_id(conn, entry)
                if gid is None:
                    missing_g += 1
                    continue
            else:
                gid = _find_grammar_id(conn, entry["pattern"])
                if gid is None:
                    gid = _insert_inline_grammar(conn, entry, level)
                    inserted_g += 1
            _link_lesson_item(conn, lesson_id, "grammar", gid, i)
            linked_g += 1

        for i, ch in enumerate(lesson.get("kanji", [])):
            kid = _find_kanji_id(conn, ch) if isinstance(ch, str) else None
            if kid is None:
                missing_k += 1
                continue
            _link_lesson_item(conn, lesson_id, "kanji", kid, i)
            linked_k += 1

    conn.commit()
    conn.close()
    print(f"  {textbook}: {linked_v} vocab + {linked_g} grammar + {linked_k} kanji bağlandı "
          f"(yeni: {inserted_v}v/{inserted_g}g, eksik: {missing_v}v/{missing_g}g/{missing_k}k).")


def seed_genki1():
    seed_textbook("genki1.json")


def main():
    print("Veritabanı oluşturuluyor...")
    init_db()
    migrate_grammar_unique()
    print("Tablolar oluşturuldu.\n")

    print("Veriler yükleniyor...")
    seed_vocabulary()
    seed_kanji()
    seed_grammar()
    seed_genki1()
    print("\nVeritabanı hazır!")


if __name__ == "__main__":
    main()
