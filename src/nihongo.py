#!/usr/bin/env python3
"""日本語マスター - JLPT Japonca Ogrenme Uygulamasi.

Kullanim:
    python nihongo.py            # Ana menuyu baslat
    python nihongo.py --init     # Veritabanini sifirdan olustur
    python nihongo.py --stats    # Istatistikleri goster
    python nihongo.py --version  # Surum bilgisi
    python nihongo.py --update        # En son surume guncelle
    python nihongo.py --update-beta   # Beta dahil en son surume guncelle
"""

import sys
import os
import shutil

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

import db
from ui import console, show_main_menu, show_level_select, show_vocab_list, show_kanji_list, show_vocab_card, show_kanji_card, show_grammar_card, show_stats, show_quiz_menu, show_search_results, show_settings_menu, show_language_select, clear, banner
from rich.prompt import Prompt, IntPrompt
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
                                  migrate_meanings, update_meanings)
        migrate_meanings()
        migrate_extra_examples()
        migrate_grammar_unique()
        seed_vocabulary()
        seed_kanji()
        seed_grammar()
        update_extra_examples()
        update_meanings()


def handle_study_vocab():
    level = show_level_select(t("vocab_study_level"))
    if level:
        quiz.study_vocabulary(level)


def handle_study_kanji():
    level = show_level_select(t("kanji_study_level"))
    if level:
        quiz.study_kanji(level)


def handle_study_grammar():
    level = show_level_select(t("grammar_study_level"))
    if level:
        quiz.study_grammar(level)


def handle_quiz():
    mode = show_quiz_menu()
    if mode == "0":
        return

    level = show_level_select(t("quiz_level"))
    if not level:
        return

    count = IntPrompt.ask(t("quiz.question_count"), default=10)

    if mode == "1":
        quiz.quiz_jp_to_tr(level, count)
    elif mode == "2":
        quiz.quiz_tr_to_jp(level, count)
    elif mode == "3":
        quiz.quiz_kanji_reading(level, count)
    elif mode == "4":
        quiz.quiz_kanji_meaning(level, count)


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
    level = show_level_select(t("vocab_list_level"))
    if not level:
        return
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
    level = show_level_select(t("kanji_list_level"))
    if not level:
        return
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
        results = db.search_all(query.strip())
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


def first_run_setup():
    """İlk açılışta setup wizard: dil, veritabanı, ses paketi."""
    from rich.progress import Progress

    # --- Hoşgeldin ---
    clear()
    banner()
    console.print(f"\n[bold green]{'Welcome to Nihongo Master!'}[/bold green]")
    console.print(f"[dim]{'日本語マスターへようこそ！'}[/dim]\n")

    # --- Adım 1: Dil ---
    console.print(f"[bold cyan]{'Step 1: Select Language / Dil Secimi'}[/bold cyan]\n")
    lang_code = show_language_select()
    set_lang(lang_code)

    # --- Adım 2: Veritabanı ---
    clear()
    banner()
    console.print(f"\n[bold cyan]{t('setup.step_db')}[/bold cyan]\n")
    ensure_db()
    console.print(f"[green]{t('setup.db_ready')}[/green]\n")

    # --- Adım 3: Ses Paketi ---
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

    try:
        while True:
            choice = show_main_menu()

            if choice == "0":
                clear()
                console.print(f"\n[bold red]お疲れ様でした！[/bold red] ({t('exit.goodbye')})")
                console.print(f"[dim]{t('exit.see_you')}、また明日！[/dim]\n")
                break
            elif choice == "1":
                handle_study_vocab()
            elif choice == "2":
                handle_study_kanji()
            elif choice == "3":
                handle_study_grammar()
            elif choice == "4":
                handle_quiz()
            elif choice == "5":
                handle_vocab_list()
            elif choice == "6":
                handle_kanji_list()
            elif choice == "7":
                show_stats()
            elif choice == "8":
                handle_settings()
            elif choice == "9":
                handle_search()

    except KeyboardInterrupt:
        console.print(f"\n\n[bold red]さようなら！[/bold red] ({t('exit.interrupt')})\n")


if __name__ == "__main__":
    main()
