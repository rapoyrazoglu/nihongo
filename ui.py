"""Rich terminal arayüzü - Nihongo öğrenme uygulaması."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.prompt import Prompt, IntPrompt
from rich import box
import db

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
    info_table.add_row("Bekleyen tekrar:", f"[bold yellow]{due}[/bold yellow] kart")
    if today:
        info_table.add_row("Bugün çalışılan:", f"{today['cards_reviewed']} kart")
        info_table.add_row("Doğruluk:", f"{today['cards_correct']}/{today['cards_reviewed']}" if today['cards_reviewed'] > 0 else "—")
    else:
        info_table.add_row("Bugün çalışılan:", "0 kart")

    console.print(Panel(info_table, title="[bold]Günlük Özet[/bold]", border_style="blue"))
    console.print()

    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("Seçenek", style="white")
    menu.add_column("Açıklama", style="dim")

    menu.add_row("1", "Kelime Çalış", "Kelime kartları ile SRS tekrarı")
    menu.add_row("2", "Kanji Çalış", "Kanji kartları ile SRS tekrarı")
    menu.add_row("3", "Dilbilgisi Çalış", "Gramer noktaları tekrarı")
    menu.add_row("4", "Quiz", "Test modları (JP↔TR, Kanji okuma)")
    menu.add_row("5", "Kelime Listesi", "Tüm kelimeleri göster")
    menu.add_row("6", "Kanji Listesi", "Tüm kanjileri göster")
    menu.add_row("7", "İstatistikler", "İlerleme ve istatistikler")
    menu.add_row("8", "Ayarlar", "Seviye ve günlük hedef")
    menu.add_row("0", "Çıkış", "Programdan çık")

    console.print(Panel(menu, title="[bold]Ana Menü[/bold]", border_style="green"))

    return Prompt.ask("\n[bold cyan]Seçiminiz[/bold cyan]", choices=["0","1","2","3","4","5","6","7","8"], default="1")


def show_level_select(title="Seviye Seçin"):
    console.print(f"\n[bold]{title}[/bold]")
    for i, level in enumerate(LEVELS, 1):
        count_v = db.count_vocabulary(level)
        count_k = db.count_kanji(level)
        console.print(f"  [cyan]{i}[/cyan] - {level} (Kelime: {count_v}, Kanji: {count_k})")
    console.print(f"  [cyan]0[/cyan] - Geri")

    choice = Prompt.ask("Seviye", choices=["0","1","2","3","4","5"], default="1")
    if choice == "0":
        return None
    return LEVELS[int(choice) - 1]


def show_vocab_card(vocab, show_answer=False):
    """Kelime kartını göster."""
    card = Table(show_header=False, box=box.ROUNDED, border_style="magenta", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    card.add_row("Kelime", f"[bold bright_white]{vocab['word']}[/bold bright_white]")
    card.add_row("Okuma", f"[bold green]{vocab['reading']}[/bold green]")

    if show_answer:
        card.add_row("Türkçe", f"[bold yellow]{vocab['meaning_tr']}[/bold yellow]")
        card.add_row("İngilizce", vocab["meaning_en"])
        if vocab["example_jp"]:
            card.add_row("Örnek", vocab["example_jp"])
            if vocab["example_tr"]:
                card.add_row("", f"[dim]{vocab['example_tr']}[/dim]")
        if vocab["part_of_speech"]:
            card.add_row("Tür", vocab["part_of_speech"])
    else:
        card.add_row("Anlam", "[dim italic]Enter'a basarak göster...[/dim italic]")

    console.print(card)


def show_kanji_card(kanji, show_answer=False):
    """Kanji kartını göster."""
    kanji_display = Text(kanji['kanji'], style="bold bright_white")

    card = Table(show_header=False, box=box.ROUNDED, border_style="blue", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    card.add_row("Kanji", kanji_display)

    if show_answer:
        card.add_row("On'yomi", f"[bold magenta]{kanji['on_yomi']}[/bold magenta]")
        card.add_row("Kun'yomi", f"[bold green]{kanji['kun_yomi']}[/bold green]")
        card.add_row("Türkçe", f"[bold yellow]{kanji['meaning_tr']}[/bold yellow]")
        card.add_row("İngilizce", kanji["meaning_en"])
        card.add_row("Çizgi sayısı", str(kanji["stroke_count"]))
        if kanji["compounds"]:
            card.add_row("Bileşikler", kanji["compounds"])
    else:
        card.add_row("Anlam", "[dim italic]Enter'a basarak göster...[/dim italic]")

    console.print(card)


def show_grammar_card(grammar, show_answer=False):
    """Dilbilgisi kartını göster."""
    card = Table(show_header=False, box=box.ROUNDED, border_style="yellow", width=60)
    card.add_column("key", style="bold cyan", width=15)
    card.add_column("value", style="white")

    card.add_row("Kalıp", f"[bold bright_white]{grammar['pattern']}[/bold bright_white]")
    card.add_row("Seviye", grammar["level"])

    if show_answer:
        card.add_row("Türkçe", f"[bold yellow]{grammar['meaning_tr']}[/bold yellow]")
        card.add_row("İngilizce", grammar["meaning_en"])
        if grammar["example_jp"]:
            card.add_row("Örnek", grammar["example_jp"])
            if grammar["example_tr"]:
                card.add_row("", f"[dim]{grammar['example_tr']}[/dim]")
        if grammar["notes"]:
            card.add_row("Not", f"[dim]{grammar['notes']}[/dim]")
    else:
        card.add_row("Anlam", "[dim italic]Enter'a basarak göster...[/dim italic]")

    console.print(card)


def show_review_prompt():
    """Kartı değerlendirme seçeneklerini göster."""
    console.print()
    options = Table(show_header=False, box=None, padding=(0, 1))
    options.add_column(style="bold")
    options.add_column()
    options.add_row("[red]1[/red]", "Hiç bilmiyorum (tekrar)")
    options.add_row("[yellow]2[/yellow]", "Zor hatırladım")
    options.add_row("[green]3[/green]", "Bildim")
    options.add_row("[bold green]4[/bold green]", "Çok kolaydı")
    options.add_row("[cyan]s[/cyan]", "Atla")
    options.add_row("[red]q[/red]", "Çalışmayı bitir")
    console.print(options)

    return Prompt.ask("Değerlendirme", choices=["1","2","3","4","s","q"], default="3")


def show_srs_feedback(quality, interval):
    """Rating sonrası SRS geri bildirimini göster."""
    if quality < 3:
        console.print(f"\n  [red]Tekrar yarın[/red]")
    elif interval == 1:
        console.print(f"\n  [yellow]Sonraki tekrar: yarın[/yellow]")
    elif interval <= 7:
        console.print(f"\n  [green]Sonraki tekrar: {interval} gün sonra[/green]")
    else:
        console.print(f"\n  [bold green]Sonraki tekrar: {interval} gün sonra[/bold green]")


def card_status_label(review):
    """Kart durum etiketi döndür."""
    if review is None:
        return "[bright_cyan][Yeni][/bright_cyan]"
    if review["repetitions"] == 0:
        return "[red][Tekrar][/red]"
    if review["interval"] < 7:
        return "[yellow][Öğreniyor][/yellow]"
    if review["interval"] < 30:
        return "[green][Biliyor][/green]"
    return "[bold green][Usta][/bold green]"


def show_vocab_list(level):
    """Kelime listesini göster."""
    vocabs = db.get_vocabulary(level=level)
    if not vocabs:
        console.print("[yellow]Bu seviyede kelime yok.[/yellow]")
        return

    table = Table(title=f"{level} Kelime Listesi", box=box.SIMPLE_HEAVY, border_style="magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Kelime", style="bold white")
    table.add_column("Okuma", style="green")
    table.add_column("Türkçe", style="yellow")
    table.add_column("İngilizce", style="white")
    table.add_column("Tür", style="dim")

    for i, v in enumerate(vocabs, 1):
        table.add_row(str(i), v["word"], v["reading"], v["meaning_tr"], v["meaning_en"], v["part_of_speech"])

    console.print(table)


def show_kanji_list(level):
    """Kanji listesini göster."""
    kanjis = db.get_kanji(level=level)
    if not kanjis:
        console.print("[yellow]Bu seviyede kanji yok.[/yellow]")
        return

    table = Table(title=f"{level} Kanji Listesi", box=box.SIMPLE_HEAVY, border_style="blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Kanji", style="bold white")
    table.add_column("On'yomi", style="magenta")
    table.add_column("Kun'yomi", style="green")
    table.add_column("Türkçe", style="yellow")
    table.add_column("Çizgi", style="dim", width=5)

    for i, k in enumerate(kanjis, 1):
        table.add_row(str(i), k["kanji"], k["on_yomi"], k["kun_yomi"], k["meaning_tr"], str(k["stroke_count"]))

    console.print(table)


def show_stats():
    """İstatistikleri göster."""
    clear()
    banner()

    # Genel istatistikler
    total_vocab = db.count_vocabulary()
    total_kanji = db.count_kanji()
    learned_vocab = db.count_learned("vocabulary")
    learned_kanji = db.count_learned("kanji")
    learned_grammar = db.count_learned("grammar")
    due_total = db.count_due_reviews()

    general = Table(title="Genel İlerleme", box=box.ROUNDED, border_style="green")
    general.add_column("Kategori", style="cyan")
    general.add_column("Öğrenilen", style="yellow", justify="right")
    general.add_column("Toplam", style="white", justify="right")
    general.add_column("Oran", style="green", justify="right")

    vocab_pct = f"{learned_vocab/total_vocab*100:.0f}%" if total_vocab > 0 else "—"
    kanji_pct = f"{learned_kanji/total_kanji*100:.0f}%" if total_kanji > 0 else "—"

    general.add_row("Kelime", str(learned_vocab), str(total_vocab), vocab_pct)
    general.add_row("Kanji", str(learned_kanji), str(total_kanji), kanji_pct)
    general.add_row("Dilbilgisi", str(learned_grammar), "—", "—")
    general.add_row("Bekleyen Tekrar", str(due_total), "", "")

    console.print(general)
    console.print()

    # Seviye bazında
    level_table = Table(title="Seviye Bazında", box=box.ROUNDED, border_style="blue")
    level_table.add_column("Seviye", style="cyan")
    level_table.add_column("Kelime", justify="right")
    level_table.add_column("Kanji", justify="right")

    for level in LEVELS:
        vc = db.count_vocabulary(level)
        kc = db.count_kanji(level)
        level_table.add_row(level, str(vc), str(kc))

    console.print(level_table)
    console.print()

    # Son 7 gün
    stats = db.get_stats(7)
    if stats:
        daily = Table(title="Son 7 Gün", box=box.ROUNDED, border_style="yellow")
        daily.add_column("Tarih", style="cyan")
        daily.add_column("Çalışılan", justify="right")
        daily.add_column("Doğru", justify="right", style="green")
        daily.add_column("Yeni", justify="right", style="blue")
        daily.add_column("Süre", justify="right", style="dim")

        for s in stats:
            mins = s["study_seconds"] // 60
            daily.add_row(
                s["date"],
                str(s["cards_reviewed"]),
                str(s["cards_correct"]),
                str(s["cards_new"]),
                f"{mins} dk"
            )
        console.print(daily)
    else:
        console.print("[dim]Henüz çalışma verisi yok.[/dim]")

    console.print()
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def show_quiz_menu():
    console.print("\n[bold]Quiz Modu Seçin[/bold]")
    menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    menu.add_column("No", style="bold cyan", width=4)
    menu.add_column("Mod", style="white")

    menu.add_row("1", "Japonca → Türkçe (Kelime anlamı)")
    menu.add_row("2", "Türkçe → Japonca (Kelime yazma)")
    menu.add_row("3", "Kanji → Okuma (Kanji okuma)")
    menu.add_row("4", "Kanji → Anlam (Kanji anlamı)")
    menu.add_row("0", "Geri")

    console.print(menu)
    return Prompt.ask("Seçiminiz", choices=["0","1","2","3","4"], default="1")


def show_quiz_result(correct, total):
    console.print()
    pct = correct / total * 100 if total > 0 else 0
    if pct >= 80:
        style = "bold green"
        msg = "Harika!"
    elif pct >= 60:
        style = "bold yellow"
        msg = "İyi!"
    else:
        style = "bold red"
        msg = "Daha çok çalışmalısın!"

    result = Panel(
        f"[{style}]{correct}/{total} doğru ({pct:.0f}%) - {msg}[/{style}]",
        title="[bold]Quiz Sonucu[/bold]",
        border_style="cyan"
    )
    console.print(result)
