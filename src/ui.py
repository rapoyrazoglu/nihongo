"""Rich terminal arayuzu - Nihongo ogrenme uygulamasi."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.prompt import Prompt, IntPrompt
from rich import box
import db
from i18n import t, meaning_field, get_lang, translate_pos

console = Console()

LEVELS = ["N5", "N4", "N3", "N2", "N1"]


def clear():
    console.clear()


def banner():
    """Kirmizi blokta beyaz 日本 (README'deki SVG ikonun terminal uyarlamasi)."""
    flag = Text()
    flag.append("       \n", style="white on red")
    flag.append("   ", style="white on red")
    flag.append("日本", style="bold white on red")
    flag.append("   \n", style="white on red")
    flag.append("       ", style="white on red")

    name = Text()
    name.append("\n  日本語マスター\n", style="bold red")
    name.append("  Nihongo Master\n", style="bold yellow")
    name.append("  ", style="dim")
    name.append("〜 SRS / Quiz / Genki / JLPT 〜", style="dim white")

    columns = Columns([flag, name], padding=(0, 3), expand=False)
    console.print(Panel(columns, border_style="red", box=box.DOUBLE, padding=(0, 2)))


def show_main_menu():
    clear()
    banner()

    today = db.get_today_stats()
    due = db.count_due_reviews()

    streak = db.get_streak()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="cyan")
    info_table.add_column(style="white")
    info_table.add_row(t("due_reviews"), f"[bold yellow]{due}[/bold yellow] {t('cards')}")
    if today:
        info_table.add_row(t("today_studied"), f"{today['cards_reviewed']} {t('cards')}")
        info_table.add_row(t("accuracy"), f"{today['cards_correct']}/{today['cards_reviewed']}" if today['cards_reviewed'] > 0 else "—")
    else:
        info_table.add_row(t("today_studied"), f"0 {t('cards')}")
    if streak > 0:
        if streak >= 30:
            streak_style = "bold magenta"
        elif streak >= 7:
            streak_style = "bold green"
        else:
            streak_style = "yellow"
        info_table.add_row(t("streak"), f"[{streak_style}]{streak} {t('streak.days')}[/{streak_style}]")

    try:
        import curriculum
        from i18n import get_level
        resume = curriculum.get_resume_state(get_level() or "N5")
    except Exception:
        resume = None
    if resume and not resume.get("complete") and resume.get("lesson_id"):
        op = resume["overall_progress"]
        phase = t(f"resume.phase.{resume['phase']}")
        info_table.add_row(
            f"[bold green]{t('menu.resume_label')}[/bold green]",
            f"L{resume['lesson_no']} {resume['lesson_title']} — [yellow]{phase}[/yellow]  "
            f"[dim]({op['completed_lessons']}/{op['total_lessons']})[/dim]"
        )
    elif resume and resume.get("complete"):
        info_table.add_row(
            f"[bold green]{t('menu.resume_label')}[/bold green]",
            f"[bold green]{t('resume.curriculum_complete_short')}[/bold green]"
        )

    try:
        from updater import check_update_async
        update_info = check_update_async()
    except Exception:
        update_info = None
    if update_info:
        info_table.add_row(
            f"[bold yellow]{t('update.available_label')}[/bold yellow]",
            f"[bold green]v{update_info['latest']}[/bold green]  [dim]{t('update.run_hint')}[/dim]"
        )

    console.print(Panel(info_table, title=f"[bold]{t('daily_summary')}[/bold]", border_style="blue"))
    console.print()

    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column(t("your_choice"), style="white")
    menu.add_column("", style="dim")

    menu.add_row("1", f"[bold green]{t('menu.resume')}[/bold green]", t("menu.resume_desc"))
    menu.add_row("2", t("menu.study_vocab"), t("menu.study_vocab_desc"))
    menu.add_row("3", t("menu.study_kanji"), t("menu.study_kanji_desc"))
    menu.add_row("4", t("menu.study_grammar"), t("menu.study_grammar_desc"))
    menu.add_row("5", t("menu.quiz"), t("menu.quiz_desc"))
    menu.add_row("6", t("menu.vocab_list"), t("menu.vocab_list_desc"))
    menu.add_row("7", t("menu.kanji_list"), t("menu.kanji_list_desc"))
    menu.add_row("8", t("menu.stats"), t("menu.stats_desc"))
    menu.add_row("9", t("menu.settings"), t("menu.settings_desc"))
    menu.add_row("A", t("menu.search"), t("menu.search_desc"))
    menu.add_row("T", t("menu.textbook"), t("menu.textbook_desc"))
    menu.add_row("0", t("menu.exit"), t("menu.exit_desc"))

    console.print(Panel(menu, title=f"[bold]{t('main_menu')}[/bold]", border_style="green"))

    raw = Prompt.ask(f"\n[bold cyan]{t('your_choice')}[/bold cyan]", default="1")
    return raw.strip().upper() if raw else "1"


def show_level_select(title=None):
    if title is None:
        title = t("select_level")
    console.print(f"\n[bold]{title}[/bold]")
    for i, level in enumerate(LEVELS, 1):
        count_v = db.count_vocabulary(level)
        count_k = db.count_kanji(level)
        console.print(f"  [cyan]{i}[/cyan] - {t('level_info', level=level, vocab=count_v, kanji=count_k)}")
    console.print(f"  [cyan]0[/cyan] - {t('back')}")

    choice = Prompt.ask(t("level"), choices=["0","1","2","3","4","5"], default="1")
    if choice == "0":
        return None
    return LEVELS[int(choice) - 1]


def _meaning_rows(card, card_table, card_type="vocab"):
    """Add meaning rows to a card table based on current language."""
    mf = meaning_field()
    if get_lang() != "en":
        native = card[mf] or card["meaning_en"]
        card_table.add_row(t("native_meaning"), f"[bold yellow]{native}[/bold yellow]")
        card_table.add_row(t("english_meaning"), card["meaning_en"])
    else:
        card_table.add_row(t("meaning_label"), f"[bold yellow]{card['meaning_en']}[/bold yellow]")


def _should_show_hiragana(word, level):
    """N5 kelimelerinde kanji bilinmiyorsa True don."""
    if level != "N5":
        return False
    import unicodedata
    # Kelimede kanji var mi?
    has_kanji = any(unicodedata.category(ch) == "Lo" and ord(ch) >= 0x4E00 for ch in word)
    if not has_kanji:
        return False
    # Kullanicinin ogrendigi kanjileri kontrol et
    learned = set()
    conn = db.get_connection()
    rows = conn.execute("""
        SELECT k.kanji FROM kanji k
        JOIN reviews r ON r.card_type = 'kanji' AND r.card_id = k.id
        WHERE r.repetitions >= 1
    """).fetchall()
    conn.close()
    learned = {r["kanji"] for r in rows}
    # Kelimedeki her kanji ogrenilmis mi?
    for ch in word:
        if ord(ch) >= 0x4E00 and unicodedata.category(ch) == "Lo":
            if ch not in learned:
                return True  # Bilinmeyen kanji var
    return False


def show_vocab_card(vocab, show_answer=False):
    """Kelime kartini goster."""
    card = Table(show_header=False, box=box.ROUNDED, border_style="magenta", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    word_display = vocab["word"]
    level = vocab["level"] if "level" in vocab.keys() else ""
    if _should_show_hiragana(vocab["word"], level):
        word_display = f"{vocab['reading']} [dim]({vocab['word']})[/dim]"
        card.add_row(t("word"), f"[bold bright_white]{word_display}[/bold bright_white]")
    else:
        card.add_row(t("word"), f"[bold bright_white]{vocab['word']}[/bold bright_white]")
    card.add_row(t("reading"), f"[bold green]{vocab['reading']}[/bold green]")

    if show_answer:
        _meaning_rows(vocab, card)
        if vocab["example_jp"]:
            card.add_row(t("example"), vocab["example_jp"])
            if get_lang() == "tr" and vocab["example_tr"]:
                card.add_row("", f"[dim]{vocab['example_tr']}[/dim]")
        # Extra examples
        try:
            extras = vocab["extra_examples"] or ""
        except (KeyError, IndexError):
            extras = ""
        if extras:
            import json as _json
            try:
                ex_list = _json.loads(extras) if isinstance(extras, str) else extras
                for i, ex in enumerate(ex_list):
                    card.add_row(f"{t('example')} {i+2}", ex.get("jp", ""))
                    if get_lang() == "tr" and ex.get("tr"):
                        card.add_row("", f"[dim]{ex['tr']}[/dim]")
                    elif ex.get("en"):
                        card.add_row("", f"[dim]{ex['en']}[/dim]")
            except (ValueError, TypeError):
                pass
        if vocab["part_of_speech"]:
            card.add_row(t("part_of_speech"), translate_pos(vocab["part_of_speech"]))
    else:
        card.add_row(t("meaning_label"), f"[dim italic]{t('press_enter')}[/dim italic]")

    console.print(card)


def show_kanji_card(kanji, show_answer=False):
    """Kanji kartini goster."""
    kanji_display = Text(kanji['kanji'], style="bold bright_white")

    card = Table(show_header=False, box=box.ROUNDED, border_style="blue", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    card.add_row(t("kanji"), kanji_display)

    if show_answer:
        card.add_row(t("on_yomi"), f"[bold magenta]{kanji['on_yomi']}[/bold magenta]")
        card.add_row(t("kun_yomi"), f"[bold green]{kanji['kun_yomi']}[/bold green]")
        _meaning_rows(kanji, card, card_type="kanji")
        card.add_row(t("stroke_count"), str(kanji["stroke_count"]))
        if kanji["compounds"]:
            card.add_row(t("compounds"), kanji["compounds"])
    else:
        card.add_row(t("meaning_label"), f"[dim italic]{t('press_enter')}[/dim italic]")

    console.print(card)


def show_grammar_card(grammar, show_answer=False):
    """Dilbilgisi kartini goster."""
    card = Table(show_header=False, box=box.ROUNDED, border_style="yellow", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    card.add_row(t("pattern"), f"[bold bright_white]{grammar['pattern']}[/bold bright_white]")
    card.add_row(t("level"), grammar["level"])

    if show_answer:
        _meaning_rows(grammar, card, card_type="grammar")
        if grammar["example_jp"]:
            card.add_row(t("example"), grammar["example_jp"])
            if get_lang() == "tr" and grammar["example_tr"]:
                card.add_row("", f"[dim]{grammar['example_tr']}[/dim]")
        if get_lang() == "tr" and grammar["notes"]:
            card.add_row(t("note"), f"[dim]{grammar['notes']}[/dim]")
    else:
        card.add_row(t("meaning_label"), f"[dim italic]{t('press_enter')}[/dim italic]")

    console.print(card)


def show_review_prompt(vocab_mode=False):
    """Karti degerlendirme seceneklerini goster.
    vocab_mode=True ise okuma/kanji ayrimi olan secenekleri goster."""
    console.print()
    options = Table(show_header=False, box=None, padding=(0, 1))
    options.add_column(style="bold")
    options.add_column()

    if vocab_mode:
        options.add_row("[red]1[/red]", t("review.forgot"))
        options.add_row("[yellow]2[/yellow]", t("review.know_reading"))
        options.add_row("[green]3[/green]", t("review.good"))
        options.add_row("[bold green]4[/bold green]", t("review.easy"))
    else:
        options.add_row("[red]1[/red]", t("review.forgot"))
        options.add_row("[yellow]2[/yellow]", t("review.hard"))
        options.add_row("[green]3[/green]", t("review.good"))
        options.add_row("[bold green]4[/bold green]", t("review.easy"))

    options.add_row("[cyan]s[/cyan]", t("review.skip"))
    options.add_row("[red]q[/red]", t("review.quit"))
    console.print(options)

    return Prompt.ask(t("review.rating"), choices=["1","2","3","4","s","q"], default="3")


def show_srs_feedback(quality, interval, weak_kanji=False):
    """Rating sonrasi SRS geri bildirimini goster."""
    if weak_kanji:
        console.print(f"\n  [yellow]{t('srs.weak_kanji_note')}[/yellow]")
    if quality < 3:
        console.print(f"  [red]{t('srs.repeat_tomorrow')}[/red]")
    elif interval == 1:
        console.print(f"  [yellow]{t('srs.next_tomorrow')}[/yellow]")
    elif interval <= 7:
        console.print(f"  [green]{t('srs.next_days', days=interval)}[/green]")
    else:
        console.print(f"  [bold green]{t('srs.next_days', days=interval)}[/bold green]")


def card_status_label(review):
    """Kart durum etiketi dondur."""
    if review is None:
        return f"[bright_cyan][{t('status.new')}][/bright_cyan]"
    weak = review["weak_kanji"] if "weak_kanji" in review.keys() else 0
    label = ""
    if review["repetitions"] == 0:
        label = f"[red][{t('status.repeat')}][/red]"
    elif review["interval"] < 7:
        label = f"[yellow][{t('status.learning')}][/yellow]"
    elif review["interval"] < 30:
        label = f"[green][{t('status.known')}][/green]"
    else:
        label = f"[bold green][{t('status.master')}][/bold green]"
    if weak:
        label += f" [yellow][{t('status.weak_kanji')}][/yellow]"
    return label


def show_vocab_list(level, items=None):
    """Kelime listesini goster. Listeyi dondurur."""
    vocabs = items if items is not None else db.get_vocabulary(level=level)
    if not vocabs:
        console.print(f"[yellow]{t('no_vocab_level')}[/yellow]")
        return []

    mf = meaning_field()
    table = Table(title=t("vocab_list_title", level=level), box=box.SIMPLE_HEAVY, border_style="magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column(t("word"), style="bold white")
    table.add_column(t("reading"), style="green")
    if get_lang() != "en":
        table.add_column(t("native_meaning"), style="yellow")
    table.add_column(t("english_meaning"), style="cyan")
    table.add_column(t("part_of_speech"), style="dim")

    for i, v in enumerate(vocabs, 1):
        native = (v[mf] or v["meaning_en"]) if get_lang() != "en" else None
        pos = translate_pos(v["part_of_speech"])
        if get_lang() != "en":
            table.add_row(str(i), v["word"], v["reading"], native, v["meaning_en"], pos)
        else:
            table.add_row(str(i), v["word"], v["reading"], v["meaning_en"], pos)

    console.print(table)
    return vocabs


def show_kanji_list(level, items=None):
    """Kanji listesini goster. Listeyi dondurur."""
    kanjis = items if items is not None else db.get_kanji(level=level)
    if not kanjis:
        console.print(f"[yellow]{t('no_kanji_level')}[/yellow]")
        return []

    mf = meaning_field()
    table = Table(title=t("kanji_list_title", level=level), box=box.SIMPLE_HEAVY, border_style="blue")
    table.add_column("#", style="dim", width=4)
    table.add_column(t("kanji"), style="bold white")
    table.add_column(t("on_yomi"), style="magenta")
    table.add_column(t("kun_yomi"), style="green")
    if get_lang() != "en":
        table.add_column(t("native_meaning"), style="yellow")
    table.add_column(t("english_meaning"), style="cyan")
    table.add_column(t("stroke_count"), style="dim", width=5)

    for i, k in enumerate(kanjis, 1):
        native = (k[mf] or k["meaning_en"]) if get_lang() != "en" else None
        if get_lang() != "en":
            table.add_row(str(i), k["kanji"], k["on_yomi"], k["kun_yomi"], native, k["meaning_en"], str(k["stroke_count"]))
        else:
            table.add_row(str(i), k["kanji"], k["on_yomi"], k["kun_yomi"], k["meaning_en"], str(k["stroke_count"]))

    console.print(table)
    return kanjis


def show_stats():
    """Istatistikleri goster."""
    clear()
    banner()

    total_vocab = db.count_vocabulary()
    total_kanji = db.count_kanji()
    learned_vocab = db.count_learned("vocabulary")
    learned_kanji = db.count_learned("kanji")
    learned_grammar = db.count_learned("grammar")
    due_total = db.count_due_reviews()

    general = Table(title=t("stats.title"), box=box.ROUNDED, border_style="green")
    general.add_column(t("stats.category"), style="cyan")
    general.add_column(t("stats.learned"), style="yellow", justify="right")
    general.add_column(t("stats.total"), style="white", justify="right")
    general.add_column(t("stats.rate"), style="green", justify="right")

    vocab_pct = f"{learned_vocab/total_vocab*100:.0f}%" if total_vocab > 0 else "—"
    kanji_pct = f"{learned_kanji/total_kanji*100:.0f}%" if total_kanji > 0 else "—"

    general.add_row(t("stats.vocabulary"), str(learned_vocab), str(total_vocab), vocab_pct)
    general.add_row(t("stats.kanji"), str(learned_kanji), str(total_kanji), kanji_pct)
    general.add_row(t("stats.grammar"), str(learned_grammar), "—", "—")
    general.add_row(t("stats.due_reviews"), str(due_total), "", "")

    console.print(general)
    console.print()

    # JLPT Hazirlik Skoru
    jlpt = Table(title=t("stats.jlpt_readiness"), box=box.ROUNDED, border_style="magenta")
    jlpt.add_column(t("level"), style="cyan")
    jlpt.add_column(t("stats.vocabulary"), justify="right")
    jlpt.add_column(t("stats.kanji"), justify="right")
    jlpt.add_column(t("stats.grammar"), justify="right")
    jlpt.add_column(t("stats.readiness"), justify="right", style="bold")

    for level in LEVELS:
        vc = db.count_vocabulary(level)
        kc = db.count_kanji(level)
        gc = db.count_grammar(level)
        lv = db.count_learned("vocabulary", level)
        lk = db.count_learned("kanji", level)
        lg = db.count_learned("grammar", level)

        v_pct = lv / vc * 100 if vc > 0 else 0
        k_pct = lk / kc * 100 if kc > 0 else 0
        g_pct = lg / gc * 100 if gc > 0 else 0

        # Agirlikli ortalama: vocab %50, kanji %30, grammar %20
        weights = []
        if vc > 0:
            weights.append((v_pct, 0.5))
        if kc > 0:
            weights.append((k_pct, 0.3))
        if gc > 0:
            weights.append((g_pct, 0.2))

        if weights:
            total_w = sum(w for _, w in weights)
            readiness = sum(p * w for p, w in weights) / total_w
        else:
            readiness = 0

        if readiness >= 80:
            r_style = "bold green"
        elif readiness >= 50:
            r_style = "yellow"
        else:
            r_style = "red"

        jlpt.add_row(
            level,
            f"{lv}/{vc}" if vc > 0 else "—",
            f"{lk}/{kc}" if kc > 0 else "—",
            f"{lg}/{gc}" if gc > 0 else "—",
            f"[{r_style}]{readiness:.0f}%[/{r_style}]"
        )

    console.print(jlpt)
    console.print()

    # --- Personal profile: kisinin ogrenme stilini cikar ---
    profile = db.get_personal_profile(min_answers=20)
    if profile.get("ready"):
        profile_table = Table(title=t("stats.profile_title"), box=box.ROUNDED, border_style="green")
        profile_table.add_column(t("stats.profile_attr"), style="cyan")
        profile_table.add_column(t("stats.profile_value"), style="white")

        profile_table.add_row(t("stats.profile_total"),
                              str(profile["total_answers"]))
        profile_table.add_row(t("stats.profile_days"),
                              str(profile["session_days"]))
        # Genel başarı - sözel
        acc = profile["overall_accuracy"]
        if acc >= 0.85: acc_label = t("profile.acc_excellent")
        elif acc >= 0.70: acc_label = t("profile.acc_good")
        elif acc >= 0.55: acc_label = t("profile.acc_fair")
        else: acc_label = t("profile.acc_struggle")
        profile_table.add_row(t("stats.profile_accuracy"), acc_label)

        # Velocity
        v = profile["learning_velocity"]
        v_label = t(f"profile.velocity.{v}")
        profile_table.add_row(t("stats.profile_velocity"), v_label)

        # Strengths
        if profile["strengths"]:
            strengths = ", ".join(t(f"diagnostic.skill.{s.replace('vocabulary','vocab')}")
                                  for s in profile["strengths"])
            profile_table.add_row(t("stats.profile_strengths"),
                                  f"[bold green]{strengths}[/bold green]")
        if profile["weaknesses"]:
            weaknesses = ", ".join(t(f"diagnostic.skill.{w.replace('vocabulary','vocab')}")
                                   for w in profile["weaknesses"])
            profile_table.add_row(t("stats.profile_weaknesses"),
                                  f"[bold yellow]{weaknesses}[/bold yellow]")

        # Best hour
        if profile["best_hour"] is not None:
            profile_table.add_row(t("stats.profile_best_hour"),
                                  t("profile.best_hour_format", hour=profile["best_hour"]))

        # Streak vurgu
        if profile["recent_streak"] >= 8:
            profile_table.add_row(t("stats.profile_streak"),
                                  f"[bold green]{profile['recent_streak']}/10 ✓[/bold green]")

        console.print(profile_table)
        console.print()
    elif profile.get("total_answers", 0) > 0:
        console.print(f"[dim italic]{t('stats.profile_warming_up', total=profile['total_answers'], needed=profile['needed'])}[/dim italic]\n")

    # --- Smart pattern detection: sik yapilan hatalar ---
    insights = db.get_pattern_insights(min_occurrences=3, top_n=5)
    if insights:
        pat_table = Table(title=t("stats.patterns_title"), box=box.ROUNDED, border_style="red")
        pat_table.add_column(t("stats.patterns_diag"), style="cyan")
        pat_table.add_column(t("stats.patterns_area"), style="white")
        pat_table.add_column(t("stats.patterns_count"), justify="right", style="bold yellow")
        pat_table.add_column("", style="dim")
        for ins in insights:
            # Diag etiketini insan-okur hale getirmeye calis
            diag_human = ins["diag"].replace("_", " ").capitalize()
            entity_labels = ", ".join(t(f"diagnostic.skill.{e.replace('vocabulary','vocab')}")
                                       for e in ins["entity_types"])
            recent_marker = "⚠ " + t("stats.patterns_recent") if ins["recent"] else ""
            pat_table.add_row(diag_human, entity_labels, str(ins["count"]), recent_marker)
        console.print(pat_table)
        console.print(f"[dim italic]{t('stats.patterns_hint')}[/dim italic]\n")

    # --- Forgetting curve: tekrar zamani gelmis item ozet ---
    decay_summary = db.get_decay_summary()
    if decay_summary.get("total", 0) > 0:
        decay_table = Table(title=t("stats.review_needed_title"), box=box.ROUNDED, border_style="yellow")
        decay_table.add_column(t("stats.category"), style="cyan")
        decay_table.add_column(t("stats.review_count"), justify="right", style="bold yellow")
        for et, label_key in (("vocabulary", "stats.vocabulary"),
                              ("kanji", "stats.kanji"),
                              ("grammar", "stats.grammar")):
            n = decay_summary.get(et, 0)
            if n > 0:
                decay_table.add_row(t(label_key), str(n))
        console.print(decay_table)
        console.print(f"[dim italic]{t('stats.review_needed_hint')}[/dim italic]\n")

    # --- Mastery / Adaptive Engine — sembolik (sayisal rating asla gosterilmez) ---
    summary = db.get_mastery_summary()
    has_any = any(summary["items"].get(t_) for t_ in ("vocabulary", "kanji", "grammar"))
    if has_any:
        from elo import stars_render
        elo_table = Table(title=t("stats.mastery_title"), box=box.ROUNDED, border_style="cyan")
        elo_table.add_column(t("stats.category"), style="cyan")
        elo_table.add_column(t("stats.skill_level"), style="bold yellow")
        elo_table.add_column(t("mastery.status.new"), justify="right", style="dim yellow")
        elo_table.add_column(t("mastery.status.learning"), justify="right", style="dim cyan")
        elo_table.add_column(t("mastery.status.mastered"), justify="right", style="bold green")
        rows = (("vocabulary", t("stats.vocabulary")),
                ("kanji", t("stats.kanji")),
                ("grammar", t("stats.grammar")))
        for et, label in rows:
            data = summary["items"].get(et)
            skill = summary["skills"].get(et, 1400)
            stars = stars_render(skill)
            if not data:
                elo_table.add_row(label, stars, "—", "—", "—")
                continue
            elo_table.add_row(
                label, stars,
                str(data["new"]), str(data["learning"]), str(data["mastered"]),
            )
        console.print(elo_table)
        console.print()

        # Per-lesson skill bar — kullanici hangi derste guclu/zayif goruyor
        lesson_skills = db.get_lesson_skills()
        if lesson_skills:
            lesson_tbl = Table(title=t("stats.lesson_mastery"), box=box.ROUNDED, border_style="magenta")
            lesson_tbl.add_column(t("textbook.lesson_no"), style="cyan")
            lesson_tbl.add_column(t("textbook.title"), style="white")
            lesson_tbl.add_column(t("stats.skill_level"), style="bold yellow")
            for entry in lesson_skills:
                lesson_tbl.add_row(
                    f"L{entry['lesson_no']}",
                    entry["title"],
                    stars_render(entry["rating"]),
                )
            console.print(lesson_tbl)
            console.print()

    stats = db.get_stats(7)
    if stats:
        daily = Table(title=t("stats.last_7_days"), box=box.ROUNDED, border_style="yellow")
        daily.add_column(t("stats.date"), style="cyan")
        daily.add_column(t("stats.studied"), justify="right")
        daily.add_column(t("stats.correct"), justify="right", style="green")
        daily.add_column(t("stats.new"), justify="right", style="blue")
        daily.add_column(t("stats.duration"), justify="right", style="dim")

        for s in stats:
            mins = s["study_seconds"] // 60
            daily.add_row(
                s["date"],
                str(s["cards_reviewed"]),
                str(s["cards_correct"]),
                str(s["cards_new"]),
                t("stats.minutes", mins=mins)
            )
        console.print(daily)
    else:
        console.print(f"[dim]{t('stats.no_data')}[/dim]")

    console.print()
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def show_quiz_menu():
    clear()
    banner()
    console.print(f"\n[bold]{t('quiz.select_mode')}[/bold]")
    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("", style="white")

    menu.add_row("1", f"[bold yellow]{t('quiz.jlpt_mock')}[/bold yellow]")
    menu.add_row("2", f"[bold yellow]{t('quiz.genki_lesson')}[/bold yellow]")
    menu.add_row("3", t("quiz.jp_to_native"))
    menu.add_row("4", t("quiz.native_to_jp"))
    menu.add_row("5", t("quiz.kanji_reading"))
    menu.add_row("6", t("quiz.kanji_meaning"))
    menu.add_row("7", t("quiz.sentence_order"))
    menu.add_row("8", t("quiz.conjugation"))
    menu.add_row("0", t("back"))

    console.print(menu)
    return Prompt.ask(t("your_choice"),
                      choices=["0","1","2","3","4","5","6","7","8"], default="1")


def show_search_results(results):
    """Arama sonuclarini kategorilere gore goster. Returns list of (item, type) tuples for selection."""
    mf = meaning_field()
    all_items = []
    idx = 1

    if results["vocabulary"]:
        table = Table(title=t("search.vocab_results"), box=box.SIMPLE_HEAVY, border_style="magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column(t("word"), style="bold white")
        table.add_column(t("reading"), style="green")
        if get_lang() != "en":
            table.add_column(t("native_meaning"), style="yellow")
        table.add_column(t("english_meaning"), style="cyan")
        table.add_column(t("level"), style="cyan", width=5)
        for v in results["vocabulary"]:
            if get_lang() != "en":
                table.add_row(str(idx), v["word"], v["reading"], v[mf] or v["meaning_en"], v["meaning_en"], v["level"])
            else:
                table.add_row(str(idx), v["word"], v["reading"], v["meaning_en"], v["level"])
            all_items.append((v, "vocab"))
            idx += 1
        console.print(table)
        console.print()

    if results["kanji"]:
        table = Table(title=t("search.kanji_results"), box=box.SIMPLE_HEAVY, border_style="blue")
        table.add_column("#", style="dim", width=4)
        table.add_column(t("kanji"), style="bold white")
        table.add_column(t("on_yomi"), style="magenta")
        table.add_column(t("kun_yomi"), style="green")
        if get_lang() != "en":
            table.add_column(t("native_meaning"), style="yellow")
        table.add_column(t("english_meaning"), style="cyan")
        table.add_column(t("level"), style="cyan", width=5)
        for k in results["kanji"]:
            if get_lang() != "en":
                table.add_row(str(idx), k["kanji"], k["on_yomi"], k["kun_yomi"], k[mf] or k["meaning_en"], k["meaning_en"], k["level"])
            else:
                table.add_row(str(idx), k["kanji"], k["on_yomi"], k["kun_yomi"], k["meaning_en"], k["level"])
            all_items.append((k, "kanji"))
            idx += 1
        console.print(table)
        console.print()

    if results["grammar"]:
        table = Table(title=t("search.grammar_results"), box=box.SIMPLE_HEAVY, border_style="yellow")
        table.add_column("#", style="dim", width=4)
        table.add_column(t("pattern"), style="bold white")
        if get_lang() != "en":
            table.add_column(t("native_meaning"), style="yellow")
        table.add_column(t("english_meaning"), style="cyan")
        table.add_column(t("level"), style="cyan", width=5)
        for g in results["grammar"]:
            if get_lang() != "en":
                table.add_row(str(idx), g["pattern"], g[mf] or g["meaning_en"], g["meaning_en"], g["level"])
            else:
                table.add_row(str(idx), g["pattern"], g["meaning_en"], g["level"])
            all_items.append((g, "grammar"))
            idx += 1
        console.print(table)
        console.print()

    if not all_items:
        console.print(f"[yellow]{t('search.no_results')}[/yellow]\n")

    return all_items


def show_settings_menu():
    """Ayarlar alt menusunu goster."""
    clear()
    banner()
    console.print(f"\n[bold]{t('settings.title')}[/bold]\n")
    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("", style="white")

    menu.add_row("1", t("settings.anki_export"))
    menu.add_row("2", t("settings.backup"))
    menu.add_row("3", t("settings.restore"))
    menu.add_row("4", t("settings.change_language"))
    menu.add_row("5", t("settings.download_audio"))
    menu.add_row("6", t("settings.card_limit"))
    menu.add_row("0", t("back"))

    console.print(menu)
    return Prompt.ask(t("your_choice"), choices=["0", "1", "2", "3", "4", "5", "6"], default="0")


def show_quiz_result(correct, total):
    console.print()
    pct = correct / total * 100 if total > 0 else 0
    if pct >= 80:
        style = "bold green"
        msg = t("quiz.result_great")
    elif pct >= 60:
        style = "bold yellow"
        msg = t("quiz.result_good")
    else:
        style = "bold red"
        msg = t("quiz.result_study_more")

    result = Panel(
        f"[{style}]{t('quiz.result_text', correct=correct, total=total, pct=f'{pct:.0f}', msg=msg)}[/{style}]",
        title=f"[bold]{t('quiz.result_title')}[/bold]",
        border_style="cyan"
    )
    console.print(result)


TEXTBOOK_TITLES = {
    "genki1": "Genki I",
}


def show_textbook_level_select():
    """Ders kitabı bulunan level'ları listele (N5/N4/...). Tek varsa otomatik seç."""
    clear()
    banner()
    console.print(f"\n[bold]{t('textbook.select_level_title')}[/bold]\n")

    by_level = db.get_textbook_levels()
    if not by_level:
        console.print(f"[yellow]{t('textbook.none')}[/yellow]")
        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")
        return None

    available = [lv for lv in LEVELS if lv in by_level]
    if len(available) == 1:
        return available[0]

    for i, lv in enumerate(available, 1):
        console.print(f"  [cyan]{i}[/cyan] - {lv}  [dim]({by_level[lv]} {t('textbook.lessons').lower()})[/dim]")
    console.print(f"  [cyan]0[/cyan] - {t('back')}")

    choices = ["0"] + [str(i) for i in range(1, len(available) + 1)]
    choice = Prompt.ask(t("your_choice"), choices=choices, default="1")
    if choice == "0":
        return None
    return available[int(choice) - 1]


def show_lesson_select(level):
    """Bir level'daki tüm dersleri (kitaplara göre) listele."""
    clear()
    banner()
    console.print(f"\n[bold]{level} — {t('textbook.lessons')}[/bold]\n")

    lessons = db.get_lessons(level=level)
    if not lessons:
        console.print(f"[yellow]{t('textbook.no_lessons')}[/yellow]")
        Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")
        return None

    textbooks = sorted({l["textbook"] for l in lessons})
    show_textbook_col = len(textbooks) > 1

    table = Table(box=box.SIMPLE, padding=(0, 1))
    table.add_column("#", style="bold cyan", width=4)
    if show_textbook_col:
        table.add_column(t("textbook.book"), style="magenta")
    table.add_column(t("textbook.lesson_no"), style="cyan", width=4)
    table.add_column(t("textbook.title"), style="white")
    table.add_column(t("textbook.title_ja"), style="yellow")
    table.add_column(t("textbook.progress"), style="green", justify="right")

    for i, lesson in enumerate(lessons, 1):
        prog = db.get_lesson_progress(lesson["id"])
        if prog["total"] > 0:
            pct = int(100 * prog["learned"] / prog["total"])
            prog_str = f"{prog['learned']}/{prog['total']} ({pct}%)"
        else:
            prog_str = "—"
        row = [str(i)]
        if show_textbook_col:
            row.append(TEXTBOOK_TITLES.get(lesson["textbook"], lesson["textbook"]))
        row += [f"L{lesson['lesson_no']}", lesson["title"], lesson.get("title_ja", ""), prog_str]
        table.add_row(*row)

    console.print(table)
    if not show_textbook_col and textbooks:
        console.print(f"\n[dim]{t('textbook.book')}: {TEXTBOOK_TITLES.get(textbooks[0], textbooks[0])}[/dim]")
    console.print(f"\n  [cyan]0[/cyan] - {t('back')}")

    choice = Prompt.ask(f"\n[bold cyan]{t('textbook.pick_lesson')}[/bold cyan]", default="0")
    if not choice.isdigit():
        return None
    idx = int(choice)
    if idx == 0 or idx > len(lessons):
        return None
    return lessons[idx - 1]["id"]


def show_lesson_detail_menu(lesson_id):
    """Seçilen ders için: vocab/grammar/kanji çalış veya sınav."""
    clear()
    banner()
    lesson = db.get_lesson(lesson_id)
    items = db.get_lesson_items(lesson_id)
    v_count = len(items["vocabulary"])
    g_count = len(items["grammar"])
    k_count = len(items["kanji"])

    header = Text()
    header.append(f"L{lesson['lesson_no']}: ", style="bold cyan")
    header.append(lesson["title"], style="bold white")
    if lesson.get("title_ja"):
        header.append(f"  〜 {lesson['title_ja']}", style="yellow")
    console.print(Panel(header, border_style="cyan"))
    console.print()

    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column(style="cyan")
    info.add_column(style="white", justify="right")
    info.add_row(t("textbook.vocab_count"), str(v_count))
    info.add_row(t("textbook.grammar_count"), str(g_count))
    info.add_row(t("textbook.kanji_count"), str(k_count))
    console.print(info)
    console.print()

    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column(t("your_choice"), style="white")

    menu.add_row("1", f"[bold green]{t('textbook.guided')}[/bold green]")
    menu.add_row("2", f"[bold magenta]{t('textbook.diagnostic_quiz')}[/bold magenta]")
    menu.add_row("3", t("textbook.study_vocab"))
    menu.add_row("4", t("textbook.study_grammar"))
    menu.add_row("5", t("textbook.study_kanji"))
    menu.add_row("6", t("textbook.lesson_exam"))
    menu.add_row("0", t("back"))

    console.print(Panel(menu, title=f"[bold]{t('textbook.lesson_actions')}[/bold]", border_style="green"))
    return Prompt.ask(f"\n[bold cyan]{t('your_choice')}[/bold cyan]",
                      choices=["0", "1", "2", "3", "4", "5", "6"], default="1")


def show_startup_level_select():
    """İlk açılışta veya kullanıcı değiştirmek isterse seviye seçimi.
    Aktif olmayan seviyeler 'yakında' rozetiyle gösterilir, seçilemez."""
    from i18n import ALL_LEVELS, ACTIVE_LEVELS
    clear()
    banner()
    console.print(f"\n[bold]{t('startup.choose_level_title')}[/bold]")
    console.print(f"[dim]{t('startup.choose_level_prompt')}[/dim]\n")

    selectable_indices = []
    for i, lv in enumerate(ALL_LEVELS, 1):
        if lv in ACTIVE_LEVELS:
            console.print(f"  [cyan]{i}[/cyan] - [bold]{lv}[/bold]")
            selectable_indices.append(str(i))
        else:
            console.print(f"  [dim]{i} - {lv}  ({t('startup.coming_soon')})[/dim]")

    default = selectable_indices[0]
    choice = Prompt.ask(f"\n[bold cyan]{t('your_choice')}[/bold cyan]",
                        choices=selectable_indices, default=default)
    return ALL_LEVELS[int(choice) - 1]


def show_language_select():
    """Dil secim ekranini goster."""
    from i18n import LANGUAGES, get_lang
    clear()
    banner()
    console.print(f"\n[bold]{t('lang.select_title')}[/bold]\n")

    langs = list(LANGUAGES.items())
    # Find default index based on current (system-detected) language
    current = get_lang()
    default_idx = "1"
    for i, (code, _name) in enumerate(langs, 1):
        if code == current:
            default_idx = str(i)
            break

    for i, (code, name) in enumerate(langs, 1):
        marker = " *" if str(i) == default_idx else ""
        console.print(f"  [cyan]{i}[/cyan] - {name}{marker}")

    choices = [str(i) for i in range(1, len(langs) + 1)]
    choice = Prompt.ask(t("lang.select_prompt"), choices=choices, default=default_idx)
    selected_code = langs[int(choice) - 1][0]
    return selected_code
