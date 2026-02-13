<p align="center">
  <img src="assets/nihongo.svg" width="120" alt="Nihongo Master">
</p>

<h1 align="center">日本語マスター Nihongo Master</h1>

<p align="center">
  <strong>Terminal-based JLPT Japanese learning app with spaced repetition</strong>
</p>

<p align="center">
  <a href="https://github.com/rapoyrazoglu/nihongo/releases/latest"><img src="https://img.shields.io/github/v/release/rapoyrazoglu/nihongo?style=flat-square&color=blue" alt="Release"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/JLPT-N5--N3-e74c3c?style=flat-square" alt="JLPT">
  <img src="https://img.shields.io/badge/languages-8-2ecc71?style=flat-square" alt="Languages">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey?style=flat-square" alt="Platform">
</p>

<p align="center">
  <sub>Study vocabulary, kanji, and grammar with SRS flashcards, quizzes, and text-to-speech.</sub><br>
  <sub>Supports 8 UI languages: Turkish, English, German, French, Spanish, Portuguese, Korean, Chinese.</sub>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **SRS Flashcards** | SM-2 spaced repetition for vocabulary, kanji, and grammar |
| **Quiz Modes** | JP→Meaning, Meaning→JP, kanji reading, kanji meaning (multiple choice & typing) |
| **JLPT N5–N3** | 1579 vocabulary, 585 kanji, 120 grammar patterns |
| **Text-to-Speech** | Native Japanese pronunciation via system TTS (espeak-ng / say / SAPI) |
| **8 Languages** | Auto-detects system locale, changeable from settings |
| **Search** | Full-text search across vocabulary, kanji, and grammar |
| **Statistics** | Daily progress tracking, accuracy rates, study streaks |
| **Anki Export** | Export flashcards as TSV for Anki import |
| **Backup/Restore** | Database backup and restore |
| **Self-Update** | `nihongo --update` to download the latest version |
| **Cross-Platform** | Single binary for Linux, macOS, Windows |

---

## Installation

### Pre-built binary (recommended)

Download from [**Releases**](https://github.com/rapoyrazoglu/nihongo/releases/latest):

| Platform | Install |
|----------|---------|
| **Ubuntu / Debian** | `sudo dpkg -i nihongo_*.deb` |
| **Arch Linux** | `yay -S nihongo` |
| **macOS** | `brew install rapoyrazoglu/nihongo/nihongo` |
| **Windows** | Download `nihongo-windows.exe` and run |

### From source

```bash
git clone https://github.com/rapoyrazoglu/nihongo.git
cd nihongo
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/nihongo.py
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

---

## Usage

```
nihongo                # Start the app
nihongo --init         # Reset and rebuild database
nihongo --stats        # Show statistics
nihongo --version      # Print version
nihongo --update       # Update to the latest version
```

On first launch the app detects your system language. You can change it anytime from **Settings > Change Language**.

### Main Menu

```
 1  Study Vocabulary     SRS review with word cards
 2  Study Kanji          SRS review with kanji cards
 3  Study Grammar        Grammar point review
 4  Quiz                 Test modes (JP↔Meaning, Kanji reading)
 5  Vocabulary List      Browse all words
 6  Kanji List           Browse all kanji
 7  Statistics           Progress and stats
 8  Settings             Export, backup, restore, language
 9  Search               Search words, kanji, grammar
 0  Exit
```

### Japanese Input

For typing Japanese answers in quiz mode you need an input method editor. On Arch Linux:

```bash
bash setup_fcitx5.sh   # Installs fcitx5 + Mozc
```

Use `Ctrl+Space` to toggle Japanese input.

---

## Project Structure

```
nihongo/
├── src/                   Application source code
│   ├── nihongo.py         Entry point & menu routing
│   ├── ui.py              Rich terminal UI
│   ├── quiz.py            Quiz & SRS study sessions
│   ├── db.py              SQLite database operations
│   ├── srs.py             SM-2 spaced repetition algorithm
│   ├── tts.py             Cross-platform text-to-speech
│   ├── i18n.py            Internationalization engine
│   ├── updater.py         Self-update via GitHub releases
│   ├── paths.py           Path resolution (frozen vs source)
│   ├── version.py         Version string
│   ├── data/              JLPT content (vocab, kanji, grammar JSON)
│   └── lang/              8 translation files (tr/en/de/fr/es/pt/ko/zh)
├── assets/                App icon
├── Formula/               Homebrew formula
├── .github/workflows/     CI/CD: build + release + packages
├── nihongo.spec           PyInstaller build spec
├── Makefile               Build & install targets
├── build.sh               Build script
└── requirements.txt       Python dependencies
```

---

## Data Storage

| Platform | Path |
|----------|------|
| Linux | `~/.local/share/nihongo/` |
| macOS | `~/Library/Application Support/nihongo/` |
| Windows | `%APPDATA%/nihongo/` |

Files: `nihongo.db` (SQLite), `config.json` (language preference)

---

## Dependencies

- **Python 3.10+**
- **[rich](https://github.com/Textualize/rich)** — Terminal UI rendering
- **espeak-ng** (Linux, optional) — Text-to-speech

---

## License

MIT
