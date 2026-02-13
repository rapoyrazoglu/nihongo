# Nihongo Master - Changelog & Roadmap

---

## Released

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

## Planned

### v1.6.0 - Content Expansion
- [ ] N1/N2 vocabulary expansion (target: 3000+ words)
- [ ] N1/N2 kanji expansion (target: 1000+ kanji)
- [ ] Advanced grammar patterns (N2/N1)
- [ ] Example sentences for all vocabulary
- [ ] Kanji stroke order data

### v1.7.0 - Study Enhancements
- [ ] Custom study decks (user-created word lists)
- [ ] Cloze deletion quiz mode (fill in the blank)
- [ ] Listening quiz mode (audio -> meaning)
- [ ] Sentence construction quiz
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
- [ ] Handwriting recognition for kanji input
- [ ] Pitch accent data and quiz
- [ ] Conjugation drill mode
- [ ] Reading comprehension passages
- [ ] Integration with external dictionaries (Jisho API)
- [ ] Plugin system for custom quiz types
