"""Quiz modlari - Japonca ogrenme quiz sistemi."""

import random
import time
from rich.prompt import Prompt
from rich.panel import Panel

import db
import srs
import ui
import tts
from i18n import t, meaning_field


def _quality_from_choice(choice):
    """Kullanici secimini SM-2 kalite puanina cevir."""
    return {"1": 1, "2": 3, "3": 4, "4": 5}.get(choice, 4)


def study_vocabulary(level):
    """Kelime kartlari ile SRS calismasi."""
    ui.clear()
    ui.console.print(f"\n[bold magenta]{t('study.vocab_title', level=level)}[/bold magenta]\n")

    # Bekleyen tekrarlar
    due_reviews = db.get_due_reviews(card_type="vocabulary")
    due_cards = []
    for r in due_reviews:
        vocab = db.get_vocab_by_id(r["card_id"])
        if vocab and vocab["level"] == level:
            due_cards.append(vocab)

    new_cards = db.get_new_cards("vocabulary", level, limit=10)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print(f"[yellow]{t('study.no_cards_vocab')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]{t('study.card_count', total=len(cards), due=len(due_cards), new=len(new_cards))}[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        review = db.get_review("vocabulary", card["id"])
        status = ui.card_status_label(review)
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")

        ui.show_vocab_card(card, show_answer=False)
        tts.speak(card["word"])
        input()

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")
        ui.show_vocab_card(card, show_answer=True)
        if card["example_jp"]:
            tts.speak(card["example_jp"])

        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = review is None
        interval, next_date = srs.review_card("vocabulary", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.show_srs_feedback(quality, interval)
        time.sleep(0.8)
        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]{t('study.done', reviewed=reviewed, correct=correct, minutes=elapsed//60)}[/green]")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def study_kanji(level):
    """Kanji kartlari ile SRS calismasi."""
    ui.clear()
    ui.console.print(f"\n[bold blue]{t('study.kanji_title', level=level)}[/bold blue]\n")

    due_reviews = db.get_due_reviews(card_type="kanji")
    due_cards = []
    for r in due_reviews:
        kanji = db.get_kanji_by_id(r["card_id"])
        if kanji and kanji["level"] == level:
            due_cards.append(kanji)

    new_cards = db.get_new_cards("kanji", level, limit=10)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print(f"[yellow]{t('study.no_cards_kanji')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]{t('study.card_count', total=len(cards), due=len(due_cards), new=len(new_cards))}[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        review = db.get_review("kanji", card["id"])
        status = ui.card_status_label(review)
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")

        ui.show_kanji_card(card, show_answer=False)
        tts.speak(card["kanji"])
        input()

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")
        ui.show_kanji_card(card, show_answer=True)

        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = review is None
        interval, next_date = srs.review_card("kanji", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.show_srs_feedback(quality, interval)
        time.sleep(0.8)
        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]{t('study.done', reviewed=reviewed, correct=correct, minutes=elapsed//60)}[/green]")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def study_grammar(level):
    """Dilbilgisi kartlari ile SRS calismasi."""
    ui.clear()
    ui.console.print(f"\n[bold yellow]{t('study.grammar_title', level=level)}[/bold yellow]\n")

    due_reviews = db.get_due_reviews(card_type="grammar")
    due_cards = []
    for r in due_reviews:
        gram = db.get_grammar_by_id(r["card_id"])
        if gram and gram["level"] == level:
            due_cards.append(gram)

    new_cards = db.get_new_cards("grammar", level, limit=5)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print(f"[yellow]{t('study.no_cards_grammar')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]{t('study.card_count', total=len(cards), due=len(due_cards), new=len(new_cards))}[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        review = db.get_review("grammar", card["id"])
        status = ui.card_status_label(review)
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")

        ui.show_grammar_card(card, show_answer=False)
        tts.speak(card["pattern"])
        input()

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")
        ui.show_grammar_card(card, show_answer=True)
        if card["example_jp"]:
            tts.speak(card["example_jp"])

        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = review is None
        interval, next_date = srs.review_card("grammar", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.show_srs_feedback(quality, interval)
        time.sleep(0.8)
        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]{t('study.done', reviewed=reviewed, correct=correct, minutes=elapsed//60)}[/green]")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def quiz_jp_to_tr(level, count=10):
    """Japonca -> native quiz. 4 sikli coktan secmeli."""
    mf = meaning_field()
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.jp_to_native_title', level=level)}[/bold]\n")

    all_vocab = db.get_vocabulary(level=level)
    if len(all_vocab) < 4:
        ui.console.print(f"[yellow]{t('quiz.not_enough_vocab')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(list(all_vocab), min(count, len(all_vocab)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  [bold white on red] {q['word']} [/bold white on red]  [green]({q['reading']})[/green]\n")

        # 4 sik olustur
        wrong = [v for v in all_vocab if v["id"] != q["id"]]
        distractors = random.sample(wrong, min(3, len(wrong)))
        options = [q[mf]] + [d[mf] for d in distractors]
        random.shuffle(options)

        correct_idx = options.index(q[mf])

        for j, opt in enumerate(options):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask(f"\n{t('quiz.your_answer')}", choices=["1","2","3","4","q"], default="1")
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card("vocabulary", q["id"], 1)

        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def quiz_tr_to_jp(level, count=10):
    """Native -> Japonca quiz. Yazarak cevaplama."""
    mf = meaning_field()
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.native_to_jp_title', level=level)}[/bold]")
    ui.console.print(f"[dim]{t('quiz.native_to_jp_hint')}[/dim]\n")

    all_vocab = db.get_vocabulary(level=level)
    if not all_vocab:
        ui.console.print(f"[yellow]{t('quiz.no_vocab')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(list(all_vocab), min(count, len(all_vocab)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  {t('meaning_label')}: [bold yellow]{q[mf]}[/bold yellow]")
        if mf == "meaning_tr":
            ui.console.print(f"  {t('english_meaning')}: [dim]{q['meaning_en']}[/dim]\n")
        else:
            ui.console.print()

        answer = Prompt.ask(t("quiz.japanese_label")).strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if answer == q["word"] or answer == q["reading"]:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_was', word=q['word'], reading=q['reading'])}")
            srs.review_card("vocabulary", q["id"], 1)

        db.update_stats(reviewed=1, correct=1 if answer in (q["word"], q["reading"]) else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def quiz_kanji_reading(level, count=10):
    """Kanji okuma quiz'i. Kanji goster, okumayi sor."""
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.kanji_reading_title', level=level)}[/bold]")
    ui.console.print(f"[dim]{t('quiz.kanji_reading_hint')}[/dim]\n")

    all_kanji = db.get_kanji(level=level)
    if not all_kanji:
        ui.console.print(f"[yellow]{t('quiz.no_kanji')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    mf = meaning_field()
    questions = random.sample(list(all_kanji), min(count, len(all_kanji)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  {t('kanji')}: [bold white on red] {q['kanji']} [/bold white on red]\n")

        answer = Prompt.ask(t("quiz.reading_label")).strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        valid_readings = []
        for reading_field in [q["kun_yomi"], q["on_yomi"]]:
            for part in reading_field.replace("\u3001", ",").split(","):
                clean = part.strip().split(".")[0].strip()
                if clean:
                    valid_readings.append(clean)

        if answer in valid_readings or answer == q["kun_yomi"].split("\u3001")[0].split(".")[0].strip():
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("kanji", q["id"], 4)
        else:
            readings_str = f"On: {q['on_yomi']} / Kun: {q['kun_yomi']}"
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.readings', readings=readings_str)}")
            srs.review_card("kanji", q["id"], 1)

        ui.console.print(f"  {t('quiz.meaning_line', meaning=q[mf])}")
        db.update_stats(reviewed=1, correct=1 if answer in valid_readings else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def quiz_kanji_meaning(level, count=10):
    """Kanji anlam quiz'i. 4 sikli."""
    mf = meaning_field()
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.kanji_meaning_title', level=level)}[/bold]\n")

    all_kanji = db.get_kanji(level=level)
    if len(all_kanji) < 4:
        ui.console.print(f"[yellow]{t('quiz.not_enough_kanji')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(list(all_kanji), min(count, len(all_kanji)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  {t('kanji')}: [bold white on red] {q['kanji']} [/bold white on red]\n")

        wrong = [k for k in all_kanji if k["id"] != q["id"]]
        distractors = random.sample(wrong, min(3, len(wrong)))
        options = [q[mf]] + [d[mf] for d in distractors]
        random.shuffle(options)
        correct_idx = options.index(q[mf])

        for j, opt in enumerate(options):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask(f"\n{t('quiz.your_answer')}", choices=["1","2","3","4","q"], default="1")
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("kanji", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card("kanji", q["id"], 1)

        ui.console.print(f"  {t('reading')}: On: {q['on_yomi']} / Kun: {q['kun_yomi']}")
        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
