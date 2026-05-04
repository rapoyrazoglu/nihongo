"""Curriculum / resume engine.

Tek sorumluluk: kullanicinin Genki mufredatinda nerede oldugunu hesaplamak ve
"sirada ne var" sorusunu cevaplamak. CLI/UI'dan bagimsiz; ileride SDK olarak
ayni API'yi mobil/desktop GUI'ye sunmayi hedefler.

Public API (stable):
    get_resume_state(level: str) -> ResumeState
    is_phase_complete(lesson_id, phase) -> bool
    is_lesson_complete(lesson_id) -> bool
    is_curriculum_complete(level) -> bool
    advance_phase(state) -> ResumeState  (next phase pointer)

PASS_THRESHOLD: bir lesson exam'inin "gecmis" sayilmasi icin gereken minimum
yuzde. JLPT 60% genel kabul; ayni esik burada da kullanilir.
"""

import db

PHASES = ("vocab", "grammar", "kanji", "exam")
PASS_THRESHOLD = 0.60


def _phase_items(lesson_id, phase):
    """Phase icin ilgili lesson item'lari (vocabulary/grammar/kanji) doner."""
    items = db.get_lesson_items(lesson_id)
    if phase == "vocab":
        return items["vocabulary"]
    if phase == "grammar":
        return items["grammar"]
    if phase == "kanji":
        return items["kanji"]
    return []


def _phase_progress(lesson_id, phase):
    """Bir asamanin {learned, total} ilerlemesi.
    learned = reviews.repetitions >= 1 olan ogeler."""
    items = _phase_items(lesson_id, phase)
    total = len(items)
    if total == 0:
        return {"learned": 0, "total": 0}

    item_type = {"vocab": "vocabulary", "grammar": "grammar", "kanji": "kanji"}[phase]
    ids = [i["id"] for i in items]

    conn = db.get_connection()
    placeholders = ",".join("?" * len(ids))
    row = conn.execute(f"""
        SELECT COUNT(*) as c FROM reviews
        WHERE card_type = ? AND card_id IN ({placeholders}) AND repetitions >= 1
    """, [item_type] + ids).fetchone()
    conn.close()
    return {"learned": row["c"], "total": total}


def is_phase_complete(lesson_id, phase):
    """Asama tamamlandi mi?
    vocab/grammar/kanji: tum ogeler en az 1 kere review edilmis.
    exam: en az bir gecme notu (>= PASS_THRESHOLD) bu lesson icin kayitli."""
    if phase == "exam":
        return _has_passing_exam(lesson_id)
    progress = _phase_progress(lesson_id, phase)
    if progress["total"] == 0:
        return True  # bos asama (orn. L1/L2'de kanji yok) otomatik tamam
    return progress["learned"] >= progress["total"]


def _has_passing_exam(lesson_id):
    """Bu lesson icin gecmis bir Genki exam var mi?"""
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        return False
    scope = f"{lesson['textbook']}:L{lesson['lesson_no']}"
    conn = db.get_connection()
    rows = conn.execute("""
        SELECT score_correct, score_total FROM exam_sessions
        WHERE exam_kind = 'genki' AND exam_scope = ?
              AND finished_at IS NOT NULL AND score_total > 0
    """, (scope,)).fetchall()
    conn.close()
    for r in rows:
        if r["score_correct"] / r["score_total"] >= PASS_THRESHOLD:
            return True
    return False


def is_lesson_complete(lesson_id):
    """Tum 4 asama (vocab + grammar + kanji + exam) tamamlandi mi?"""
    return all(is_phase_complete(lesson_id, p) for p in PHASES)


def is_curriculum_complete(level):
    """Verilen seviyedeki tum lesson'lar tamamlandi mi?"""
    lessons = db.get_lessons(level=level)
    return bool(lessons) and all(is_lesson_complete(l["id"]) for l in lessons)


def get_resume_state(level):
    """Kullanicinin nerede oldugunu hesapla.

    Returns dict:
        {
          "level": str,
          "complete": bool,                  # tum mufredat bitti mi
          "lesson_id": int | None,
          "lesson_no": int | None,
          "lesson_title": str | None,
          "lesson_title_ja": str | None,
          "textbook": str | None,
          "phase": str | None,               # vocab/grammar/kanji/exam
          "phase_progress": {learned, total},
          "lesson_progress": {phases_done, phases_total},
          "overall_progress": {completed_lessons, total_lessons},
        }
    """
    lessons = db.get_lessons(level=level)
    total_lessons = len(lessons)

    if total_lessons == 0:
        return {
            "level": level, "complete": False,
            "lesson_id": None, "lesson_no": None,
            "lesson_title": None, "lesson_title_ja": None, "textbook": None,
            "phase": None,
            "phase_progress": {"learned": 0, "total": 0},
            "lesson_progress": {"phases_done": 0, "phases_total": len(PHASES)},
            "overall_progress": {"completed_lessons": 0, "total_lessons": 0},
        }

    completed = 0
    target_lesson = None
    target_phase = None

    for lesson in lessons:
        if is_lesson_complete(lesson["id"]):
            completed += 1
            continue
        # Ilk eksik lesson — burada duracagiz
        target_lesson = lesson
        for phase in PHASES:
            if not is_phase_complete(lesson["id"], phase):
                target_phase = phase
                break
        break

    if target_lesson is None:
        # Tum lesson'lar tamam
        return {
            "level": level, "complete": True,
            "lesson_id": None, "lesson_no": None,
            "lesson_title": None, "lesson_title_ja": None, "textbook": None,
            "phase": None,
            "phase_progress": {"learned": 0, "total": 0},
            "lesson_progress": {"phases_done": len(PHASES), "phases_total": len(PHASES)},
            "overall_progress": {"completed_lessons": completed, "total_lessons": total_lessons},
        }

    phases_done = sum(1 for p in PHASES if is_phase_complete(target_lesson["id"], p))
    phase_prog = _phase_progress(target_lesson["id"], target_phase) if target_phase != "exam" else {"learned": 0, "total": 1}

    return {
        "level": level, "complete": False,
        "lesson_id": target_lesson["id"],
        "lesson_no": target_lesson["lesson_no"],
        "lesson_title": target_lesson["title"],
        "lesson_title_ja": target_lesson.get("title_ja", ""),
        "textbook": target_lesson["textbook"],
        "phase": target_phase,
        "phase_progress": phase_prog,
        "lesson_progress": {"phases_done": phases_done, "phases_total": len(PHASES)},
        "overall_progress": {"completed_lessons": completed, "total_lessons": total_lessons},
    }


def advance_phase(state):
    """Mevcut asamayi tamamladiktan sonra yeni resume state al.
    UI bu fonksiyonu degil, get_resume_state'i tekrar cagirmali — DB durumu
    icine yansir. Bu fonksiyon sadece readability icin var; ileride alternatif
    yollarla advance gerekirse genisletilir."""
    return get_resume_state(state["level"])
