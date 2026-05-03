"""JLPT mock exam: vocab + grammar sections, multiple choice.

Currently N5 only (v1.7.0-beta scope). N4 in v2.0.0.
Reading/listening sections planned for later.

Question dedup: signature = (item_type, item_id, question_subtype). The same
underlying item can appear in different subtypes (e.g. 食べる as kanji→reading
and again as meaning→word) — those count as distinct questions.
"""

import random
import time

from rich.prompt import Prompt

import db
import ui
import srs
from i18n import t, meaning_field
from exam_common import build_question, has_kanji


# (section, subtype, count_per_section)
N5_BLUEPRINT = [
    ("vocabulary", "kanji_to_reading", 6),
    ("vocabulary", "reading_to_kanji", 4),
    ("vocabulary", "meaning_to_word", 4),
    ("vocabulary", "word_to_meaning", 3),
    ("grammar",    "pattern_to_meaning", 8),
]


def _pick_items(item_type, level, subtype, count, recent_sigs):
    if item_type == "vocabulary":
        pool = [dict(r) for r in db.get_vocabulary(level=level)]
    else:
        pool = [dict(r) for r in db.get_grammar(level=level)]

    if subtype in ("kanji_to_reading", "reading_to_kanji"):
        pool = [p for p in pool if has_kanji(p["word"])]

    # Strict dedup: prefer items whose signature is not in recent
    fresh = [p for p in pool
             if db.question_signature(item_type, p["id"], subtype) not in recent_sigs]
    if len(fresh) >= count:
        return random.sample(fresh, count)
    # Fallback: relax dedup but keep within the level
    if len(pool) >= count:
        return random.sample(pool, count)
    return pool


def _build_questions(level, recent_sigs, blueprint):
    """Build all questions up-front so we know the total count before starting."""
    mf = meaning_field()
    distractor_pools = {
        "vocabulary": [dict(r) for r in db.get_vocabulary(level=level)],
        "grammar":    [dict(r) for r in db.get_grammar(level=level)],
    }

    questions = []
    for section, subtype, count in blueprint:
        items = _pick_items(section, level, subtype, count, recent_sigs)
        for item in items:
            dpool = [d for d in distractor_pools[section] if d["id"] != item["id"]]
            built = build_question(section, item, subtype, dpool, mf)
            if built is None:
                continue
            prompt_text, options, correct_idx = built
            questions.append({
                "section": section,
                "item_type": section,
                "item_id": item["id"],
                "subtype": subtype,
                "prompt": prompt_text,
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


def run_jlpt_exam(level):
    if level != "N5":
        ui.console.print(f"[yellow]{t('jlpt.only_n5')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    blueprint = N5_BLUEPRINT
    recent = db.get_recent_question_signatures("jlpt", level, days=14)
    questions = _build_questions(level, recent, blueprint)

    if not questions:
        ui.console.print(f"[yellow]{t('jlpt.no_questions')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    ui.clear()
    ui.console.print(f"\n[bold]{t('jlpt.title', level=level)}[/bold]")
    ui.console.print(f"[dim]{t('jlpt.subtitle', total=len(questions))}[/dim]\n")
    Prompt.ask(f"[dim]{t('jlpt.start_prompt')}[/dim]", default="")

    session_uuid = db.start_exam_session("jlpt", level, level)
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
    passed = pct >= 60  # JLPT N5 gerçek geçme barajı yaklaşık %60
    style = "bold green" if passed else "bold red"
    label = t("jlpt.pass") if passed else t("jlpt.fail")
    ui.console.print(f"\n[{style}]{label}  ({pct}%)[/{style}]\n")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
