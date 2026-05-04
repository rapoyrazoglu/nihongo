"""Quiz modlari - Japonca ogrenme quiz sistemi."""

import random
import time
from rich.prompt import Prompt
from rich.panel import Panel

import db
import srs
import ui
import tts
import conjugation
from i18n import t, meaning_field, get_card_limit


def _quality_from_choice(choice, vocab_mode=False):
    """Kullanici secimini SM-2 kalite puanina cevir.
    vocab_mode: 2=okuma biliyor kanji bilmiyor (quality=3, weak_kanji=1)"""
    if vocab_mode:
        return {"1": 1, "2": 3, "3": 4, "4": 5}.get(choice, 4)
    return {"1": 1, "2": 3, "3": 4, "4": 5}.get(choice, 4)


def _review_wrong_cards(wrong_cards, card_type, show_fn):
    """Yanlis yapilanları tekrar goster. Kart listesi + gosterim fonksiyonu alir."""
    if not wrong_cards:
        return
    answer = Prompt.ask(f"\n[yellow]{t('quiz.review_wrong', count=len(wrong_cards))}[/yellow]",
                        choices=["e", "h"], default="e")
    if answer != "e":
        return

    ui.clear()
    ui.console.print(f"\n[bold red]{t('quiz.wrong_review_title')}[/bold red]\n")

    for i, card in enumerate(wrong_cards):
        ui.console.print(f"[dim]── {i+1}/{len(wrong_cards)} ──[/dim]\n")
        show_fn(card, show_answer=True)
        text = card.get("reading") if hasattr(card, "get") else None
        if not text:
            try:
                text = card["reading"]
            except (KeyError, IndexError):
                try:
                    text = card["kanji"]
                except (KeyError, IndexError):
                    text = None
        if text:
            tts.speak(text)
        choice = Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")
        if choice == "q":
            break
        ui.clear()


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

    new_cards = db.get_new_cards("vocabulary", level, limit=get_card_limit())

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

        choice = ui.show_review_prompt(vocab_mode=True)
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice, vocab_mode=True)
        is_new = review is None

        # Secim 2: okuma biliyorum, kanji bilmiyorum
        if choice == "2":
            weak_kanji = 1
        elif choice in ("3", "4"):
            weak_kanji = 0  # kanji de biliniyor, flag temizle
        else:
            weak_kanji = None  # 1=bilmiyorum, flag degistirme

        interval, next_date = srs.review_card("vocabulary", card["id"], quality, weak_kanji=weak_kanji)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.show_srs_feedback(quality, interval, weak_kanji=(choice == "2"))
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

    new_cards = db.get_new_cards("kanji", level, limit=get_card_limit())

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

    new_cards = db.get_new_cards("grammar", level, limit=get_card_limit())

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


def _study_cards_loop(cards, card_type, show_fn, vocab_mode=False):
    """Bir liste karta SRS çalışma döngüsü uygula. Hem level-bazlı hem ders-bazlı çalışmada kullanılır."""
    if not cards:
        ui.console.print(f"[yellow]{t('study.no_cards')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return
    cards = list(cards)
    random.shuffle(cards)
    ui.console.print(f"[cyan]{t('study.cards_total', total=len(cards))}[/cyan]\n")

    reviewed = correct = 0
    wrong = []
    for i, card in enumerate(cards):
        review = db.get_review(card_type, card["id"])
        status = ui.card_status_label(review)
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")
        show_fn(card, show_answer=False)
        text_for_tts = None
        if card_type == "vocabulary":
            text_for_tts = card.get("reading") or card.get("word")
        elif card_type == "kanji":
            text_for_tts = card.get("kanji")
        if text_for_tts:
            tts.speak(text_for_tts)
        try:
            input()
        except EOFError:
            break

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.card_n', n=i+1, total=len(cards))} {status} ──[/dim]\n")
        show_fn(card, show_answer=True)
        if card_type == "vocabulary" and card.get("example_jp"):
            tts.speak(card["example_jp"])

        choice = ui.show_review_prompt(vocab_mode=vocab_mode)
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice, vocab_mode=vocab_mode)
        if vocab_mode:
            weak_kanji = 1 if choice == "2" else (0 if choice in ("3", "4") else None)
            srs.review_card(card_type, card["id"], quality, weak_kanji=weak_kanji)
        else:
            srs.review_card(card_type, card["id"], quality)
        reviewed += 1
        if quality >= 3:
            correct += 1
        else:
            wrong.append(card)

    if reviewed > 0:
        db.update_stats(reviewed=reviewed, correct=correct)
    _review_wrong_cards(wrong, card_type, show_fn)
    Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")


def _ask_confidence():
    """Cevap sonrasi 1-4 confidence sorusu. None = sorulmadi (ENTER ile atla)."""
    raw = Prompt.ask(
        f"\n[dim]{t('mastery.confidence_prompt')}[/dim]",
        choices=["1", "2", "3", "4", ""], default="3", show_choices=False
    )
    if not raw or not raw.strip():
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _show_status_milestone(result, previous_status=None):
    """Sadece status DEGISTIGINDE bildirim (Yeni->Ogreniyor->Usta).
    Sayisal rating asla gosterilmez. previous_status: oncekinin status string'i."""
    import elo
    current = result["status"]
    if previous_status is None:
        prev_rating = result["rating_before"]
        previous_status = elo.status_label(prev_rating)
    if current == previous_status:
        return
    # Yukselen vs dusen transition
    order = {"new": 0, "learning": 1, "mastered": 2}
    going_up = order.get(current, 0) > order.get(previous_status, 0)
    color = "bold green" if going_up else "yellow"
    arrow = "→" if going_up else "↓"
    prev_label = t(f"mastery.status.{previous_status}")
    new_label = t(f"mastery.status.{current}")
    ui.console.print(f"  [{color}]{prev_label} {arrow} {new_label}[/{color}]")


def _enrich_with_ratings(cards, entity_type="vocabulary"):
    """Cards listesine her birinin mevcut mastery rating'ini ekle."""
    import elo
    enriched = []
    for c in cards:
        m = db.get_mastery(entity_type, c["id"])
        rating = m["rating"] if m else elo.INITIAL_RATING
        enriched.append({**dict(c), "rating": rating})
    return enriched


def _adaptive_pick(cards, count, session):
    """AdaptiveSession hedefine yakin N kart sec. Random yerine sirali."""
    ordered = session.order_candidates(cards)
    return ordered[:count] if count <= len(ordered) else ordered


def _mini_mc_quiz(cards, count, lesson_id=None):
    """Lesson-scoped mini coktan secmeli quiz (vocab cards). ELO + adaptive zorluk.
    lesson_id verilirse lesson-bazli skill rating de guncellenir."""
    if not cards:
        return
    import elo
    mf = meaning_field()

    # Adaptive session: eger lesson_id varsa lesson skill'inden, yoksa vocab skill'inden
    if lesson_id:
        lesson = db.get_lesson(lesson_id)
        if lesson:
            skill = db.get_skill_rating(f"lesson:{lesson['textbook']}:L{lesson['lesson_no']}")
            if skill == 1400.0:  # default = lesson henüz ogrenilmedi, vocab skill'e dus
                skill = db.get_skill_rating("vocabulary")
        else:
            skill = db.get_skill_rating("vocabulary")
    else:
        skill = db.get_skill_rating("vocabulary")
    session = elo.AdaptiveSession(skill)

    enriched = _enrich_with_ratings(cards, "vocabulary")
    # Hedef-bazli secim: her soruda tekrar siralanir (streak target'a etkiledigi icin)
    asked_ids = set()
    correct = 0
    total = min(count, len(enriched))
    for i in range(total):
        # Adaylar: henuz sorulmamis olanlar; session.target'a gore en yakin
        remaining = [c for c in enriched if c["id"] not in asked_ids]
        if not remaining:
            break
        ordered = session.order_candidates(remaining)
        q = ordered[0]
        asked_ids.add(q["id"])

        stars = elo.stars_render(q["rating"])
        ui.console.print(f"\n[dim]── {t('quiz.question_n', n=i+1, total=total)} "
                         f"[yellow]{stars}[/yellow] ──[/dim]")
        ui.console.print(f"\n  [bold white on red] {q['word']} [/bold white on red]  [green]({q['reading']})[/green]\n")
        wrong = [c for c in cards if c["id"] != q["id"] and c.get(mf)]
        if len(wrong) < 3:
            continue
        distractors = random.sample(wrong, 3)
        options = [q[mf]] + [d[mf] for d in distractors]
        random.shuffle(options)
        correct_idx = options.index(q[mf])
        for j, opt in enumerate(options):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")
        ans = Prompt.ask(f"\n{t('quiz.your_answer')}", choices=["1","2","3","4","q"], default="1")
        if ans == "q":
            break
        is_ok = (int(ans) - 1 == correct_idx)
        if is_ok:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card("vocabulary", q["id"], 1)
        confidence = _ask_confidence()
        prev_status = elo.status_label(q["rating"])
        result = db.record_answer("vocabulary", q["id"], is_ok, confidence, "mc",
                                  lesson_id=lesson_id)
        _show_status_milestone(result, prev_status)
        # Adaptive session report (target shift kalir, hedefin kendisi gizli)
        session.report(is_ok)
        db.update_stats(reviewed=1, correct=1 if is_ok else 0)
    ui.show_quiz_result(correct, total)


def _mini_typing_quiz(cards, count, lesson_id=None):
    """Lesson-scoped mini yazarak quiz (anlam -> kelime). ELO + adaptive zorluk."""
    if not cards:
        return
    import elo
    mf = meaning_field()

    if lesson_id:
        lesson = db.get_lesson(lesson_id)
        if lesson:
            skill = db.get_skill_rating(f"lesson:{lesson['textbook']}:L{lesson['lesson_no']}")
            if skill == 1400.0:
                skill = db.get_skill_rating("vocabulary")
        else:
            skill = db.get_skill_rating("vocabulary")
    else:
        skill = db.get_skill_rating("vocabulary")
    session = elo.AdaptiveSession(skill)
    enriched = _enrich_with_ratings(cards, "vocabulary")

    asked_ids = set()
    correct = 0
    total = min(count, len(enriched))
    for i in range(total):
        remaining = [c for c in enriched if c["id"] not in asked_ids]
        if not remaining:
            break
        ordered = session.order_candidates(remaining)
        q = ordered[0]
        asked_ids.add(q["id"])

        stars = elo.stars_render(q["rating"])
        ui.console.print(f"\n[dim]── {t('quiz.question_n', n=i+1, total=total)} "
                         f"[yellow]{stars}[/yellow] ──[/dim]")
        ui.console.print(f"\n  [bold yellow]{q[mf]}[/bold yellow]\n")
        ans = Prompt.ask(t("quiz.your_answer"))
        if ans.lower() in ("q", "quit"):
            break
        normalized = ans.strip()
        is_ok = normalized in (q["word"], q["reading"])
        if is_ok:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] "
                             f"{t('quiz.correct_was', word=q['word'], reading=q['reading'])}")
            srs.review_card("vocabulary", q["id"], 1)
        confidence = _ask_confidence()
        prev_status = elo.status_label(q["rating"])
        result = db.record_answer("vocabulary", q["id"], is_ok, confidence, "typing",
                                  lesson_id=lesson_id)
        _show_status_milestone(result, prev_status)
        session.report(is_ok)
        db.update_stats(reviewed=1, correct=1 if is_ok else 0)
    ui.show_quiz_result(correct, total)


def _load_lesson_enrichment(lesson_id):
    """genki1.json'daki enrichment alanlarini lesson kayitiyla birlikte don."""
    import os, json as _json
    from paths import DATA_DIR
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        return None
    path = os.path.join(DATA_DIR, "genki1.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            book = _json.load(f)
    except Exception:
        return None
    for entry in book.get("lessons", []):
        if entry.get("lesson_no") == lesson["lesson_no"] and book.get("textbook") == lesson.get("textbook"):
            return entry
    return None


def _show_lesson_intro(enrichment):
    """Ders basinda description'i goster."""
    if not enrichment or not enrichment.get("description"):
        return
    ui.console.print(f"\n[bold cyan]{t('guided.intro_title')}[/bold cyan]\n")
    ui.console.print(f"  [white]{enrichment['description']}[/white]\n")
    Prompt.ask(f"[dim]{t('guided.intro_continue')}[/dim]", default="")


def _show_lesson_real_life(enrichment):
    """Ders sonunda cultural notes + diyaloglar + gercek hayat gorevleri."""
    if not enrichment:
        return
    notes = enrichment.get("cultural_notes") or []
    dialogues = enrichment.get("dialogues") or []
    prompts = enrichment.get("real_world_prompts") or []
    if not (notes or dialogues or prompts):
        return

    ui.clear()
    ui.console.print(f"\n[bold magenta]{t('guided.real_life_title')}[/bold magenta]\n")

    # Cultural notes
    if notes:
        ui.console.print(f"[bold yellow]{t('guided.cultural_notes')}[/bold yellow]\n")
        for n in notes:
            ui.console.print(f"  • [bold cyan]{n.get('topic','')}[/bold cyan]")
            ui.console.print(f"    {n.get('text','')}\n")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")

    # Diyaloglar
    if dialogues:
        ui.clear()
        ui.console.print(f"\n[bold yellow]{t('guided.dialogues')}[/bold yellow]\n")
        for i, d in enumerate(dialogues, 1):
            ui.console.print(f"[bold]── {t('guided.dialogue_n', n=i, total=len(dialogues))} ──[/bold]")
            if d.get("context"):
                ui.console.print(f"[dim italic]{d['context']}[/dim italic]\n")
            for line in d.get("lines", []):
                speaker = line.get("speaker", "")
                ui.console.print(f"  [cyan]{speaker}:[/cyan]  [bold white]{line.get('jp','')}[/bold white]")
                ui.console.print(f"        [dim]{line.get('tr','')}[/dim]")
            highlights = d.get("highlights", [])
            if highlights:
                ui.console.print(f"  [yellow]{t('guided.dialogue_uses')}:[/yellow] "
                                 f"[dim]{', '.join(highlights)}[/dim]")
            ui.console.print()
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")

    # Real world prompts
    if prompts:
        ui.clear()
        ui.console.print(f"\n[bold yellow]{t('guided.real_world')}[/bold yellow]\n")
        ui.console.print(f"[dim italic]{t('guided.real_world_intro')}[/dim italic]\n")
        for i, p in enumerate(prompts, 1):
            ui.console.print(f"  [bold cyan]{i}.[/bold cyan] {p}")
        ui.console.print()
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def guided_lesson_study(lesson_id):
    """Konu anlat -> pratik yap akisi.
    Her grammar concept icin: detayli aciklama -> kullanici pratik modu secer
    (yazarak / coktan secmeli) -> mini quiz lesson'un vocab pool'undan.
    Ders basinda intro paragrafi, sonunda cultural notes + diyaloglar +
    real-world gorevleri (genki1.json enrichment alanlarindan)."""
    items = db.get_lesson_items(lesson_id)
    grammar_concepts = items["grammar"]
    vocab_pool = items["vocabulary"]
    lesson = db.get_lesson(lesson_id)
    enrichment = _load_lesson_enrichment(lesson_id)

    ui.clear()
    title = f"L{lesson['lesson_no']}: {lesson['title']}"
    ui.console.print(f"\n[bold cyan]{t('guided.session_title', title=title)}[/bold cyan]\n")

    # Lesson intro
    _show_lesson_intro(enrichment)

    if not grammar_concepts:
        ui.console.print(f"[yellow]{t('guided.no_grammar')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        # Vocab varsa sadece vocab calistir
        if vocab_pool:
            _study_cards_loop(vocab_pool, "vocabulary", ui.show_vocab_card, vocab_mode=True)
        return

    n_concepts = len(grammar_concepts)
    for idx, concept in enumerate(grammar_concepts):
        ui.clear()
        ui.console.print(f"[dim]── {t('guided.concept_n', n=idx+1, total=n_concepts)} ──[/dim]\n")

        # 1) Konu anlatimi
        ui.show_grammar_card(concept, show_answer=True)
        Prompt.ask(f"\n[dim]{t('guided.continue_to_practice')}[/dim]", default="")

        # 2) Pratik modu sec
        ui.clear()
        ui.console.print(f"[dim]── {t('guided.concept_n', n=idx+1, total=n_concepts)} ──[/dim]\n")
        ui.console.print(f"[bold]{concept['pattern']}[/bold]\n")
        ui.console.print(f"[bold]{t('guided.pick_practice')}[/bold]")
        ui.console.print(f"  [cyan]1[/cyan] {t('guided.practice_typing')}")
        ui.console.print(f"  [cyan]2[/cyan] {t('guided.practice_mc')}")
        ui.console.print(f"  [cyan]0[/cyan] {t('guided.practice_skip')}")
        choice = Prompt.ask(t("your_choice"), choices=["0", "1", "2"], default="2")

        if choice == "0":
            # SRS kaydı yine de; "biliyorum" sayalım, hızlı geç
            srs.review_card("grammar", concept["id"], 4)
            continue

        # Concept'i de SRS'e bildir (gördü)
        srs.review_card("grammar", concept["id"], 4)

        # 3) Mini quiz vocab pool uzerinde
        practice_n = min(5, len(vocab_pool))
        if practice_n < 1:
            ui.console.print(f"[yellow]{t('guided.no_practice_pool')}[/yellow]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
            continue

        ui.clear()
        ui.console.print(f"[bold cyan]{t('guided.practice_starting', n=practice_n)}[/bold cyan]\n")
        if choice == "1":
            _mini_typing_quiz(vocab_pool, practice_n, lesson_id=lesson_id)
        else:
            _mini_mc_quiz(vocab_pool, practice_n, lesson_id=lesson_id)

        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")

    # Gercek hayat senaryolarini goster (enrichment varsa)
    _show_lesson_real_life(enrichment)

    # Bitiş ekrani
    ui.clear()
    ui.console.print(f"\n[bold green]{t('guided.session_complete')}[/bold green]\n")
    ui.console.print(f"[dim]{t('guided.exam_hint')}[/dim]\n")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def study_lesson_vocab(lesson_id):
    cards = db.get_lesson_items(lesson_id, "vocabulary")["vocabulary"]
    ui.clear()
    ui.console.print(f"\n[bold magenta]{t('study.lesson_vocab_title')}[/bold magenta]\n")
    _study_cards_loop(cards, "vocabulary", ui.show_vocab_card, vocab_mode=True)


def study_lesson_grammar(lesson_id):
    cards = db.get_lesson_items(lesson_id, "grammar")["grammar"]
    ui.clear()
    ui.console.print(f"\n[bold magenta]{t('study.lesson_grammar_title')}[/bold magenta]\n")
    _study_cards_loop(cards, "grammar", ui.show_grammar_card)


def study_lesson_kanji(lesson_id):
    cards = db.get_lesson_items(lesson_id, "kanji")["kanji"]
    ui.clear()
    ui.console.print(f"\n[bold magenta]{t('study.lesson_kanji_title')}[/bold magenta]\n")
    _study_cards_loop(cards, "kanji", ui.show_kanji_card)


def quiz_lesson_exam(lesson_id, count=10):
    """Bir dersten karışık (vocab + grammar + kanji) çoktan seçmeli sınav."""
    mf = meaning_field()
    ui.clear()
    lesson = db.get_lesson(lesson_id)
    title_str = f"L{lesson['lesson_no']}: {lesson['title']}"
    ui.console.print(f"\n[bold]{t('quiz.lesson_exam_title', lesson=title_str)}[/bold]\n")

    items = db.get_lesson_items(lesson_id)
    pool = (
        [("vocabulary", v) for v in items["vocabulary"]]
        + [("grammar", g) for g in items["grammar"]]
        + [("kanji", k) for k in items["kanji"]]
    )

    if len(pool) < 4:
        ui.console.print(f"[yellow]{t('quiz.lesson_not_enough')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(pool, min(count, len(pool)))
    correct_count = 0
    total = len(questions)

    all_v = db.get_vocabulary()
    all_g = db.get_grammar()
    all_k = db.get_kanji()

    for i, (typ, q) in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} [{typ}] ──[/dim]")

        if typ == "vocabulary":
            ui.console.print(f"\n  [bold white on red] {q['word']} [/bold white on red]  [green]({q['reading']})[/green]\n")
            distractor_pool = [v for v in all_v if v["id"] != q["id"] and v[mf]]
        elif typ == "grammar":
            ui.console.print(f"\n  [bold yellow]{q['pattern']}[/bold yellow]")
            if q.get("example_jp"):
                ui.console.print(f"  [dim]{q['example_jp']}[/dim]")
            ui.console.print()
            distractor_pool = [g for g in all_g if g["id"] != q["id"] and g[mf]]
        else:  # kanji
            ui.console.print(f"\n  [bold white on red] {q['kanji']} [/bold white on red]  [green]On: {q['on_yomi']} | Kun: {q['kun_yomi']}[/green]\n")
            distractor_pool = [k for k in all_k if k["id"] != q["id"] and k[mf]]

        if len(distractor_pool) < 3:
            continue
        distractors = random.sample(distractor_pool, 3)
        options = [q[mf]] + [d[mf] for d in distractors]
        random.shuffle(options)
        correct_idx = options.index(q[mf])

        for j, opt in enumerate(options):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask(f"\n{t('quiz.your_answer')}", choices=["1", "2", "3", "4", "q"], default="1")
        if answer == "q":
            break

        is_correct = (int(answer) - 1 == correct_idx)
        if is_correct:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card(typ, q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card(typ, q["id"], 1)

        db.update_stats(reviewed=1, correct=1 if is_correct else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
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
    wrong_cards = []

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
            _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card("vocabulary", q["id"], 1)
            wrong_cards.append(q)

        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
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
    wrong_cards = []

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
            _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
            return

        if answer == q["word"] or answer == q["reading"]:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_was', word=q['word'], reading=q['reading'])}")
            srs.review_card("vocabulary", q["id"], 1)
            wrong_cards.append(q)

        db.update_stats(reviewed=1, correct=1 if answer in (q["word"], q["reading"]) else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
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
    wrong_cards = []

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  {t('kanji')}: [bold white on red] {q['kanji']} [/bold white on red]\n")

        answer = Prompt.ask(t("quiz.reading_label")).strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            _review_wrong_cards(wrong_cards, "kanji", ui.show_kanji_card)
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
            wrong_cards.append(q)

        ui.console.print(f"  {t('quiz.meaning_line', meaning=q[mf])}")
        db.update_stats(reviewed=1, correct=1 if answer in valid_readings else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    _review_wrong_cards(wrong_cards, "kanji", ui.show_kanji_card)
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
    wrong_cards = []

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
            _review_wrong_cards(wrong_cards, "kanji", ui.show_kanji_card)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("kanji", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red] {t('quiz.correct_answer', answer=q[mf])}")
            srs.review_card("kanji", q["id"], 1)
            wrong_cards.append(q)

        ui.console.print(f"  {t('reading')}: On: {q['on_yomi']} / Kun: {q['kun_yomi']}")
        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    _review_wrong_cards(wrong_cards, "kanji", ui.show_kanji_card)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def _split_japanese(sentence):
    """Japonca cumleyi parcalara ayir. Particle-aware bolme."""
    # Noktalama temizle
    clean = sentence.replace("。", "").replace("、", "").replace("！", "").replace("？", "").strip()
    if not clean:
        return []

    # Particle'lardan sonra bol
    import re
    # Particle: は が を に で へ の と も か ね よ
    # Ayrica: です ます した ない から まで より けど
    parts = re.split(r'(は|が|を|に|で|へ|の|と|も|か|ね|よ|から|まで|より|けど)', clean)

    # Particle'lari onceki chunk'a yap (は → 私は)
    chunks = []
    i = 0
    while i < len(parts):
        if not parts[i]:
            i += 1
            continue
        chunk = parts[i]
        # Sonraki parca particle mi?
        if i + 1 < len(parts) and len(parts[i+1]) <= 3:
            chunk += parts[i+1]
            i += 2
        else:
            i += 1
        if chunk.strip():
            chunks.append(chunk)

    # 2'den az parca varsa kullanilamaz
    return chunks if len(chunks) >= 2 else []


def quiz_sentence_order(level, count=10):
    """Cumle siralama quiz'i. Karisik parcalari dogru siraya diz."""
    mf = meaning_field()
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.sentence_order_title', level=level)}[/bold]")
    ui.console.print(f"[dim]{t('quiz.sentence_order_hint')}[/dim]\n")

    all_vocab = db.get_vocabulary(level=level)
    # Ornek cumlesi olan ve parcalanabilen kelimeleri filtrele
    with_examples = []
    for v in all_vocab:
        if v["example_jp"] and len(v["example_jp"]) >= 6:
            chunks = _split_japanese(v["example_jp"])
            if len(chunks) >= 3:
                with_examples.append(v)

    if len(with_examples) < 3:
        ui.console.print(f"[yellow]{t('quiz.not_enough_vocab')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(with_examples, min(count, len(with_examples)))
    correct_count = 0
    total = len(questions)
    wrong_cards = []

    for i, q in enumerate(questions):
        sentence = q["example_jp"]
        chunks = _split_japanese(sentence)

        # Karistir (dogru sirayla ayni olmayana kadar)
        shuffled = chunks[:]
        attempts = 0
        while shuffled == chunks and attempts < 10:
            random.shuffle(shuffled)
            attempts += 1

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")

        # Anlami goster
        meaning = q[mf] or q["meaning_en"]
        ui.console.print(f"\n  {t('meaning_label')}: [bold yellow]{meaning}[/bold yellow]")
        ui.console.print(f"  {t('word')}: [bold white]{q['word']}[/bold white] ({q['reading']})\n")

        # Karisik parcalari numarayla goster
        for j, chunk in enumerate(shuffled):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {chunk}")

        ui.console.print(f"\n  [dim]{t('quiz.sentence_order_input')}[/dim]")
        answer = Prompt.ask(t("quiz.your_answer")).strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
            return

        # Kullanicinin sirasini kontrol et
        try:
            user_order = [int(x) - 1 for x in answer.replace(",", " ").replace("-", " ").split()]
            user_sentence = "".join(shuffled[idx] for idx in user_order)
        except (ValueError, IndexError):
            user_sentence = ""

        # Dogru cumle (noktalama haric)
        correct_sentence = "".join(chunks)

        if user_sentence == correct_sentence:
            ui.console.print(f"\n[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            ui.console.print(f"  {sentence}")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"\n[bold red]  ✗ {t('quiz.wrong')}[/bold red]")
            ui.console.print(f"  {t('quiz.correct_sentence')}: {sentence}")
            srs.review_card("vocabulary", q["id"], 1)
            wrong_cards.append(q)

        tts.speak(sentence)
        db.update_stats(reviewed=1, correct=1 if user_sentence == correct_sentence else 0)
        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")

    ui.show_quiz_result(correct_count, total)
    _review_wrong_cards(wrong_cards, "vocabulary", ui.show_vocab_card)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def quiz_conjugation(level, count=10):
    """Fiil çekim drilli. Fiil + hedef form verilir, kullanıcı çekimler."""
    ui.clear()
    ui.console.print(f"\n[bold]{t('quiz.conjugation_title', level=level)}[/bold]")
    ui.console.print(f"[dim]{t('quiz.conjugation_hint')}[/dim]\n")

    all_vocab = db.get_vocabulary(level=level)
    # Sadece fiilleri filtrele
    verbs = [v for v in all_vocab if v["part_of_speech"] in ("fiil", "動詞")]
    if len(verbs) < 3:
        ui.console.print(f"[yellow]{t('quiz.not_enough_vocab')}[/yellow]")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    questions = random.sample(verbs, min(count, len(verbs)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        form = random.choice(conjugation.FORMS)
        form_jp, form_en = conjugation.FORM_NAMES[form]
        correct_answer = conjugation.conjugate(q["word"], q["reading"], form)

        ui.clear()
        ui.console.print(f"[dim]── {t('quiz.question_n', n=i+1, total=total)} ──[/dim]")
        ui.console.print(f"\n  {t('word')}: [bold white on red] {q['word']} [/bold white on red]  [green]({q['reading']})[/green]")
        ui.console.print(f"  {t('quiz.target_form')}: [bold yellow]{form_jp}[/bold yellow] ({form_en})\n")

        answer = Prompt.ask(t("quiz.conjugation_label")).strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if answer == correct_answer:
            ui.console.print(f"[bold green]  ✓ {t('quiz.correct')}[/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ {t('quiz.wrong')}[/bold red]  {correct_answer}")
            srs.review_card("vocabulary", q["id"], 1)

        tts.speak(correct_answer)
        db.update_stats(reviewed=1, correct=1 if answer == correct_answer else 0)
        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")

    ui.show_quiz_result(correct_count, total)
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
