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


def main():
    print("Veritabanı oluşturuluyor...")
    init_db()
    migrate_grammar_unique()
    print("Tablolar oluşturuldu.\n")

    print("Veriler yükleniyor...")
    seed_vocabulary()
    seed_kanji()
    seed_grammar()
    print("\nVeritabanı hazır!")


if __name__ == "__main__":
    main()
