"""SM-2 Spaced Repetition Algoritması.

SuperMemo 2 algoritması ile akıllı tekrar zamanlaması.
Kalite (quality) 0-5 arası:
  0 - Hiç hatırlamadım
  1 - Yanlış, ama doğruyu görünce tanıdım
  2 - Yanlış, ama doğruyu biliyordum
  3 - Doğru, ama çok zorlandım
  4 - Doğru, biraz düşündüm
  5 - Doğru, hemen bildim
"""

from datetime import date, timedelta
from db import get_review, upsert_review


def sm2(quality, repetitions, ease_factor, interval):
    """SM-2 algoritmasını uygula.

    Args:
        quality: 0-5 arası kalite puanı
        repetitions: mevcut tekrar sayısı
        ease_factor: mevcut kolaylık faktörü (≥1.3)
        interval: mevcut tekrar aralığı (gün)

    Returns:
        (new_repetitions, new_ease_factor, new_interval)
    """
    if quality < 0 or quality > 5:
        raise ValueError("Kalite puanı 0-5 arası olmalı")

    if quality >= 3:
        # Doğru cevap
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
        new_repetitions = repetitions + 1
    else:
        # Yanlış cevap - başa dön
        new_repetitions = 0
        new_interval = 1

    # Kolaylık faktörünü güncelle
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3

    return new_repetitions, round(new_ease_factor, 2), new_interval


def review_card(card_type, card_id, quality, weak_kanji=None):
    """Bir kartı tekrarla ve SRS bilgilerini güncelle.

    Args:
        card_type: 'vocabulary', 'kanji', veya 'grammar'
        card_id: kartın veritabanı ID'si
        quality: 0-5 arası kalite puanı
        weak_kanji: None=değiştirme, 0=kanji biliniyor, 1=kanji bilinmiyor

    Returns:
        (new_interval, next_review_date)
    """
    existing = get_review(card_type, card_id)

    if existing:
        repetitions = existing["repetitions"]
        ease_factor = existing["ease_factor"]
        interval = existing["interval"]
    else:
        repetitions = 0
        ease_factor = 2.5
        interval = 0

    new_reps, new_ef, new_interval = sm2(quality, repetitions, ease_factor, interval)

    # weak_kanji: okumayı biliyor ama kanjiyi bilmiyor → max 3 gün aralık
    if weak_kanji == 1 and new_interval > 3:
        new_interval = 3

    next_review = (date.today() + timedelta(days=new_interval)).isoformat()

    upsert_review(card_type, card_id, new_ef, new_interval, new_reps, next_review, weak_kanji=weak_kanji)

    return new_interval, next_review


def quality_from_answer(correct, difficulty="normal"):
    """Cevap doğruluğu ve zorluğa göre kalite puanı döndür.

    Args:
        correct: True/False
        difficulty: 'easy', 'normal', 'hard'

    Returns:
        0-5 arası kalite puanı
    """
    if correct:
        if difficulty == "easy":
            return 5
        elif difficulty == "normal":
            return 4
        else:
            return 3
    else:
        if difficulty == "hard":
            return 0
        elif difficulty == "normal":
            return 1
        else:
            return 2
