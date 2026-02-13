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
    if _current_lang == "tr":
        return "meaning_tr"
    return "meaning_en"


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
