#!/usr/bin/env python3
"""tools/_drafts/Lxx.json -> src/data/genki1.json merge.

Her draft (gen_lesson_enrichment.py'nin urettigi dosya) ilgili lesson'a
'description', 'cultural_notes', 'dialogues', 'real_world_prompts' alanlarini
ekler. Var olan alanlar ezilir (idempotent).

Calistirma:
    python tools/merge_enrichment.py            # tum draft'lari merge et
    python tools/merge_enrichment.py --dry-run  # ne olacagini goster, yazma
    python tools/merge_enrichment.py 1 3 5      # sadece bu lesson no'lar
"""

import json
import os
import sys

# Windows UTF-8
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENKI_PATH = os.path.join(ROOT, "src", "data", "genki1.json")
DRAFTS_DIR = os.path.join(ROOT, "tools", "_drafts")

ENRICHMENT_KEYS = ("description", "cultural_notes", "dialogues", "real_world_prompts")


def load_draft(lesson_no):
    path = os.path.join(DRAFTS_DIR, f"L{lesson_no:02d}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    only = set(int(x) for x in args if x.isdigit()) or None

    with open(GENKI_PATH, encoding="utf-8") as f:
        book = json.load(f)

    merged = 0
    missing = []
    for lesson in book["lessons"]:
        n = lesson["lesson_no"]
        if only and n not in only:
            continue
        draft = load_draft(n)
        if not draft:
            missing.append(n)
            continue
        for k in ENRICHMENT_KEYS:
            if k in draft:
                lesson[k] = draft[k]
        merged += 1
        print(f"  L{n:>2} {lesson['title_en']:<28s}  merged "
              f"({len(draft.get('cultural_notes', []))} notes, "
              f"{len(draft.get('dialogues', []))} dialogues, "
              f"{len(draft.get('real_world_prompts', []))} prompts)")

    if missing:
        print(f"\nDraft yok: L{missing}")

    if dry_run:
        print(f"\n[DRY-RUN] {merged} lesson merge edilirdi. Yazılmadı.")
        return

    if merged > 0:
        with open(GENKI_PATH, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=2)
        print(f"\n{merged} lesson merge edildi -> {GENKI_PATH}")
    else:
        print("Merge edilecek bir sey yok.")


if __name__ == "__main__":
    main()
