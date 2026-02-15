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
    title = Text()
    title.append("日本語", style="bold red")
    title.append(" マスター ", style="bold white")
    title.append("〜 Nihongo Master 〜", style="bold yellow")
    console.print(Panel(title, border_style="red", box=box.DOUBLE))


def show_main_menu():
    clear()
    banner()

    today = db.get_today_stats()
    due = db.count_due_reviews()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="cyan")
    info_table.add_column(style="white")
    info_table.add_row(t("due_reviews"), f"[bold yellow]{due}[/bold yellow] {t('cards')}")
    if today:
        info_table.add_row(t("today_studied"), f"{today['cards_reviewed']} {t('cards')}")
        info_table.add_row(t("accuracy"), f"{today['cards_correct']}/{today['cards_reviewed']}" if today['cards_reviewed'] > 0 else "—")
    else:
        info_table.add_row(t("today_studied"), f"0 {t('cards')}")

    console.print(Panel(info_table, title=f"[bold]{t('daily_summary')}[/bold]", border_style="blue"))
    console.print()

    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column(t("your_choice"), style="white")
    menu.add_column("", style="dim")

    menu.add_row("1", t("menu.study_vocab"), t("menu.study_vocab_desc"))
    menu.add_row("2", t("menu.study_kanji"), t("menu.study_kanji_desc"))
    menu.add_row("3", t("menu.study_grammar"), t("menu.study_grammar_desc"))
    menu.add_row("4", t("menu.quiz"), t("menu.quiz_desc"))
    menu.add_row("5", t("menu.vocab_list"), t("menu.vocab_list_desc"))
    menu.add_row("6", t("menu.kanji_list"), t("menu.kanji_list_desc"))
    menu.add_row("7", t("menu.stats"), t("menu.stats_desc"))
    menu.add_row("8", t("menu.settings"), t("menu.settings_desc"))
    menu.add_row("9", t("menu.search"), t("menu.search_desc"))
    menu.add_row("0", t("menu.exit"), t("menu.exit_desc"))

    console.print(Panel(menu, title=f"[bold]{t('main_menu')}[/bold]", border_style="green"))

    return Prompt.ask(f"\n[bold cyan]{t('your_choice')}[/bold cyan]", choices=["0","1","2","3","4","5","6","7","8","9"], default="1")


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


def show_vocab_card(vocab, show_answer=False):
    """Kelime kartini goster."""
    card = Table(show_header=False, box=box.ROUNDED, border_style="magenta", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

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


def show_review_prompt():
    """Karti degerlendirme seceneklerini goster."""
    console.print()
    options = Table(show_header=False, box=None, padding=(0, 1))
    options.add_column(style="bold")
    options.add_column()
    options.add_row("[red]1[/red]", t("review.forgot"))
    options.add_row("[yellow]2[/yellow]", t("review.hard"))
    options.add_row("[green]3[/green]", t("review.good"))
    options.add_row("[bold green]4[/bold green]", t("review.easy"))
    options.add_row("[cyan]s[/cyan]", t("review.skip"))
    options.add_row("[red]q[/red]", t("review.quit"))
    console.print(options)

    return Prompt.ask(t("review.rating"), choices=["1","2","3","4","s","q"], default="3")


def show_srs_feedback(quality, interval):
    """Rating sonrasi SRS geri bildirimini goster."""
    if quality < 3:
        console.print(f"\n  [red]{t('srs.repeat_tomorrow')}[/red]")
    elif interval == 1:
        console.print(f"\n  [yellow]{t('srs.next_tomorrow')}[/yellow]")
    elif interval <= 7:
        console.print(f"\n  [green]{t('srs.next_days', days=interval)}[/green]")
    else:
        console.print(f"\n  [bold green]{t('srs.next_days', days=interval)}[/bold green]")


def card_status_label(review):
    """Kart durum etiketi dondur."""
    if review is None:
        return f"[bright_cyan][{t('status.new')}][/bright_cyan]"
    if review["repetitions"] == 0:
        return f"[red][{t('status.repeat')}][/red]"
    if review["interval"] < 7:
        return f"[yellow][{t('status.learning')}][/yellow]"
    if review["interval"] < 30:
        return f"[green][{t('status.known')}][/green]"
    return f"[bold green][{t('status.master')}][/bold green]"


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

    level_table = Table(title=t("stats.by_level"), box=box.ROUNDED, border_style="blue")
    level_table.add_column(t("level"), style="cyan")
    level_table.add_column(t("stats.vocabulary"), justify="right")
    level_table.add_column(t("stats.kanji"), justify="right")

    for level in LEVELS:
        vc = db.count_vocabulary(level)
        kc = db.count_kanji(level)
        level_table.add_row(level, str(vc), str(kc))

    console.print(level_table)
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
    console.print(f"\n[bold]{t('quiz.select_mode')}[/bold]")
    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("", style="white")

    menu.add_row("1", t("quiz.jp_to_native"))
    menu.add_row("2", t("quiz.native_to_jp"))
    menu.add_row("3", t("quiz.kanji_reading"))
    menu.add_row("4", t("quiz.kanji_meaning"))
    menu.add_row("0", t("back"))

    console.print(menu)
    return Prompt.ask(t("your_choice"), choices=["0","1","2","3","4"], default="1")


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
    console.print(f"\n[bold]{t('settings.title')}[/bold]\n")
    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("", style="white")

    menu.add_row("1", t("settings.anki_export"))
    menu.add_row("2", t("settings.backup"))
    menu.add_row("3", t("settings.restore"))
    menu.add_row("4", t("settings.change_language"))
    menu.add_row("5", t("settings.download_audio"))
    menu.add_row("0", t("back"))

    console.print(menu)
    return Prompt.ask(t("your_choice"), choices=["0", "1", "2", "3", "4", "5"], default="0")


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
