"""Quiz modları - Japonca öğrenme quiz sistemi."""

import random
import time
from rich.prompt import Prompt
from rich.panel import Panel

import db
import srs
import ui


def _quality_from_choice(choice):
    """Kullanıcı seçimini SM-2 kalite puanına çevir."""
    return {"1": 1, "2": 3, "3": 4, "4": 5}.get(choice, 4)


def study_vocabulary(level):
    """Kelime kartları ile SRS çalışması."""
    ui.clear()
    ui.console.print(f"\n[bold magenta]Kelime Çalışma - {level}[/bold magenta]\n")

    # Önce bekleyen tekrarları al
    due_reviews = db.get_due_reviews(card_type="vocabulary")
    due_cards = []
    for r in due_reviews:
        vocab = db.get_vocab_by_id(r["card_id"])
        if vocab and vocab["level"] == level:
            due_cards.append(vocab)

    # Sonra yeni kartlar
    new_cards = db.get_new_cards("vocabulary", level, limit=10)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print("[yellow]Bu seviyede çalışılacak kart yok.[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]Toplam {len(cards)} kart ({len(due_cards)} tekrar, {len(new_cards)} yeni)[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")

        # Kartı göster (cevapsız)
        ui.show_vocab_card(card, show_answer=False)
        input()  # Enter bekle

        # Cevabı göster
        ui.clear()
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")
        ui.show_vocab_card(card, show_answer=True)

        # Değerlendirme
        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = db.get_review("vocabulary", card["id"]) is None
        srs.review_card("vocabulary", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]Çalışma bitti! {reviewed} kart, {correct} doğru, {elapsed//60} dakika[/green]")
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def study_kanji(level):
    """Kanji kartları ile SRS çalışması."""
    ui.clear()
    ui.console.print(f"\n[bold blue]Kanji Çalışma - {level}[/bold blue]\n")

    due_reviews = db.get_due_reviews(card_type="kanji")
    due_cards = []
    for r in due_reviews:
        kanji = db.get_kanji_by_id(r["card_id"])
        if kanji and kanji["level"] == level:
            due_cards.append(kanji)

    new_cards = db.get_new_cards("kanji", level, limit=10)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print("[yellow]Bu seviyede çalışılacak kanji yok.[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]Toplam {len(cards)} kart ({len(due_cards)} tekrar, {len(new_cards)} yeni)[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")

        ui.show_kanji_card(card, show_answer=False)
        input()

        ui.clear()
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")
        ui.show_kanji_card(card, show_answer=True)

        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = db.get_review("kanji", card["id"]) is None
        srs.review_card("kanji", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]Çalışma bitti! {reviewed} kart, {correct} doğru, {elapsed//60} dakika[/green]")
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def study_grammar(level):
    """Dilbilgisi kartları ile SRS çalışması."""
    ui.clear()
    ui.console.print(f"\n[bold yellow]Dilbilgisi Çalışma - {level}[/bold yellow]\n")

    due_reviews = db.get_due_reviews(card_type="grammar")
    due_cards = []
    for r in due_reviews:
        gram = db.get_grammar_by_id(r["card_id"])
        if gram and gram["level"] == level:
            due_cards.append(gram)

    new_cards = db.get_new_cards("grammar", level, limit=5)

    cards = due_cards + list(new_cards)
    if not cards:
        ui.console.print("[yellow]Bu seviyede çalışılacak dilbilgisi yok.[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    random.shuffle(cards)
    ui.console.print(f"[cyan]Toplam {len(cards)} kart ({len(due_cards)} tekrar, {len(new_cards)} yeni)[/cyan]\n")

    start_time = time.time()
    reviewed = 0
    correct = 0
    new_count = 0

    for i, card in enumerate(cards):
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")

        ui.show_grammar_card(card, show_answer=False)
        input()

        ui.clear()
        ui.console.print(f"[dim]── Kart {i+1}/{len(cards)} ──[/dim]\n")
        ui.show_grammar_card(card, show_answer=True)

        choice = ui.show_review_prompt()
        if choice == "q":
            break
        if choice == "s":
            continue

        quality = _quality_from_choice(choice)
        is_new = db.get_review("grammar", card["id"]) is None
        srs.review_card("grammar", card["id"], quality)

        reviewed += 1
        if quality >= 3:
            correct += 1
        if is_new:
            new_count += 1

        ui.clear()

    elapsed = int(time.time() - start_time)
    db.update_stats(reviewed=reviewed, correct=correct, new=new_count, seconds=elapsed)

    ui.console.print(f"\n[green]Çalışma bitti! {reviewed} kart, {correct} doğru, {elapsed//60} dakika[/green]")
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def quiz_jp_to_tr(level, count=10):
    """Japonca → Türkçe quiz. 4 şıklı çoktan seçmeli."""
    ui.clear()
    ui.console.print(f"\n[bold]Quiz: Japonca → Türkçe ({level})[/bold]\n")

    all_vocab = db.get_vocabulary(level=level)
    if len(all_vocab) < 4:
        ui.console.print("[yellow]Yeterli kelime yok (en az 4 gerekli).[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    questions = random.sample(list(all_vocab), min(count, len(all_vocab)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── Soru {i+1}/{total} ──[/dim]")
        ui.console.print(f"\n  [bold white on red] {q['word']} [/bold white on red]  [green]({q['reading']})[/green]\n")

        # 4 şık oluştur
        wrong = [v for v in all_vocab if v["id"] != q["id"]]
        distractors = random.sample(wrong, min(3, len(wrong)))
        options = [q["meaning_tr"]] + [d["meaning_tr"] for d in distractors]
        random.shuffle(options)

        correct_idx = options.index(q["meaning_tr"])

        for j, opt in enumerate(options):
            marker = "  "
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask("\nCevabınız", choices=["1","2","3","4","q"], default="1")
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print("[bold green]  ✓ Doğru![/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ Yanlış![/bold red] Doğru cevap: [yellow]{q['meaning_tr']}[/yellow]")
            srs.review_card("vocabulary", q["id"], 1)

        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def quiz_tr_to_jp(level, count=10):
    """Türkçe → Japonca quiz. Yazarak cevaplama."""
    ui.clear()
    ui.console.print(f"\n[bold]Quiz: Türkçe → Japonca ({level})[/bold]")
    ui.console.print("[dim]Kelimeyi Japonca yazın (hiragana/kanji). 'q' ile çıkış.[/dim]\n")

    all_vocab = db.get_vocabulary(level=level)
    if not all_vocab:
        ui.console.print("[yellow]Bu seviyede kelime yok.[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    questions = random.sample(list(all_vocab), min(count, len(all_vocab)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── Soru {i+1}/{total} ──[/dim]")
        ui.console.print(f"\n  Türkçe: [bold yellow]{q['meaning_tr']}[/bold yellow]")
        ui.console.print(f"  İngilizce: [dim]{q['meaning_en']}[/dim]\n")

        answer = Prompt.ask("Japonca").strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if answer == q["word"] or answer == q["reading"]:
            ui.console.print("[bold green]  ✓ Doğru![/bold green]")
            correct_count += 1
            srs.review_card("vocabulary", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ Yanlış![/bold red] Doğru: [white]{q['word']}[/white] ([green]{q['reading']}[/green])")
            srs.review_card("vocabulary", q["id"], 1)

        db.update_stats(reviewed=1, correct=1 if answer in (q["word"], q["reading"]) else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def quiz_kanji_reading(level, count=10):
    """Kanji okuma quiz'i. Kanji göster, okumayı sor."""
    ui.clear()
    ui.console.print(f"\n[bold]Quiz: Kanji Okuma ({level})[/bold]")
    ui.console.print("[dim]Kanji'nin okumasını yazın (hiragana). 'q' ile çıkış.[/dim]\n")

    all_kanji = db.get_kanji(level=level)
    if not all_kanji:
        ui.console.print("[yellow]Bu seviyede kanji yok.[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    questions = random.sample(list(all_kanji), min(count, len(all_kanji)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── Soru {i+1}/{total} ──[/dim]")
        ui.console.print(f"\n  Kanji: [bold white on red] {q['kanji']} [/bold white on red]\n")

        answer = Prompt.ask("Okuma").strip()
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        # Kun'yomi ve on'yomi parçalarını kontrol et
        valid_readings = []
        for reading_field in [q["kun_yomi"], q["on_yomi"]]:
            for part in reading_field.replace("、", ",").split(","):
                clean = part.strip().split(".")[0].strip()
                if clean:
                    valid_readings.append(clean)

        if answer in valid_readings or answer == q["kun_yomi"].split("、")[0].split(".")[0].strip():
            ui.console.print("[bold green]  ✓ Doğru![/bold green]")
            correct_count += 1
            srs.review_card("kanji", q["id"], 4)
        else:
            readings_str = f"On: {q['on_yomi']} / Kun: {q['kun_yomi']}"
            ui.console.print(f"[bold red]  ✗ Yanlış![/bold red] Okumalar: [green]{readings_str}[/green]")
            srs.review_card("kanji", q["id"], 1)

        ui.console.print(f"  Anlam: [yellow]{q['meaning_tr']}[/yellow] ({q['meaning_en']})")
        db.update_stats(reviewed=1, correct=1 if answer in valid_readings else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def quiz_kanji_meaning(level, count=10):
    """Kanji anlam quiz'i. 4 şıklı."""
    ui.clear()
    ui.console.print(f"\n[bold]Quiz: Kanji → Anlam ({level})[/bold]\n")

    all_kanji = db.get_kanji(level=level)
    if len(all_kanji) < 4:
        ui.console.print("[yellow]Yeterli kanji yok (en az 4 gerekli).[/yellow]")
        Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
        return

    questions = random.sample(list(all_kanji), min(count, len(all_kanji)))
    correct_count = 0
    total = len(questions)

    for i, q in enumerate(questions):
        ui.console.print(f"[dim]── Soru {i+1}/{total} ──[/dim]")
        ui.console.print(f"\n  Kanji: [bold white on red] {q['kanji']} [/bold white on red]\n")

        wrong = [k for k in all_kanji if k["id"] != q["id"]]
        distractors = random.sample(wrong, min(3, len(wrong)))
        options = [q["meaning_tr"]] + [d["meaning_tr"] for d in distractors]
        random.shuffle(options)
        correct_idx = options.index(q["meaning_tr"])

        for j, opt in enumerate(options):
            ui.console.print(f"  [cyan]{j+1}[/cyan]) {opt}")

        answer = Prompt.ask("\nCevabınız", choices=["1","2","3","4","q"], default="1")
        if answer == "q":
            ui.show_quiz_result(correct_count, i)
            return

        if int(answer) - 1 == correct_idx:
            ui.console.print("[bold green]  ✓ Doğru![/bold green]")
            correct_count += 1
            srs.review_card("kanji", q["id"], 4)
        else:
            ui.console.print(f"[bold red]  ✗ Yanlış![/bold red] Doğru: [yellow]{q['meaning_tr']}[/yellow]")
            srs.review_card("kanji", q["id"], 1)

        ui.console.print(f"  Okuma: On: {q['on_yomi']} / Kun: {q['kun_yomi']}")
        db.update_stats(reviewed=1, correct=1 if int(answer) - 1 == correct_idx else 0)
        ui.console.print()

    ui.show_quiz_result(correct_count, total)
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")
