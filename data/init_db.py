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


def seed_vocabulary():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as cnt FROM vocabulary").fetchone()["cnt"]
    if count > 0:
        print(f"  Kelime tablosu zaten dolu ({count} kayıt), atlanıyor.")
        conn.close()
        return

    for level_file, level in [("n5_vocab.json", "N5"), ("n4_vocab.json", "N4")]:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            print(f"  {level_file} bulunamadı, atlanıyor.")
            continue
        data = load_json(level_file)
        for item in data:
            conn.execute("""
                INSERT INTO vocabulary (word, reading, meaning_tr, meaning_en, level, example_jp, example_tr, part_of_speech)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["word"], item["reading"], item["meaning_tr"], item["meaning_en"],
                level, item.get("example_jp", ""), item.get("example_tr", ""),
                item.get("part_of_speech", "")
            ))
        print(f"  {level}: {len(data)} kelime yüklendi.")

    conn.commit()
    conn.close()


def seed_kanji():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as cnt FROM kanji").fetchone()["cnt"]
    if count > 0:
        print(f"  Kanji tablosu zaten dolu ({count} kayıt), atlanıyor.")
        conn.close()
        return

    for level_file, level in [("n5_kanji.json", "N5"), ("n4_kanji.json", "N4")]:
        filepath = os.path.join(DATA_DIR, level_file)
        if not os.path.exists(filepath):
            print(f"  {level_file} bulunamadı, atlanıyor.")
            continue
        data = load_json(level_file)
        for item in data:
            conn.execute("""
                INSERT OR IGNORE INTO kanji (kanji, on_yomi, kun_yomi, meaning_tr, meaning_en, level, stroke_count, compounds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["kanji"], item["on_yomi"], item["kun_yomi"],
                item["meaning_tr"], item["meaning_en"], level,
                item.get("stroke_count", 0), item.get("compounds", "")
            ))
        print(f"  {level}: {len(data)} kanji yüklendi.")

    conn.commit()
    conn.close()


def seed_grammar():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as cnt FROM grammar").fetchone()["cnt"]
    if count > 0:
        print(f"  Dilbilgisi tablosu zaten dolu ({count} kayıt), atlanıyor.")
        conn.close()
        return

    data = load_json("grammar.json")
    for item in data:
        conn.execute("""
            INSERT INTO grammar (pattern, meaning_tr, meaning_en, level, example_jp, example_tr, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["pattern"], item["meaning_tr"], item["meaning_en"],
            item["level"], item.get("example_jp", ""), item.get("example_tr", ""),
            item.get("notes", "")
        ))
    print(f"  Dilbilgisi: {len(data)} kural yüklendi.")

    conn.commit()
    conn.close()


def main():
    print("Veritabanı oluşturuluyor...")
    init_db()
    print("Tablolar oluşturuldu.\n")

    print("Veriler yükleniyor...")
    seed_vocabulary()
    seed_kanji()
    seed_grammar()
    print("\nVeritabanı hazır!")


if __name__ == "__main__":
    main()
