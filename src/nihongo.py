#!/usr/bin/env python3
"""日本語マスター - JLPT Japonca Ogrenme Uygulamasi.

Kullanim:
    python nihongo.py            # Ana menuyu baslat
    python nihongo.py --init     # Veritabanini sifirdan olustur
    python nihongo.py --stats    # Istatistikleri goster
    python nihongo.py --version  # Surum bilgisi
    python nihongo.py --update        # En son surume guncelle
    python nihongo.py --update-beta   # Beta dahil en son surume guncelle
    python nihongo.py --delete        # Uygulamayi kaldir
"""

import sys
import os
import shutil

# --- Windows: force UTF-8 stdout/stderr so Turkish chars don't crash on cp1252 ---
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

# --- Frozen guard (PyInstaller) ---
if getattr(sys, "frozen", False):
    import multiprocessing
    multiprocessing.freeze_support()

# Proje dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Auto-install rich (sadece source modda) ---
if not getattr(sys, "frozen", False):
    try:
        import rich  # noqa: F401
    except ImportError:
        print("'rich' kutuphanesi bulunamadi, yukleniyor...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich>=13.0"])
        os.execv(sys.executable, [sys.executable] + sys.argv)

from version import __version__
from paths import DB_PATH

# --- --version flag ---
if "--version" in sys.argv:
    print(f"nihongo {__version__}")
    sys.exit(0)

import i18n
from i18n import t, set_lang

# --- --update flag ---
if "--update-beta" in sys.argv:
    i18n.init()
    from updater import do_update
    do_update(include_beta=True)
    sys.exit(0)
if "--update" in sys.argv:
    i18n.init()
    from updater import do_update
    do_update()
    sys.exit(0)
if "--delete" in sys.argv:
    i18n.init()
    from updater import do_uninstall
    do_uninstall()
    sys.exit(0)

import db
from ui import console, show_main_menu, show_vocab_list, show_kanji_list, show_vocab_card, show_kanji_card, show_grammar_card, show_stats, show_quiz_menu, show_search_results, show_settings_menu, show_language_select, show_startup_level_select, show_lesson_select, show_lesson_detail_menu, clear, banner
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import quiz


def migrate_old_db():
    """Eski ./nihongo.db varsa ~/.local/share/nihongo/ altina kopyala."""
    old_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nihongo.db")
    if os.path.exists(old_db) and not os.path.exists(DB_PATH):
        print(f"Eski veritabani bulundu, tasiniyor: {old_db} -> {DB_PATH}")
        shutil.copy2(old_db, DB_PATH)


def ensure_db():
    """Veritabani yoksa olustur ve seed et."""
    migrate_old_db()
    if not os.path.exists(DB_PATH):
        console.print(f"[yellow]{t('db.not_found')}[/yellow]")
        from data.init_db import main as init_main
        init_main()
        console.print(f"[green]{t('db.ready')}[/green]\n")
    else:
        db.init_db()
        from data.init_db import (migrate_grammar_unique, seed_vocabulary, seed_kanji,
                                  seed_grammar, migrate_extra_examples, update_extra_examples,
                                  migrate_meanings, update_meanings, seed_genki1)
        migrate_meanings()
        migrate_extra_examples()
        migrate_grammar_unique()
        seed_vocabulary()
        seed_kanji()
        seed_grammar()
        seed_genki1()
        update_extra_examples()
        update_meanings()


def _current_level():
    """Yapılandırılmış aktif seviye (config.json'dan); zaten ensure_level_selected() ile garanti."""
    from i18n import get_level, ACTIVE_LEVELS
    lv = get_level()
    return lv if lv in ACTIVE_LEVELS else ACTIVE_LEVELS[0]


def handle_study_vocab():
    quiz.study_vocabulary(_current_level())


def handle_study_kanji():
    quiz.study_kanji(_current_level())


def handle_study_grammar():
    quiz.study_grammar(_current_level())


def handle_quiz():
    mode = show_quiz_menu()
    if mode == "0":
        return

    level = _current_level()

    if mode == "1":
        # JLPT mock exam
        import exam_jlpt
        exam_jlpt.run_jlpt_exam(level)
        return

    if mode == "2":
        # Genki lesson cumulative exam
        from ui import show_lesson_select
        import exam_genki
        lesson_id = show_lesson_select(level)
        if lesson_id is None:
            return
        exam_genki.run_genki_lesson_exam(level, lesson_id)
        return

    count = IntPrompt.ask(t("quiz.question_count"), default=10)
    if mode == "3":
        quiz.quiz_jp_to_tr(level, count)
    elif mode == "4":
        quiz.quiz_tr_to_jp(level, count)
    elif mode == "5":
        quiz.quiz_kanji_reading(level, count)
    elif mode == "6":
        quiz.quiz_kanji_meaning(level, count)
    elif mode == "7":
        quiz.quiz_sentence_order(level, count)
    elif mode == "8":
        quiz.quiz_conjugation(level, count)


def _row_get(row, key, default=""):
    """Safely get a value from sqlite3.Row or dict."""
    try:
        val = row[key]
        return val if val is not None else default
    except (KeyError, IndexError):
        return default


def _detail_loop(card, show_fn):
    """Show card detail with TTS support. 'p' to play, Enter to go back."""
    import tts
    while True:
        clear()
        show_fn(card, show_answer=True)
        choice = Prompt.ask(f"\n[cyan]{t('list.detail_action')}[/cyan]", default="0")
        if choice.lower() == "p":
            # reading (hiragana) varsa onu oku, yoksa word'u oku
            text = _row_get(card, "reading") or _row_get(card, "word") or _row_get(card, "kanji") or _row_get(card, "pattern") or ""
            tts.speak(text)
        elif choice == "0" or choice == "":
            break


def _list_search(items, query):
    """Filter items by query matching word/reading/meaning fields."""
    from i18n import meaning_field
    q = query.lower()
    mf = meaning_field()
    results = []
    for item in items:
        fields = [
            _row_get(item, "word"), _row_get(item, "reading"),
            _row_get(item, "kanji"), _row_get(item, "on_yomi"), _row_get(item, "kun_yomi"),
            _row_get(item, "meaning_tr"), _row_get(item, "meaning_en"),
            _row_get(item, "pattern"),
        ]
        if any(q in (f or "").lower() for f in fields):
            results.append(item)
    return results


def handle_vocab_list():
    level = _current_level()
    all_vocabs = db.get_vocabulary(level=level)
    filtered = None
    while True:
        clear()
        vocabs = show_vocab_list(level) if filtered is None else show_vocab_list(level, filtered)
        if not vocabs:
            Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")
            return
        choice = Prompt.ask(f"\n[cyan]{t('list.detail_prompt')}[/cyan]", default="0")
        if choice == "0":
            if filtered is not None:
                filtered = None
                continue
            return
        if choice.lower() == "s":
            query = Prompt.ask(f"[cyan]{t('list.search_prompt')}[/cyan]")
            if query.strip():
                filtered = _list_search(all_vocabs, query.strip())
                if not filtered:
                    console.print(f"[yellow]{t('list.no_match')}[/yellow]")
                    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
                    filtered = None
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(vocabs):
                _detail_loop(vocabs[idx - 1], show_vocab_card)


def handle_kanji_list():
    level = _current_level()
    all_kanjis = db.get_kanji(level=level)
    filtered = None
    while True:
        clear()
        kanjis = show_kanji_list(level) if filtered is None else show_kanji_list(level, filtered)
        if not kanjis:
            Prompt.ask(f"\n[dim]{t('continue_enter')}[/dim]", default="")
            return
        choice = Prompt.ask(f"\n[cyan]{t('list.detail_prompt')}[/cyan]", default="0")
        if choice == "0":
            if filtered is not None:
                filtered = None
                continue
            return
        if choice.lower() == "s":
            query = Prompt.ask(f"[cyan]{t('list.search_prompt')}[/cyan]")
            if query.strip():
                filtered = _list_search(all_kanjis, query.strip())
                if not filtered:
                    console.print(f"[yellow]{t('list.no_match')}[/yellow]")
                    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
                    filtered = None
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(kanjis):
                _detail_loop(kanjis[idx - 1], show_kanji_card)


def handle_search():
    query = ""
    while True:
        clear()
        banner()
        console.print(f"\n[bold]{t('search.title')}[/bold]\n")
        if not query:
            query = Prompt.ask(f"[cyan]{t('search.prompt')}[/cyan]")
            if not query.strip():
                return
        from i18n import get_lang
        results, expansion = db.search_smart(query.strip(), get_lang())
        if expansion:
            terms = ", ".join(expansion["to"])
            key = "search.expanded_synonym" if expansion["kind"] == "synonym" else "search.expanded_fuzzy"
            console.print(
                f"\n[yellow]{t(key, query=expansion['from'], terms=terms)}[/yellow]"
            )
        console.print()
        all_items = show_search_results(results)
        if not all_items:
            choice = Prompt.ask(f"\n[cyan]{t('search.action_prompt')}[/cyan]", default="0")
        else:
            choice = Prompt.ask(f"\n[cyan]{t('search.action_prompt')}[/cyan]", default="0")
        if choice == "0":
            return
        if choice.lower() == "s":
            query = Prompt.ask(f"[cyan]{t('search.prompt')}[/cyan]")
            if not query.strip():
                return
            continue
        if choice.isdigit() and all_items:
            idx = int(choice)
            if 1 <= idx <= len(all_items):
                item, item_type = all_items[idx - 1]
                if item_type == "vocab":
                    _detail_loop(item, show_vocab_card)
                elif item_type == "kanji":
                    _detail_loop(item, show_kanji_card)
                elif item_type == "grammar":
                    _detail_loop(item, show_grammar_card)
                continue
        query = ""


def handle_language_change():
    """Dil degistirme islemini yap."""
    lang_code = show_language_select()
    set_lang(lang_code)


def ensure_level_selected():
    """Seviye config'de yoksa zorla seçtir; varsa değiştirmek isteyip istemediğini sor."""
    from i18n import get_level, set_level, ACTIVE_LEVELS
    current = get_level()

    if current not in ACTIVE_LEVELS:
        # İlk seçim ya da artık desteklenmeyen seviye → zorunlu seçim
        new_level = show_startup_level_select()
        set_level(new_level)
        console.print(f"\n[green]{t('startup.level_set', level=new_level)}[/green]\n")
        return

    # Mevcut seviyeyi göster, değiştirmek ister mi?
    console.print(
        f"\n[bold cyan]{t('startup.current_level')}:[/bold cyan] "
        f"[bold]{current}[/bold]"
    )
    yes = t("startup.confirm_yes")
    no = t("startup.confirm_no")
    answer = Prompt.ask(
        f"[dim]{t('startup.change_level_q')}[/dim]",
        default=no,
    ).strip().lower()
    if answer == yes:
        new_level = show_startup_level_select()
        set_level(new_level)
        console.print(f"\n[green]{t('startup.level_set', level=new_level)}[/green]\n")


def first_run_setup():
    """İlk açılışta setup wizard: dil, seviye, veritabanı, ses paketi."""
    from rich.progress import Progress
    from i18n import set_level

    # --- Hoşgeldin ---
    clear()
    banner()
    console.print(f"\n[bold green]{'Welcome to Nihongo Master!'}[/bold green]")
    console.print(f"[dim]{'日本語マスターへようこそ！'}[/dim]\n")

    # --- Adım 1: Dil ---
    console.print(f"[bold cyan]{'Step 1: Select Language / Dil Secimi'}[/bold cyan]\n")
    lang_code = show_language_select()
    set_lang(lang_code)

    # --- Adım 2: Seviye ---
    level = show_startup_level_select()
    set_level(level)

    # --- Adım 3: Veritabanı ---
    clear()
    banner()
    console.print(f"\n[bold cyan]{t('setup.step_db')}[/bold cyan]\n")
    ensure_db()
    console.print(f"[green]{t('setup.db_ready')}[/green]\n")

    # --- Adım 3: Ses Paketi ---
    # Installer önceden indirmişse (Windows .exe / macOS .pkg) sorma, atla.
    import glob
    from paths import _DB_DIR
    cache_dir = os.path.join(_DB_DIR, "tts_cache")
    existing_audio = glob.glob(os.path.join(cache_dir, "*.mp3"))

    if existing_audio:
        console.print(f"[green]{t('setup.audio_already_installed', count=len(existing_audio))}[/green]\n")
    else:
        console.print(f"[bold cyan]{t('setup.step_audio')}[/bold cyan]\n")
        console.print(f"  {t('setup.audio_ask')}")
        console.print(f"  [dim]{t('setup.audio_hint')}[/dim]\n")
        console.print(f"  [cyan]1[/cyan] {t('setup.audio_yes')}")
        console.print(f"  [cyan]2[/cyan] {t('setup.audio_no')}")
        audio_choice = Prompt.ask(t("your_choice"), choices=["1", "2"], default="1")

        if audio_choice == "1":
            import tts
            console.print()
            with Progress(console=console) as progress:
                task = progress.add_task(t("settings.download_audio_progress", current=0, total="?"), total=None)
                def on_progress(current, total):
                    progress.update(task, total=total, completed=current,
                                    description=t("settings.download_audio_progress", current=current, total=total))
                cached, skipped, failed = tts.download_all_audio(progress_callback=on_progress)
            if failed == -1:
                console.print(f"\n[yellow]{t('settings.download_audio_fail')}[/yellow]")
            else:
                console.print(f"\n[green]{t('settings.download_audio_done', cached=cached, skipped=skipped, failed=failed)}[/green]")

    # --- Bitti ---
    console.print(f"\n[bold green]{t('setup.done')}[/bold green]\n")
    Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def handle_resume_study():
    """Curriculum 'devam et' akisi: kullanicinin kaldigi yerdeki lesson + asama."""
    import curriculum
    level = _current_level()
    state = curriculum.get_resume_state(level)

    if state["overall_progress"]["total_lessons"] == 0:
        clear(); banner()
        console.print(f"\n[yellow]{t('resume.no_curriculum', level=level)}[/yellow]\n")
        Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        return

    while True:
        clear(); banner()
        state = curriculum.get_resume_state(level)

        # Mufredat tamam — tebrikler ekrani
        if state["complete"]:
            console.print(f"\n[bold green]{t('resume.curriculum_complete', level=level)}[/bold green]\n")
            console.print(f"[dim]{t('resume.try_free_srs')}[/dim]\n")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
            return

        # Resume header
        op = state["overall_progress"]
        lp = state["lesson_progress"]
        pp = state["phase_progress"]

        header = Text()
        header.append(f"{state['textbook']} ", style="dim")
        header.append(f"L{state['lesson_no']}: ", style="bold cyan")
        header.append(state["lesson_title"], style="bold white")
        if state.get("lesson_title_ja"):
            header.append(f"  〜 {state['lesson_title_ja']}", style="yellow")
        console.print(Panel(header, border_style="cyan"))

        info = Table(show_header=False, box=None, padding=(0, 2))
        info.add_column(style="cyan")
        info.add_column(style="white")
        info.add_row(t("resume.overall"),
                     f"{op['completed_lessons']}/{op['total_lessons']} {t('resume.lessons_done')}")
        info.add_row(t("resume.lesson_phases"),
                     f"{lp['phases_done']}/{lp['phases_total']}")
        phase_label = t(f"resume.phase.{state['phase']}")
        if state["phase"] == "exam":
            info.add_row(t("resume.next_phase"),
                         f"[bold yellow]{phase_label}[/bold yellow]")
        else:
            info.add_row(t("resume.next_phase"),
                         f"[bold yellow]{phase_label}[/bold yellow]  "
                         f"({pp['learned']}/{pp['total']})")
        console.print(info)
        console.print()

        menu = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        menu.add_column("No", style="bold cyan", width=4)
        menu.add_column("", style="white")
        menu.add_row("1", f"[bold green]{t('resume.continue')}[/bold green]")
        menu.add_row("2", t("resume.skip_phase"))
        menu.add_row("0", t("back"))
        console.print(Panel(menu, title=f"[bold]{t('resume.title')}[/bold]", border_style="green"))

        choice = Prompt.ask(t("your_choice"), choices=["0", "1", "2"], default="1")
        if choice == "0":
            return
        if choice == "2":
            # "Atla" — bu asamayi geciyoruz, bir sonrakine yapay olarak gecemeyiz cunku
            # asamalar gercek ilerlemeye baglı. Atlamak icin lesson_id ile manuel ders
            # kitabi menusune yonlendir.
            handle_textbook_study()
            return

        # Devam — asamaya gore uygun fonksiyon
        lesson_id = state["lesson_id"]
        phase = state["phase"]
        if phase == "vocab":
            quiz.study_lesson_vocab(lesson_id)
        elif phase == "grammar":
            quiz.study_lesson_grammar(lesson_id)
        elif phase == "kanji":
            quiz.study_lesson_kanji(lesson_id)
        elif phase == "exam":
            import exam_genki
            exam_genki.run_genki_lesson_exam(level, lesson_id)


def handle_textbook_study():
    """Ders kitabı modu: level config'den, ders → vocab/grammar/kanji/sınav."""
    level = _current_level()
    while True:
        lesson_id = show_lesson_select(level)
        if lesson_id is None:
            return
        while True:
            action = show_lesson_detail_menu(lesson_id)
            if action == "0":
                break
            elif action == "1":
                quiz.study_lesson_vocab(lesson_id)
            elif action == "2":
                quiz.study_lesson_grammar(lesson_id)
            elif action == "3":
                quiz.study_lesson_kanji(lesson_id)
            elif action == "4":
                count = IntPrompt.ask(t("quiz.question_count"), default=10)
                quiz.quiz_lesson_exam(lesson_id, count)


def handle_settings():
    export_dir = os.path.join(os.path.expanduser("~"), "nihongo_export")
    while True:
        clear()
        banner()
        choice = show_settings_menu()

        if choice == "0":
            return
        elif choice == "1":
            # Anki export
            console.print(f"\n[bold]{t('settings.anki_title')}[/bold]")
            console.print(f"  [cyan]1[/cyan] {t('settings.anki_vocab')}")
            console.print(f"  [cyan]2[/cyan] {t('settings.anki_kanji')}")
            console.print(f"  [cyan]3[/cyan] {t('settings.anki_grammar')}")
            sub = Prompt.ask(t("your_choice"), choices=["1", "2", "3"], default="1")
            card_type = {"1": "vocabulary", "2": "kanji", "3": "grammar"}[sub]
            filepath = os.path.join(export_dir, f"{card_type}_anki.tsv")
            count = db.export_anki_tsv(card_type, filepath)
            console.print(f"\n[green]{t('settings.exported', count=count, path=filepath)}[/green]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        elif choice == "2":
            # Backup
            from datetime import datetime
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(export_dir, f"nihongo_backup_{stamp}.db")
            db.backup_db(dest)
            console.print(f"\n[green]{t('settings.backup_done', path=dest)}[/green]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        elif choice == "3":
            # Restore
            src = Prompt.ask(t("settings.restore_prompt"))
            try:
                db.restore_db(src.strip())
                console.print(f"[green]{t('settings.restore_done')}[/green]")
            except FileNotFoundError as e:
                console.print(f"[red]{e}[/red]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        elif choice == "4":
            # Language change
            handle_language_change()
        elif choice == "5":
            # Download all TTS audio
            import tts
            from rich.progress import Progress
            console.print(f"\n[bold]{t('settings.download_audio')}[/bold]\n")
            with Progress(console=console) as progress:
                task = progress.add_task(t("settings.download_audio_progress", current=0, total="?"), total=None)
                def on_progress(current, total):
                    progress.update(task, total=total, completed=current,
                                    description=t("settings.download_audio_progress", current=current, total=total))
                cached, skipped, failed = tts.download_all_audio(progress_callback=on_progress)
            if failed == -1:
                console.print(f"\n[red]{t('settings.download_audio_fail')}[/red]")
            else:
                console.print(f"\n[green]{t('settings.download_audio_done', cached=cached, skipped=skipped, failed=failed)}[/green]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")
        elif choice == "6":
            # Card limit
            from i18n import get_card_limit, set_card_limit
            current = get_card_limit()
            new_limit = IntPrompt.ask(t("settings.card_limit_prompt", current=current), default=current)
            if new_limit < 1:
                new_limit = 1
            set_card_limit(new_limit)
            console.print(f"\n[green]{t('settings.card_limit_set', limit=new_limit)}[/green]")
            Prompt.ask(f"[dim]{t('continue_enter')}[/dim]", default="")


def main():
    if "--init" in sys.argv:
        i18n.init()
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            console.print(f"[yellow]{t('db.old_deleted')}[/yellow]")
        from data.init_db import main as init_main
        init_main()
        return

    if "--stats" in sys.argv:
        i18n.init()
        ensure_db()
        show_stats()
        return

    # Dil ayarini yukle; ilk acilissa setup wizard
    has_lang = i18n.init()
    if not has_lang:
        first_run_setup()
    else:
        ensure_db()

    # Seviye kontrolü: ilk girişte zorla seçtir, sonraki açılışlarda değiştir? sor
    ensure_level_selected()

    try:
        while True:
            choice = show_main_menu()

            if choice == "0":
                clear()
                console.print(f"\n[bold red]お疲れ様でした！[/bold red] ({t('exit.goodbye')})")
                console.print(f"[dim]{t('exit.see_you')}、また明日！[/dim]\n")
                break
            elif choice == "1":
                handle_resume_study()
            elif choice == "2":
                handle_study_vocab()
            elif choice == "3":
                handle_study_kanji()
            elif choice == "4":
                handle_study_grammar()
            elif choice == "5":
                handle_quiz()
            elif choice == "6":
                handle_vocab_list()
            elif choice == "7":
                handle_kanji_list()
            elif choice == "8":
                show_stats()
            elif choice == "9":
                handle_settings()
            elif choice == "A":
                handle_search()
            elif choice == "T":
                handle_textbook_study()

    except KeyboardInterrupt:
        console.print(f"\n\n[bold red]さようなら！[/bold red] ({t('exit.interrupt')})\n")


if __name__ == "__main__":
    main()
