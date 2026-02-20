"""Japonca fiil çekim motoru.

3 grup:
  - ichidan (一段): ~える/~いる son eki düşür + form eki
  - godan (五段): son hece değişir (u-satırı → a/i/e satırı)
  - irregular: する→します, くる→きます
"""


# Godan fiil: son karakter → satır dönüşümleri
_GODAN_MAP = {
    # dict → a-dan, i-dan, e-dan, te-form, ta-form
    "う": ("わ", "い", "え", "って", "った"),
    "く": ("か", "き", "け", "いて", "いた"),
    "ぐ": ("が", "ぎ", "げ", "いで", "いだ"),
    "す": ("さ", "し", "せ", "して", "した"),
    "つ": ("た", "ち", "て", "って", "った"),
    "ぬ": ("な", "に", "ね", "んで", "んだ"),
    "ぶ": ("ば", "び", "べ", "んで", "んだ"),
    "む": ("ま", "み", "め", "んで", "んだ"),
    "る": ("ら", "り", "れ", "って", "った"),
}

# 行く は特殊: いって/いった
_SPECIAL_GODAN = {
    "いく": {"te": "いって", "ta": "いった"},
    "行く": {"te": "行って", "ta": "行った"},
}

# Ichidan olduğu bilinen yaygın fiiller (godan ~える/~いる ile karışmaması için)
_ICHIDAN_ENDINGS = [
    "える", "いる",
]

# Godan olmasına rağmen ~える/~いる ile biten fiiller
_GODAN_EXCEPTIONS = {
    "帰る", "入る", "走る", "知る", "切る", "要る", "参る", "散る",
    "しゃべる", "焦る", "限る", "握る", "練る", "蹴る", "滑る",
    "かえる", "はいる", "はしる", "しる", "きる", "いる",
}


def _is_ichidan(word, reading):
    """Fiil ichidan mı?"""
    # する/くる irregular
    if reading in ("する", "くる") or word in ("する", "来る"):
        return False
    # Godan exception listesi
    if word in _GODAN_EXCEPTIONS or reading in _GODAN_EXCEPTIONS:
        return False
    # ~える veya ~いる ile bitiyorsa ichidan
    if reading.endswith("える") or reading.endswith("いる"):
        return True
    if reading.endswith("る") and len(reading) >= 2:
        prev = reading[-2]
        if prev in "えいけせてねべめれげぜでぺ":
            return True
    return False


def _is_irregular(word, reading):
    """する veya くる mu?"""
    if reading == "する" or word == "する":
        return "suru"
    if reading == "くる" or word == "来る":
        return "kuru"
    if reading.endswith("する") or word.endswith("する"):
        return "suru_compound"
    if reading.endswith("くる") or word.endswith("来る"):
        return "kuru_compound"
    return None


def conjugate(word, reading, form):
    """Fiili çekimle.

    form: 'masu', 'nai', 'te', 'ta', 'dict' (sözlük formu)

    Returns: çekimlenmiş hali (reading bazlı)
    """
    if form == "dict":
        return reading

    irr = _is_irregular(word, reading)
    if irr:
        return _conjugate_irregular(reading, form, irr)

    if _is_ichidan(word, reading):
        return _conjugate_ichidan(reading, form)
    else:
        return _conjugate_godan(reading, form)


def _conjugate_ichidan(reading, form):
    """Ichidan fiil çekimi: stem = reading[:-1]"""
    stem = reading[:-1]  # る'yu düşür
    if form == "masu":
        return stem + "ます"
    elif form == "nai":
        return stem + "ない"
    elif form == "te":
        return stem + "て"
    elif form == "ta":
        return stem + "た"
    return reading


def _conjugate_godan(reading, form):
    """Godan fiil çekimi."""
    if not reading:
        return reading

    last = reading[-1]
    stem = reading[:-1]

    # Özel durum: 行く
    if reading in _SPECIAL_GODAN:
        spec = _SPECIAL_GODAN[reading]
        if form == "te" and "te" in spec:
            return spec["te"]
        elif form == "ta" and "ta" in spec:
            return spec["ta"]

    if last not in _GODAN_MAP:
        return reading

    a_dan, i_dan, e_dan, te_form, ta_form = _GODAN_MAP[last]

    if form == "masu":
        return stem + i_dan + "ます"
    elif form == "nai":
        if last == "う":
            return stem + "わない"
        return stem + a_dan + "ない"
    elif form == "te":
        return stem + te_form
    elif form == "ta":
        return stem + ta_form
    return reading


def _conjugate_irregular(reading, form, irr_type):
    """Düzensiz fiil çekimi."""
    if irr_type == "suru":
        if form == "masu":
            return "します"
        elif form == "nai":
            return "しない"
        elif form == "te":
            return "して"
        elif form == "ta":
            return "した"
        return reading
    elif irr_type == "kuru":
        if form == "masu":
            return "きます"
        elif form == "nai":
            return "こない"
        elif form == "te":
            return "きて"
        elif form == "ta":
            return "きた"
        return reading
    elif irr_type == "suru_compound":
        prefix = reading[:-2]  # ~する'yu çıkar
        if form == "masu":
            return prefix + "します"
        elif form == "nai":
            return prefix + "しない"
        elif form == "te":
            return prefix + "して"
        elif form == "ta":
            return prefix + "した"
        return reading
    elif irr_type == "kuru_compound":
        prefix = reading[:-2]
        if form == "masu":
            return prefix + "きます"
        elif form == "nai":
            return prefix + "こない"
        elif form == "te":
            return prefix + "きて"
        elif form == "ta":
            return prefix + "きた"
        return reading
    return reading


# Form adları (quiz'de gösterilecek)
FORM_NAMES = {
    "masu": ("ます形", "masu form"),
    "nai": ("ない形", "nai form"),
    "te": ("て形", "te form"),
    "ta": ("た形", "ta form"),
}

FORMS = ["masu", "nai", "te", "ta"]
