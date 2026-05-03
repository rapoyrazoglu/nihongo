"""Genki textbook cumulative lesson exam.

Picking lesson L<n> tests vocab + grammar from L1..L<n>, weighted toward L<n>
so the latest material gets the most coverage. Same MCQ subtypes as JLPT,
shorter blueprint since lesson scope is narrower.

Dedup scope is per (textbook, lesson) — re-running the same exam pulls fresh
questions for 14 days; older history can repeat.
"""

import random
import time

from rich.prompt import Prompt

import db
import ui
import srs
from i18n import t, meaning_field
from exam_common import build_question, has_kanji


# (section, subtype, count_per_section) — total ~15 sorular per exam
LESSON_BLUEPRINT = [
    ("vocabulary", "kanji_to_reading", 3),
    ("vocabulary", "reading_to_kanji", 2),
    ("vocabulary", "meaning_to_word", 3),
    ("vocabulary", "word_to_meaning", 2),
    ("grammar",    "pattern_to_meaning", 5),
]

# Latest lesson gets this fraction of questions per subtype, prior lessons share the rest.
LATEST_WEIGHT = 0.5


def _cumulative_pool(textbook, max_lesson_no):
    """Return {'vocabulary': {lesson_no: [items]}, 'grammar': {...}} for L1..max."""
    lessons = [l for l in db.get_lessons(textbook=textbook)
               if l["lesson_no"] <= max_lesson_no]
    pool = {"vocabulary": {}, "grammar": {}}
    for lesson in lessons:
        items = db.get_lesson_items(lesson["id"])
        pool["vocabulary"][lesson["lesson_no"]] = list(items["vocabulary"])
        pool["grammar"][lesson["lesson_no"]] = list(items["grammar"])
    return pool


def _pick_with_weight(pool_by_lesson, max_lesson, subtype, count, recent_sigs, item_type):
    """Pick `count` items: ~LATEST_WEIGHT from max_lesson, rest from prior lessons.
    Avoid recently-seen signatures; relax fallback if pool too small."""
    latest = pool_by_lesson.get(max_lesson, [])
    prior = []
    for ln, items in pool_by_lesson.items():
        if ln != max_lesson:
            prior.extend(items)

    if subtype in ("kanji_to_reading", "reading_to_kanji"):
        latest = [p for p in latest if has_kanji(p["word"])]
        prior = [p for p in prior if has_kanji(p["word"])]

    def fresh(items):
        return [p for p in items
                if db.question_signature(item_type, p["id"], subtype) not in recent_sigs]

    n_latest = max(1, int(round(count * LATEST_WEIGHT))) if latest else 0
    n_prior = count - n_latest

    chosen = []
    f_latest = fresh(latest)
    chosen.extend(random.sample(f_latest, min(n_latest, len(f_latest))))

    if prior and n_prior > 0:
        f_prior = fresh(prior)
        chosen.extend(random.sample(f_prior, min(n_prior, len(f_prior))))

    # Top up if dedup left us short
    if len(chosen) < count:
        seen_ids = {p["id"] for p in chosen}
        remaining = [p for p in (latest + prior) if p["id"] not in seen_ids]
        chosen.extend(random.sample(remaining, min(count - len(chosen), len(remaining))))

    return chosen


def _build_questions(textbook, lesson_no, recent_sigs, blueprint):
    mf = meaning_field()
    pool_by = _cumulative_pool(textbook, lesson_no)

    # Distractor pool = whole cumulative pool for that section
    distractor_pools = {
        "vocabulary": [v for items in pool_by["vocabulary"].values() for v in items],
        "grammar":    [g for items in pool_by["grammar"].values() for g in items],
    }

    questions = []
    for section, subtype, count in blueprint:
        items = _pick_with_weight(
            pool_by[section], lesson_no, subtype, count, recent_sigs, section,
        )
        for item in items:
            dpool = [d for d in distractor_pools[section] if d["id"] != item["id"]]
            built = build_question(section, item, subtype, dpool, mf)
            if built is None:
                continue
            prompt, options, correct_idx = built
            questions.append({
                "section": section,
                "item_type": section,
                "item_id": item["id"],
                "subtype": subtype,
                "prompt": prompt,
                "options": options,
                "correct_idx": correct_idx,
            })

    # Group by section, shuffle within, keep vocab→grammar order
    by_section = {}
    for q in questions:
        by_section.setdefault(q["section"], []).append(q)
    for sec in by_section:
        random.shuffle(by_section[sec])
    ordered = []
    for sec in ("vocabulary", "grammar"):
        ordered.extend(by_section.get(sec, []))
    return ordered


def run_genki_lesson_exam(level, lesson_id):
    """Cumulative exam for a Genki lesson: L1..lesson covered, weighted to current."""
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        ui.console.print(f"[red]{t('genki_exam.no_lesson')}[/red]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    textbook = lesson["textbook"]
    lesson_no = lesson["lesson_no"]
    scope = f"{textbook}:L{lesson_no}"

    recent = db.get_recent_question_signatures("genki", scope, days=14)
    questions = _build_questions(textbook, lesson_no, recent, LESSON_BLUEPRINT)

    if not questions:
        ui.console.print(f"[yellow]{t('genki_exam.no_questions')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    ui.clear()
    ui.console.print(
        f"\n[bold]{t('genki_exam.title', textbook=textbook.upper(), lesson_no=lesson_no, title=lesson['title'])}[/bold]"
    )
    ui.console.print(
        f"[dim]{t('genki_exam.subtitle', max_lesson=lesson_no, total=len(questions))}[/dim]\n"
    )
    Prompt.ask(f"[dim]{t('jlpt.start_prompt')}[/dim]", default="")

    session_uuid = db.start_exam_session("genki", scope, level)
    started_at = time.time()

    correct_count = 0
    current_section = None

    for i, q in enumerate(questions):
        ui.clear()

        if q["section"] != current_section:
            current_section = q["section"]
            sec_label = t(f"jlpt.section.{current_section}")
            ui.console.print(f"\n[bold magenta]── {sec_label} ──[/bold magenta]\n")
        else:
            ui.console.print()

        sub_label = t(f"jlpt.subtype.{q['subtype']}")
        ui.console.print(
            f"[dim]{t('quiz.question_n', n=i+1, total=len(questions))}  ·  {sub_label}[/dim]\n"
        )
        ui.console.print(f"  [bold white]{q['prompt']}[/bold white]\n")
        for j, opt in enumerate(q["options"]):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask(
            f"\n{t('quiz.your_answer')}",
            choices=["1", "2", "3", "4", "q"],
            default="1",
        )
        if answer == "q":
            break

        is_correct = (int(answer) - 1 == q["correct_idx"])
        db.record_exam_question(
            session_uuid, q["section"], q["subtype"],
            q["item_type"], q["item_id"], 1 if is_correct else 0,
        )

        if is_correct:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card(q["item_type"], q["item_id"], 4)
        else:
            ui.console.print(
                f"[bold red]  ✗ {t('quiz.wrong')}[/bold red]  "
                f"{t('quiz.correct_answer', answer=q['options'][q['correct_idx']])}"
            )
            srs.review_card(q["item_type"], q["item_id"], 1)

        db.update_stats(reviewed=1, correct=1 if is_correct else 0)
        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")

    duration = int(time.time() - started_at)
    db.finish_exam_session(session_uuid, correct_count, len(questions), duration)

    ui.clear()
    ui.show_quiz_result(correct_count, len(questions))
    pct = (correct_count * 100) // max(len(questions), 1)
    style = "bold green" if pct >= 70 else "bold yellow" if pct >= 50 else "bold red"
    ui.console.print(f"\n[{style}]{t('genki_exam.score', pct=pct)}[/{style}]\n")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
