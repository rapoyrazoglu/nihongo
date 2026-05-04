"""Adaptive mastery engine — Elo-style ranking for language items.

Saf algoritmik modul. Veritabanına bağımlı değildir; pure fonksiyonlar.
DB tarafı db.py'da, etkileşimler quiz.py / exam_*.py'da ELO hook'larıyla
bu modulu cagirir.

Model:
  Her ogenin (vocab/kanji/grammar item) bir "zorluk" rating'i var (R_item).
  Her kullanicinin ogeye ozel bir "ustalik" rating'i var (R_user_item).
  Cevap dogru ise R_user_item yukselir, R_item duser; tersi geçerli.
  K-factor (adim buyuklugu) review sayisina + confidence'a gore degisir.
  Yumusak time-decay: uzun sure dokunulmamış oge zayıflar (unutma).

Public API:
  expected_score(user_rating, item_rating)
  k_factor(reviews_count, confidence)
  update(user_rating, item_rating, correct, reviews_count, confidence=None)
      -> (new_user_rating, new_item_rating)
  decay(rating, days_since_review, half_life_days=30) -> new_rating
  master_threshold() / learning_threshold() (UI'da renklendirme icin)
"""

import math

INITIAL_RATING = 1400.0
MASTER_THRESHOLD = 1800.0     # >= 1800 master sayilir
LEARNING_THRESHOLD = 1500.0   # >= 1500 ogreniyor; alti yeni/zayif
ITEM_RATING_PULL = 0.30       # item rating, user delta'sinin bu kadarini ters yonde alir
SKILL_RATING_PULL = 0.20      # skill rating, user delta'sinin bu kadarini ayni yonde alir


def expected_score(user_rating, item_rating):
    """Klasik Elo beklenti formulu. 0..1 arasi 'kullanici bunu dogru bilme olasiligi'."""
    return 1.0 / (1.0 + math.pow(10.0, (item_rating - user_rating) / 400.0))


def k_factor(reviews_count, confidence=None):
    """Adim buyuklugu. Yeni oge -> hareket fazla; yerlesik -> az.

    confidence: 1=guess, 2=unsure, 3=knew, 4=easy. None = sorulmadi (default 3).
    """
    # Review sayisina gore base K
    if reviews_count < 3:
        base = 32
    elif reviews_count < 10:
        base = 24
    elif reviews_count < 25:
        base = 16
    else:
        base = 10

    # Confidence multiplier — kullanici "tahmin ettim" derse rating'i sallayalim,
    # "cok kolay" derse az hareket etsin (zaten biliyor).
    multipliers = {1: 1.5, 2: 1.2, 3: 1.0, 4: 0.7}
    mult = multipliers.get(confidence, 1.0)
    return base * mult


def update(user_rating, item_rating, correct, reviews_count, confidence=None):
    """Tek cevap sonrasi rating guncellemesi. Returns (new_user, new_item)."""
    expected = expected_score(user_rating, item_rating)
    score = 1.0 if correct else 0.0
    K = k_factor(reviews_count, confidence)
    delta = K * (score - expected)

    new_user = user_rating + delta
    # Item ters yonde, daha yumusak: dogru cevap → item kolaylasir
    new_item = item_rating - delta * ITEM_RATING_PULL

    # Klips — rating'lar uçmasın
    new_user = max(800.0, min(2800.0, new_user))
    new_item = max(800.0, min(2800.0, new_item))
    return new_user, new_item


def skill_delta(user_delta):
    """User-item rating degisiminin skill'e yansiyan kismi."""
    return user_delta * SKILL_RATING_PULL


def decay(rating, days_since_review, half_life_days=30):
    """Yumusak unutma: rating zamanla INITIAL_RATING'e dogru cekilir.
    half_life_days kadar dokunulmazsa ratingn farki yarıya iner.

    Sadece 7 gunden sonra etki etmeye baslar (immediate decay yok).
    """
    if days_since_review <= 7:
        return rating
    effective_days = days_since_review - 7
    # Exponential decay towards INITIAL
    factor = math.pow(0.5, effective_days / half_life_days)
    return INITIAL_RATING + (rating - INITIAL_RATING) * factor


def status_label(rating):
    """UI'da renk/etiket icin kategori. 'new'|'learning'|'mastered'."""
    if rating >= MASTER_THRESHOLD:
        return "mastered"
    if rating >= LEARNING_THRESHOLD:
        return "learning"
    return "new"


def select_priority(items_with_ratings, target_rating, days_since_map):
    """Item secimi. items_with_ratings: list of dict
        { 'id': int, 'rating': float, 'last_review_at': str|None }
    target_rating: kullanicinin skill rating'i. Hedef, +-100 etrafindaki ogeler.

    Sıralama:
      1) days_since > 14 olanlar onde (tekrar zamani)
      2) abs(rating - target) az olanlar onde (zorluk hedefte)
      3) yeni (rating yakın INITIAL) onde

    Returns sorted list (uygun siralı).
    """
    def score(item):
        days = days_since_map.get(item["id"], 999)
        diff = abs(item["rating"] - target_rating)
        # Lower score = higher priority
        review_urgency = max(0, 14 - days) * -1 if days > 14 else 0
        return (review_urgency, diff)
    return sorted(items_with_ratings, key=score)
