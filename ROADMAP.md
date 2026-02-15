# Nihongo Master - Changelog & Roadmap

---

## Released

### v1.6.0-beta - Content Expansion & Neural TTS
- [x] N5 vocabulary: 640 → 801 words (JLPT target: 800)
- [x] N4 vocabulary: 502 → 683 words (JLPT target: 700)
- [x] N5 grammar: 30 → 80 patterns (JLPT target: 80)
- [x] N4 grammar: 40 → 50 patterns (JLPT target: 50)
- [x] N4 kanji: 132 → 200 kanji (JLPT target: 200)
- [x] Interactive search: select result by number to view card detail
- [x] Consecutive search: press 's' for new search without leaving
- [x] Neural TTS via edge-tts (Microsoft Neural, ja-JP-NanamiNeural voice)
- [x] TTS audio caching for offline playback
- [x] Bulk audio download (Settings > Download all audio)
- [x] Auto-install edge-tts via pipx/pip on first TTS use
- [x] TTS reads hiragana reading (not kanji) for correct pronunciation
- [x] `--update-beta` flag for updating to pre-release versions
- [x] Updater compares build timestamps (detects same-version rebuilds)
- [x] Fix: DB migration order (meanings before seed)
- [x] Fix: sqlite3.Row → dict conversion in search results

### v1.5.7 - Interactive Lists
- [x] Vocab/kanji list: enter number to see detailed card
- [x] Shows full info (example, compounds, part of speech, etc.)

### v1.5.6 - Project Restructure
- [x] Move all source code into `src/` directory
- [x] Clean project root (only build/config files remain)
- [x] Update PyInstaller spec and README

### v1.5.5 - Updater Fix
- [x] Fix cross-device link error when updating (`/tmp` vs binary directory)
- [x] Temp file now created in same directory as binary

### v1.5.4 - Updater i18n
- [x] Translate all updater messages to 8 languages
- [x] Updater now respects user's language setting
- [x] Beautified README with centered header and badges

### v1.5.3 - SSL Fix
- [x] Fix SSL certificate verification in PyInstaller bundles
- [x] Explicitly load system CA certificates for HTTPS connections
- [x] Support Arch Linux, Debian, Fedora, macOS CA paths

### v1.5.2 - CI/CD Improvements
- [x] Fix Windows build (PyInstaller + Python 3.12 compatibility)
- [x] Remove snap packaging (replaced with .deb + Homebrew + AUR)

### v1.5.1 - Self-Update
- [x] Add `nihongo --update` command for self-updating binaries
- [x] GitHub Releases API integration for version checking
- [x] Automatic binary download and replacement

### v1.5.0 - Internationalization (i18n)
- [x] Multi-language UI support (TR, EN, DE, FR, ES, PT, KO, ZH)
- [x] Auto-detect system language on first launch
- [x] Language selection screen + settings menu
- [x] Dynamic meaning field (meaning_tr for Turkish, meaning_en for others)
- [x] JSON-based translation engine with fallback to English
- [x] Config persistence (~/.local/share/nihongo/config.json)

---

## In Progress

### v1.6.0 - Stable Release
- [ ] N4 vocabulary: 683 → 700 (17 words remaining)
- [ ] Final testing and bug fixes
- [ ] Update README with new features

---

## Planned

### v1.7.0 - Study Enhancements
- [ ] N3 content expansion (vocabulary, kanji, grammar)
- [ ] Custom study decks (user-created word lists)
- [ ] Cloze deletion quiz mode (fill in the blank)
- [ ] Listening quiz mode (audio -> meaning)
- [ ] Wrong answer review session
- [ ] Daily streak tracking + goals

### v1.8.0 - Data & Analytics
- [ ] Detailed progress charts (weekly/monthly)
- [ ] Per-word difficulty analysis
- [ ] Study time heatmap
- [ ] JLPT readiness score per level
- [ ] Export statistics as PDF/CSV

### v1.9.0 - UX Improvements
- [ ] Keyboard shortcuts for card review (1-4 without Enter)
- [ ] Configurable cards per session
- [ ] Dark/light theme toggle
- [ ] Furigana display toggle
- [ ] Compact card view mode

### v2.0.0 - Online Features
- [ ] Cloud sync (progress backup/restore)
- [ ] Community-contributed translations
- [ ] Shared study decks
- [ ] Leaderboard / challenges
- [ ] Mobile companion app (web-based)

---

## Backlog
- [ ] N2/N1 content (vocabulary, kanji, grammar)
- [ ] Handwriting recognition for kanji input
- [ ] Pitch accent data and quiz
- [ ] Conjugation drill mode
- [ ] Reading comprehension passages
- [ ] Kanji stroke order data
- [ ] Integration with external dictionaries (Jisho API)
- [ ] Plugin system for custom quiz types
