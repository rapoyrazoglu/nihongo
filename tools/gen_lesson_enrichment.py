#!/usr/bin/env python3
"""Authoring tool — Gemini ile Genki I derslerine zenginleştirme üretir.

Bu script GELIŞTIRICI TARAFIDIR — son kullanıcı çalıştırmaz. Çıktı `tools/_drafts/`
klasörüne yazılır (gitignored), insan inceler, sonra `genki1.json`'a merge edilir.

Kullanım:
    GEMINI_API_KEY=AIza... python tools/gen_lesson_enrichment.py            # tüm dersler
    GEMINI_API_KEY=AIza... python tools/gen_lesson_enrichment.py 1 2 3      # sadece L1-3
    GEMINI_API_KEY=AIza... python tools/gen_lesson_enrichment.py --review   # üretilmişleri yazdır

Üretilen alanlar (her ders için):
  description           — kısa intro paragrafı (yazılabilir; "bu derste şunu öğreneceksin")
  cultural_notes        — 2-3 kültürel/pragmatik not
  dialogues             — 2-3 gerçek hayat diyaloğu (satır satır JP+TR+context)
  real_world_prompts    — 3-5 actionable "şunu yap, şunu söyle" görevi

Anahtar:
  GEMINI_API_KEY env var'dan okunur. Asla dosyaya yazılmaz, asla commit edilmez.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

# Windows: UTF-8 stdout (Türkçe karakter cp1252'de crash etmesin)
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
        sys.exit("ERROR: Set GEMINI_API_KEY environment variable.")
    return key


def _call_gemini(prompt, temperature=0.7, max_retries=8):
    """Gemini'ye sorgu, JSON-only modda. 503/429 için exponential backoff (max 60s)."""
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
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except urllib.error.HTTPError as e:
            last_err = e
            # 5xx + 429 retry
            if e.code in (429, 500, 502, 503, 504):
                wait = min(60, 2 ** attempt + 1)  # 2, 3, 5, 9, 17, 33, 60, 60
                print(f"    HTTP {e.code} — {wait}s sonra tekrar deniyorum (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            wait = min(60, 2 ** attempt + 1)
            print(f"    {type(e).__name__}: {e} — {wait}s sonra tekrar")
            time.sleep(wait)
    raise last_err if last_err else RuntimeError("Tüm denemeler başarısız")


def _grammar_label(g):
    if isinstance(g, str):
        return g
    return f"{g['pattern']}: {g.get('meaning_tr', g.get('meaning_en', ''))}"


def _vocab_label(v):
    if isinstance(v, str):
        return v
    return v["word"]


def _build_prompt(lesson):
    """Türkçe-keyed JSON formatında prompt — AI yapılandırılmış input'u
    daha iyi anlıyor (görsel prompt formatına benzer yaklaşım)."""
    spec = {
        "gorev": "japonca_ders_zenginlestirme_uret",
        "ders": {
            "kitap": "Genki I",
            "ders_no": lesson["lesson_no"],
            "ingilizce_baslik": lesson["title_en"],
            "japonca_baslik": lesson.get("title_ja", ""),
            "turkce_baslik": lesson.get("title_tr", ""),
        },
        "ders_grameri": [_grammar_label(g) for g in lesson["grammar"][:8]],
        "ders_kelimeleri_ornegi": [_vocab_label(v) for v in lesson["vocab"][:25]],
        "kullanici": {
            "ana_dil": "tr",
            "hedef_dil": "ja",
            "seviye": "JLPT_N5_baslangic",
            "ton": "samimi_arkadasca_sen_dili"
        },
        "uretilecek_alanlar": {
            "description": {
                "tip": "string",
                "uzunluk": "2-3 cumle",
                "icerik": "bu derste neyi ogrenecek, neden onemli, gunluk hayatta nerede ise yarayacak"
            },
            "cultural_notes": {
                "tip": "array",
                "min": 2, "max": 3,
                "her_eleman": {
                    "topic": "kisa baslik (TR)",
                    "text": "1-2 cumle, Japon kulturu/pragmatigi/etiketi"
                }
            },
            "dialogues": {
                "tip": "array",
                "min": 2, "max": 3,
                "her_eleman": {
                    "context": "diyalogun nerede ve neden gectigi (TR, 1 cumle)",
                    "lines": {
                        "tip": "array",
                        "min_satir": 3, "max_satir": 5,
                        "her_satir": {
                            "speaker": "A veya B",
                            "jp": "japonca cumle (hiragana+kanji dogru, dersin gramerini kullan)",
                            "tr": "turkce cevirisi"
                        }
                    },
                    "highlights": "bu diyalogdaki dersin grammar patternleri 2-3 adet"
                }
            },
            "real_world_prompts": {
                "tip": "array",
                "min": 3, "max": 5,
                "her_eleman": "somut yapilabilir gorev — ornek: 'Bir restorana git, menuye bakarak これをください de.'"
            }
        },
        "kurallar": [
            "Diyaloglar BU dersin grammar/vocab'ini kullansin; onceki derslerden yapı kullanmak OK ama bu dersinki domine etmeli.",
            "Hiragana/kanji dogru olsun; ornek karisik (okuyan kanji bilen icin, parantez icinde bilmeyen icin reading verme).",
            "Turkce dogal, samimi, sen dili.",
            "Cikti SADECE JSON OBJECT olsun — markdown, kod blogu, aciklama YOK.",
            "Cift tirnak, Unicode escape'siz.",
            "Tum stringler JSON-uyumlu kacis karakterlerinden temizlensin."
        ],
        "kacin": [
            "google_translate_kokulu_cumle",
            "asiri_resmi_dil",
            "yariciplak_diyalog_anlam_yok",
            "alakasiz_kulturel_jargon",
            "ders_grameri_disinda_yapi_kullanma",
            "her_diyalogda_ayni_kalip"
        ],
        "cikti_format": "tek_json_object_uretilecek_alanlar_seviyesinde"
    }
    instruction = (
        "Sen Turk ogrenciler icin Japonca ogretmenisin. "
        "Asagidaki spec'e gore TEK BIR JSON OBJECT uret. "
        "Cevap markdown olmasin, sadece raw JSON dondur:\n\n"
        + json.dumps(spec, ensure_ascii=False, indent=2)
    )
    return instruction


def generate_for_lesson(lesson):
    print(f"  L{lesson['lesson_no']} {lesson['title_en']:30s} -> Gemini'ye gidiyor...")
    prompt = _build_prompt(lesson)
    try:
        result = _call_gemini(prompt)
    except Exception as e:
        print(f"    HATA: {e}")
        return None
    # Sanity check
    needed = ["description", "cultural_notes", "dialogues", "real_world_prompts"]
    missing = [k for k in needed if k not in result]
    if missing:
        print(f"    UYARI: eksik anahtar: {missing}")
    return result


def main():
    args = sys.argv[1:]
    if "--review" in args:
        # Üretilen draft'ları okutsun
        for f in sorted(os.listdir(DRAFTS_DIR)):
            if f.startswith("L") and f.endswith(".json"):
                print(f"\n=== {f} ===")
                with open(os.path.join(DRAFTS_DIR, f), encoding="utf-8") as fp:
                    print(fp.read())
        return

    only = set(int(x) for x in args if x.isdigit()) if args else None

    with open(GENKI_PATH, encoding="utf-8") as f:
        book = json.load(f)

    os.makedirs(DRAFTS_DIR, exist_ok=True)

    for lesson in book["lessons"]:
        n = lesson["lesson_no"]
        if only and n not in only:
            continue
        out_path = os.path.join(DRAFTS_DIR, f"L{n:02d}.json")
        if os.path.exists(out_path):
            print(f"  L{n} -> already drafted, skipping ({out_path})")
            continue
        result = generate_for_lesson(lesson)
        if result is None:
            continue
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)
        print(f"    yazildi: {out_path}")
        time.sleep(1.5)  # rate limit'i hafif tut

    print(f"\nDONE. Draft'lar: {DRAFTS_DIR}")
    print("Inceledikten sonra `tools/merge_enrichment.py` ile genki1.json'a aktar (yarın yazılacak).")


if __name__ == "__main__":
    main()
