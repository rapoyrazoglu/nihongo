#!/usr/bin/env python3
"""日本語マスター - JLPT Japonca Öğrenme Uygulaması.

Kullanım:
    python nihongo.py            # Ana menüyü başlat
    python nihongo.py --init     # Veritabanını sıfırdan oluştur
    python nihongo.py --stats    # İstatistikleri göster
    python nihongo.py --version  # Sürüm bilgisi
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
        print("'rich' kütüphanesi bulunamadı, yükleniyor...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich>=13.0"])
        os.execv(sys.executable, [sys.executable] + sys.argv)

from version import __version__
from paths import DB_PATH

# --- --version flag ---
if "--version" in sys.argv:
    print(f"nihongo {__version__}")
    sys.exit(0)

import db
from ui import console, show_main_menu, show_level_select, show_vocab_list, show_kanji_list, show_stats, show_quiz_menu, clear, banner
from rich.prompt import Prompt, IntPrompt
import quiz


def migrate_old_db():
    """Eski ./nihongo.db varsa ~/.local/share/nihongo/ altına kopyala."""
    old_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nihongo.db")
    if os.path.exists(old_db) and not os.path.exists(DB_PATH):
        print(f"Eski veritabanı bulundu, taşınıyor: {old_db} → {DB_PATH}")
        shutil.copy2(old_db, DB_PATH)


def ensure_db():
    """Veritabanı yoksa oluştur ve seed et."""
    migrate_old_db()
    if not os.path.exists(DB_PATH):
        console.print("[yellow]Veritabanı bulunamadı, oluşturuluyor...[/yellow]")
        from data.init_db import main as init_main
        init_main()
        console.print("[green]Veritabanı hazır![/green]\n")
    else:
        # Tabloların var olduğundan emin ol
        db.init_db()


def handle_study_vocab():
    level = show_level_select("Kelime Çalışma - Seviye Seçin")
    if level:
        quiz.study_vocabulary(level)


def handle_study_kanji():
    level = show_level_select("Kanji Çalışma - Seviye Seçin")
    if level:
        quiz.study_kanji(level)


def handle_study_grammar():
    level = show_level_select("Dilbilgisi Çalışma - Seviye Seçin")
    if level:
        quiz.study_grammar(level)


def handle_quiz():
    mode = show_quiz_menu()
    if mode == "0":
        return

    level = show_level_select("Quiz - Seviye Seçin")
    if not level:
        return

    count = IntPrompt.ask("Soru sayısı", default=10)

    if mode == "1":
        quiz.quiz_jp_to_tr(level, count)
    elif mode == "2":
        quiz.quiz_tr_to_jp(level, count)
    elif mode == "3":
        quiz.quiz_kanji_reading(level, count)
    elif mode == "4":
        quiz.quiz_kanji_meaning(level, count)


def handle_vocab_list():
    level = show_level_select("Kelime Listesi - Seviye Seçin")
    if level:
        clear()
        show_vocab_list(level)
        Prompt.ask("\n[dim]Devam etmek için Enter[/dim]", default="")


def handle_kanji_list():
    level = show_level_select("Kanji Listesi - Seviye Seçin")
    if level:
        clear()
        show_kanji_list(level)
        Prompt.ask("\n[dim]Devam etmek için Enter[/dim]", default="")


def handle_settings():
    clear()
    banner()
    console.print("\n[bold]Ayarlar[/bold]\n")
    console.print("[dim]Ayarlar şu anda basit tutulmuştur.[/dim]")
    console.print("[dim]Veritabanını sıfırlamak için: python nihongo.py --init[/dim]")
    console.print()
    Prompt.ask("[dim]Devam etmek için Enter[/dim]", default="")


def main():
    if "--init" in sys.argv:
        # Veritabanını sıfırla
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            console.print("[yellow]Eski veritabanı silindi.[/yellow]")
        from data.init_db import main as init_main
        init_main()
        return

    if "--stats" in sys.argv:
        ensure_db()
        show_stats()
        return

    ensure_db()

    try:
        while True:
            choice = show_main_menu()

            if choice == "0":
                clear()
                console.print("\n[bold red]お疲れ様でした！[/bold red] (Otsukaresama deshita!)")
                console.print("[dim]İyi çalışmalar, また明日！[/dim]\n")
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

    except KeyboardInterrupt:
        console.print("\n\n[bold red]さようなら！[/bold red] (Sayounara!)\n")


if __name__ == "__main__":
    main()
