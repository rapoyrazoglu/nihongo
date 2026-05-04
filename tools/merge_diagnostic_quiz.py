#!/usr/bin/env python3
"""tools/_drafts/Lxx_quiz.json -> src/data/genki1.json: lesson.quiz_pool ekler.

Idempotent: var olan quiz_pool ezilir.
"""
import json
import os
import sys

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENKI_PATH = os.path.join(ROOT, "src", "data", "genki1.json")
DRAFTS_DIR = os.path.join(ROOT, "tools", "_drafts")


def main():
    args = sys.argv[1:]
    only = set(int(x) for x in args if x.isdigit()) if args else None

    with open(GENKI_PATH, encoding="utf-8") as f:
        book = json.load(f)

    merged = 0
    missing = []
    for lesson in book["lessons"]:
        n = lesson["lesson_no"]
        if only and n not in only:
            continue
        path = os.path.join(DRAFTS_DIR, f"L{n:02d}_quiz.json")
        if not os.path.exists(path):
            missing.append(n)
            continue
        with open(path, encoding="utf-8") as f:
            draft = json.load(f)
        if "questions" not in draft:
            print(f"  L{n} -> skip (no 'questions' key)")
            continue
        lesson["quiz_pool"] = draft["questions"]
        merged += 1
        type_count = {}
        for q in draft["questions"]:
            type_count[q["type"]] = type_count.get(q["type"], 0) + 1
        print(f"  L{n:>2} {lesson['title_en']:<28s} {len(draft['questions'])} sorular  {type_count}")

    if missing:
        print(f"\nDraft yok: L{missing}")
    if merged > 0:
        with open(GENKI_PATH, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=2)
        print(f"\n{merged} lesson quiz_pool eklendi.")


if __name__ == "__main__":
    main()
