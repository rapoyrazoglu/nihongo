"""Internationalization (i18n) engine for Nihongo Master."""

import json
import locale
import os

from paths import CONFIG_PATH, _BASE_DIR

LANGUAGES = {
    "tr": "Turkce",
    "en": "English",
    "de": "Deutsch",
    "fr": "Francais",
    "es": "Espanol",
    "pt": "Portugues",
    "ko": "Korean",
    "zh": "Chinese",
}

_current_lang = "en"
_strings = {}
_fallback = {}

_LANG_DIR = os.path.join(_BASE_DIR, "lang")


def _load_json(lang):
    path = os.path.join(_LANG_DIR, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load(lang):
    global _current_lang, _strings, _fallback
    _current_lang = lang
    _strings = _load_json(lang)
    if lang != "en":
        _fallback = _load_json("en")
    else:
        _fallback = {}


def t(key, **kwargs):
    val = _strings.get(key) or _fallback.get(key) or key
    if kwargs:
        val = val.format(**kwargs)
    return val


def meaning_field():
    mapping = {
        "tr": "meaning_tr",
        "en": "meaning_en",
        "de": "meaning_de",
        "fr": "meaning_fr",
        "es": "meaning_es",
        "pt": "meaning_pt",
        "ko": "meaning_ko",
        "zh": "meaning_zh",
    }
    return mapping.get(_current_lang, "meaning_en")


_POS_MAP = {
    "tr": {
        "isim": "isim", "fiil": "fiil", "sıfat": "sıfat", "na-sıfat": "na-sıfat",
        "zarf": "zarf", "zamir": "zamir", "sayaç": "sayaç", "bağlaç": "bağlaç",
        "ünlem": "ünlem", "動詞": "fiil", "名詞": "isim",
        "い形容詞": "i-sıfat", "な形容詞": "na-sıfat", "副詞": "zarf",
    },
    "en": {
        "isim": "noun", "fiil": "verb", "sıfat": "i-adjective", "na-sıfat": "na-adjective",
        "zarf": "adverb", "zamir": "pronoun", "sayaç": "counter", "bağlaç": "conjunction",
        "ünlem": "interjection", "動詞": "verb", "名詞": "noun",
        "い形容詞": "i-adjective", "な形容詞": "na-adjective", "副詞": "adverb",
    },
    "de": {
        "isim": "Nomen", "fiil": "Verb", "sıfat": "i-Adjektiv", "na-sıfat": "na-Adjektiv",
        "zarf": "Adverb", "zamir": "Pronomen", "sayaç": "Zähler", "bağlaç": "Konjunktion",
        "ünlem": "Interjektion", "動詞": "Verb", "名詞": "Nomen",
        "い形容詞": "i-Adjektiv", "な形容詞": "na-Adjektiv", "副詞": "Adverb",
    },
    "fr": {
        "isim": "nom", "fiil": "verbe", "sıfat": "adjectif-i", "na-sıfat": "adjectif-na",
        "zarf": "adverbe", "zamir": "pronom", "sayaç": "compteur", "bağlaç": "conjonction",
        "ünlem": "interjection", "動詞": "verbe", "名詞": "nom",
        "い形容詞": "adjectif-i", "な形容詞": "adjectif-na", "副詞": "adverbe",
    },
    "es": {
        "isim": "sustantivo", "fiil": "verbo", "sıfat": "adjetivo-i", "na-sıfat": "adjetivo-na",
        "zarf": "adverbio", "zamir": "pronombre", "sayaç": "contador", "bağlaç": "conjunción",
        "ünlem": "interjección", "動詞": "verbo", "名詞": "sustantivo",
        "い形容詞": "adjetivo-i", "な形容詞": "adjetivo-na", "副詞": "adverbio",
    },
    "pt": {
        "isim": "substantivo", "fiil": "verbo", "sıfat": "adjetivo-i", "na-sıfat": "adjetivo-na",
        "zarf": "advérbio", "zamir": "pronome", "sayaç": "contador", "bağlaç": "conjunção",
        "ünlem": "interjeição", "動詞": "verbo", "名詞": "substantivo",
        "い形容詞": "adjetivo-i", "な形容詞": "adjetivo-na", "副詞": "advérbio",
    },
    "ko": {
        "isim": "명사", "fiil": "동사", "sıfat": "い형용사", "na-sıfat": "な형용사",
        "zarf": "부사", "zamir": "대명사", "sayaç": "조수사", "bağlaç": "접속사",
        "ünlem": "감탄사", "動詞": "동사", "名詞": "명사",
        "い形容詞": "い형용사", "な形容詞": "な형용사", "副詞": "부사",
    },
    "zh": {
        "isim": "名词", "fiil": "动词", "sıfat": "い形容词", "na-sıfat": "な形容词",
        "zarf": "副词", "zamir": "代词", "sayaç": "量词", "bağlaç": "连词",
        "ünlem": "感叹词", "動詞": "动词", "名詞": "名词",
        "い形容詞": "い形容词", "な形容詞": "な形容词", "副詞": "副词",
    },
}


def translate_pos(pos):
    """Translate part of speech to current language."""
    if not pos:
        return pos
    mapping = _POS_MAP.get(_current_lang, _POS_MAP["en"])
    return mapping.get(pos, pos)


def get_lang():
    return _current_lang


def set_lang(lang):
    load(lang)
    _save_config(lang)


def _save_config(lang):
    config = _load_config()
    config["language"] = lang
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _detect_system_lang():
    """Detect system language from locale, return matching code or 'en'."""
    try:
        loc = locale.getdefaultlocale()[0] or ""
    except ValueError:
        loc = ""
    code = loc.split("_")[0].lower()
    if code in LANGUAGES:
        return code
    return "en"


def init():
    config = _load_config()
    lang = config.get("language")
    if lang and lang in LANGUAGES:
        load(lang)
        return True
    # No config yet — use system language as default
    sys_lang = _detect_system_lang()
    load(sys_lang)
    return False
