# Nihongo Master 日本語マスター

Terminal-based JLPT Japanese learning application with spaced repetition (SRS), quiz modes, kanji study, grammar drills, and text-to-speech.

Supports 8 UI languages: Turkish, English, German, French, Spanish, Portuguese, Korean, Chinese.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)

## Features

- **SRS Flashcards** - SM-2 spaced repetition for vocabulary, kanji, and grammar
- **Quiz Modes** - JP->Meaning, Meaning->JP, kanji reading, kanji meaning (multiple choice & typing)
- **JLPT N5-N3 Content** - 1579 vocabulary, 585 kanji, 120 grammar patterns
- **Text-to-Speech** - Native Japanese pronunciation via system TTS (espeak-ng / say / SAPI)
- **Multi-language UI** - 8 languages with auto-detection of system locale
- **Search** - Full-text search across vocabulary, kanji, and grammar
- **Statistics** - Daily progress tracking, accuracy rates, study streaks
- **Anki Export** - Export flashcards as TSV for Anki import
- **Backup/Restore** - Database backup and restore
- **Cross-platform** - Single binary builds for Linux, macOS, Windows

## Installation

### Pre-built binary (recommended)

Download from [Releases](https://github.com/rapoyrazoglu/nihongo/releases/latest):

| Platform | Command |
|----------|---------|
| **Linux (deb)** | `sudo dpkg -i nihongo_*.deb` |
| **Linux (snap)** | `sudo snap install nihongo` |
| **Arch Linux** | `yay -S nihongo` |
| **macOS** | `brew install rapoyrazoglu/nihongo/nihongo` |
| **Windows** | Download `nihongo-windows.exe` and run |

### From source

```bash
git clone https://github.com/rapoyrazoglu/nihongo.git
cd nihongo
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python nihongo.py
```

### Build binary

```bash
bash build.sh
./dist/nihongo
```

### System install (Linux)

```bash
sudo make install
```

## Usage

```
python nihongo.py            # Start the app
python nihongo.py --init     # Reset and rebuild database
python nihongo.py --stats    # Show statistics
python nihongo.py --version  # Print version
```

On first launch the app detects your system language. If it matches one of the 8 supported languages it is selected automatically; otherwise English is used. You can change the language anytime from the Settings menu.

### Main Menu

```
1  Study Vocabulary    SRS review with word cards
2  Study Kanji         SRS review with kanji cards
3  Study Grammar       Grammar point review
4  Quiz                Test modes (JP<->Meaning, Kanji reading)
5  Vocabulary List     Show all words
6  Kanji List          Show all kanji
7  Statistics          Progress and statistics
8  Settings            Export, backup, restore, change language
9  Search              Search words, kanji, grammar
0  Exit
```

### Japanese Input

For typing Japanese answers in quiz mode you need an input method editor. On Arch Linux:

```bash
bash setup_fcitx5.sh
```

This installs and configures fcitx5 + Mozc. Use `Ctrl+Space` to toggle Japanese input.

## Project Structure

```
nihongo/
├── nihongo.py          # Entry point, menu routing
├── ui.py               # Rich terminal UI (menus, cards, tables)
├── quiz.py             # Quiz and SRS study sessions
├── db.py               # SQLite database operations
├── srs.py              # SM-2 spaced repetition algorithm
├── tts.py              # Cross-platform text-to-speech
├── i18n.py             # Internationalization engine
├── paths.py            # Path resolution (frozen vs source)
├── version.py          # Version string
├── data/
│   ├── init_db.py      # Database seeding
│   ├── n5_vocab.json   # JLPT N5 vocabulary (640)
│   ├── n4_vocab.json   # JLPT N4 vocabulary (502)
│   ├── n3_vocab.json   # JLPT N3 vocabulary (437)
│   ├── n5_kanji.json   # JLPT N5 kanji (145)
│   ├── n4_kanji.json   # JLPT N4 kanji (132)
│   ├── n3_kanji.json   # JLPT N3 kanji (308)
│   └── grammar.json    # Grammar patterns (120)
├── lang/
│   ├── tr.json         # Turkish
│   ├── en.json         # English
│   ├── de.json         # German
│   ├── fr.json         # French
│   ├── es.json         # Spanish
│   ├── pt.json         # Portuguese
│   ├── ko.json         # Korean
│   └── zh.json         # Chinese
├── assets/
│   └── nihongo.svg     # App icon
├── Formula/
│   └── nihongo.rb      # Homebrew formula
├── snap/
│   └── snapcraft.yaml  # Snap package config
├── .github/
│   └── workflows/
│       └── release.yml # CI/CD: build + release + packages
├── nihongo.spec        # PyInstaller build spec
├── nihongo.desktop     # Linux desktop entry
├── PKGBUILD            # Arch Linux package
├── Makefile            # Build & install targets
├── build.sh            # Build script
├── setup_fcitx5.sh     # Japanese input setup (Arch)
├── requirements.txt    # Python dependencies
├── ROADMAP.md          # Development roadmap
└── STUDY_PLAN.md       # JLPT study guide
```

## Data

User data is stored at:

| Platform | Path |
|----------|------|
| Linux | `~/.local/share/nihongo/` |
| macOS | `~/Library/Application Support/nihongo/` |
| Windows | `%APPDATA%/nihongo/` |

- `nihongo.db` - SQLite database (vocabulary, kanji, grammar, SRS reviews, stats)
- `config.json` - User preferences (language setting)

## Dependencies

- **Python 3.10+**
- **[rich](https://github.com/Textualize/rich)** - Terminal UI rendering
- **espeak-ng** (Linux, optional) - Text-to-speech

## License

MIT
