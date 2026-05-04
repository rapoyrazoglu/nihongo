#!/usr/bin/env python3
"""Diagnostic quiz authoring tool — Gemini ile her ders icin diagnostic
question pool uretir.

Diagnostic = her sorunun NEYI test ettigi acik (vocab / grammar / mixed).
Yanlis cevap -> sistem hangi skill'e zayifligi atfetmesi gerektigini bilir.

Cikti: tools/_drafts/Lxx_quiz.json — review sonra merge_diagnostic_quiz.py
ile genki1.json'a aktarilir.

Kullanim:
    GEMINI_API_KEY=AIza... python tools/gen_diagnostic_quiz.py 1 2 3
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENKI_PATH = os.path.join(ROOT, "src", "data", "genki1.json")
DRAFTS_DIR = os.path.join(ROOT, "tools", "_drafts")
MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def _api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("ERROR: Set GEMINI_API_KEY")
    return key


def _call_gemini(prompt, temperature=0.7, max_retries=8):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    url = f"{API_URL}?key={_api_key()}"
    last_err = None
    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                wait = min(60, 2 ** attempt + 1)
                print(f"    HTTP {e.code} — {wait}s sonra (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            wait = min(60, 2 ** attempt + 1)
            print(f"    {type(e).__name__}: {e} — {wait}s sonra")
            time.sleep(wait)
    raise last_err if last_err else RuntimeError("Tum denemeler basarisiz")


def _grammar_label(g):
    if isinstance(g, str):
        return g
    return f"{g['pattern']} ({g.get('meaning_tr', g.get('meaning_en', ''))})"


def _vocab_label(v):
    if isinstance(v, str):
        return v
    return f"{v['word']} ({v.get('reading','')}) = {v.get('meaning_tr', v.get('meaning_en',''))}"


_EXAMPLE_OUTPUT = {
    "questions": [
        {
            "id": "L1_q01",
            "type": "fill_in_blank_vocab",
            "prompt_jp": "私は ___ です。",
            "prompt_tr": "Bosluga 'ogrenci' anlamina gelen kelime nedir?",
            "tests": ["vocab"],
            "weights": {"vocab": 1.0},
            "correct": "学生",
            "distractors": [
                {"text": "先生", "diag": "vocab_confusion_ogretmen"},
                {"text": "医者", "diag": "vocab_confusion_doktor"},
                {"text": "会社員", "diag": "vocab_confusion_calisan"}
            ],
            "explanation_tr": "学生 (gakusei) 'ogrenci' demek. Diger secenekler de meslek/durum ama farkli anlamlar."
        },
        {
            "id": "L1_q02",
            "type": "sentence_assembly_grammar",
            "prompt_tr": "'Tanaka-san ogretmendir' nasil soylenir? (verilen kelimeler: 田中, 先生)",
            "tests": ["grammar"],
            "weights": {"grammar": 1.0},
            "correct": "田中さんは先生です。",
            "distractors": [
                {"text": "田中先生です。", "diag": "particle_は_eksik"},
                {"text": "田中さんは先生だ。", "diag": "register_casual_だ"},
                {"text": "田中さん先生はです。", "diag": "wrong_word_order"}
            ],
            "explanation_tr": "X は Y です. yapisi: konu + は + tanim + です."
        },
        {
            "id": "L1_q03",
            "type": "translate_mixed",
            "prompt_tr": "'Ben Japon degilim' Japonca'ya cevir.",
            "tests": ["vocab", "grammar"],
            "weights": {"vocab": 0.5, "grammar": 0.5},
            "correct": "私は日本人じゃないです。",
            "distractors": [
                {"text": "私は日本人です。", "diag": "vocab_olumsuzluk_eksik"},
                {"text": "私日本人じゃないです。", "diag": "grammar_は_eksik"},
                {"text": "私は中国人じゃないです。", "diag": "vocab_yanlis_ulke"}
            ],
            "explanation_tr": "じゃないです 'degil' ifadesi; X は Y じゃないです."
        }
    ]
}


def _build_prompt(lesson):
    grammar_lines = "\n".join(f"  - {_grammar_label(g)}" for g in lesson["grammar"][:8])
    vocab_lines = "\n".join(f"  - {_vocab_label(v)}" for v in lesson["vocab"][:30])

    return f"""GOREV: Asagidaki ders icin 12-15 adet diagnostic quiz sorusu URET.
"diagnostic" = her sorunun NEYI test ettigi acik olsun (vocab? grammar? mixed?).
Yanlis cevaptan sistem 'kelime mi gramer mi zayif?' anlayabilsin.

DERS: Genki I, Lesson {lesson['lesson_no']}: {lesson['title_en']}
Japonca: {lesson.get('title_ja', '')}

DERSIN GRAMMAR'I:
{grammar_lines}

DERSIN KELIMELERI:
{vocab_lines}

SORU TIPLERI (mutlaka KARISIK kullan):
1) fill_in_blank_vocab — Tam dogru gramerli cumle, sadece kelime bosluk.
   tests=["vocab"]. Distractor'lar ayni POS, yanlis anlam.
2) sentence_assembly_grammar — Verilen kelime + Turkce mana, dogru gramerli
   cumleyi bulmak. tests=["grammar"]. Distractor'lar gramer hatasi
   (eksik particle, casual register, yanlis sira).
3) translate_mixed — Turkce cumle -> Japonca cevirisi. tests=["vocab","grammar"].
4) kanji_reading — varsa, kanji okuma sorusu. tests=["kanji"].

DAGILIM (zorunlu):
  - 5-6 fill_in_blank_vocab
  - 4 sentence_assembly_grammar
  - 2-3 translate_mixed
  - eger ders kanji iceriyorsa 1-2 kanji_reading

OUTPUT: SADECE asagidaki sablona bire bir uyan TEK JSON OBJECT (markdown YOK,
aciklama YOK, sadece raw JSON):

{json.dumps(_EXAMPLE_OUTPUT, ensure_ascii=False, indent=2)}

KURALLAR:
- Distractor'lar gercekci yanlislari yansitsin (random olmasin).
- "diag" field'i kisa etiket: vocab_confusion, particle_eksik, register_casual,
  wrong_pos, wrong_word_order vb.
- explanation_tr 1 cumle, neden dogru oldugunu Turkce anlatsin.
- Tum Japonca dogru hiragana/kanji ile.
- Bu dersin disindaki grammar kullanma.
- id format: L{lesson['lesson_no']}_qNN."""


def generate_for_lesson(lesson):
    print(f"  L{lesson['lesson_no']} {lesson['title_en']:30s} -> Gemini")
    prompt = _build_prompt(lesson)
    try:
        result = _call_gemini(prompt)
    except Exception as e:
        print(f"    HATA: {e}")
        return None
    if "questions" not in result:
        print(f"    UYARI: 'questions' anahtari yok; gelen alanlar: {list(result.keys())}")
        return None
    print(f"    {len(result['questions'])} soru uretildi")
    return result


def main():
    args = sys.argv[1:]
    only = set(int(x) for x in args if x.isdigit()) if args else None

    with open(GENKI_PATH, encoding="utf-8") as f:
        book = json.load(f)

    os.makedirs(DRAFTS_DIR, exist_ok=True)
    for lesson in book["lessons"]:
        n = lesson["lesson_no"]
        if only and n not in only:
            continue
        out_path = os.path.join(DRAFTS_DIR, f"L{n:02d}_quiz.json")
        if os.path.exists(out_path):
            print(f"  L{n} -> already drafted, skipping")
            continue
        result = generate_for_lesson(lesson)
        if result is None:
            continue
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)
        print(f"    yazildi: {out_path}")
        time.sleep(2)
    print(f"\nDONE. Draft'lar: {DRAFTS_DIR}")


if __name__ == "__main__":
    main()
