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

### v2.0.0 - Full Backend Platform (Offline-First Sync)
**Architecture: production-ready, multi-service, API-gateway fronted.**

Infrastructure
- [ ] API Gateway (AWS API Gateway / Cloudflare API / Kong)
      — rate limiting, auth, routing, observability
- [ ] Auth service: OAuth2 (Google, Apple), email/password, JWT
- [ ] User service: profile, preferences, account lifecycle
- [ ] Sync service: delta sync API (push/pull diffs of user data)
- [ ] Content service: optional remote content updates (new lessons,
      patches) without app rebuild
- [ ] Notification service: scheduled push for streak/due reviews
- [ ] Analytics pipeline (event ingestion → warehouse) — opt-in only
- [ ] CDN for static assets (TTS audio packs, images, mascot frames)
- [ ] Postgres primary DB; Redis cache; S3 for blobs
- [ ] CI/CD: per-service deploy, blue-green, automated rollback
- [ ] Observability: structured logs, metrics (Prometheus), traces (OTel)
- [ ] Status page + on-call rotation

Client integration
- [ ] Local SQLite remains source of truth offline (CLI + future apps)
- [ ] Sync engine: only user data (reviews, stats, lesson_progress)
      — content stays embedded for offline-first
- [ ] Conflict resolution: per-row last-write-wins with timestamps;
      conflict log for audit
- [ ] Background sync on app start + every N minutes when online
- [ ] Manual "sync now" + "force pull" / "force push" controls

Compliance & user trust
- [ ] Encrypted at rest (KMS-managed keys)
- [ ] TLS 1.3 everywhere, HSTS, CSP for any web surface
- [ ] GDPR-compliant: export-all-data (JSON dump), full delete-account flow
- [ ] Privacy policy + terms of service published before launch
- [ ] Open-source the API spec (OpenAPI 3) for transparency

### v2.1.0 - iOS Native App (Swift / SwiftUI)
- [ ] Native iOS app, Swift + SwiftUI (not cross-platform)
- [ ] Reuse JSON content as embedded asset
- [ ] Port SRS algorithm to Swift (~100 lines, straightforward)
- [ ] Local SQLite via GRDB.swift
- [ ] Mobile-first UI: swipe gestures for review, big-tap targets
- [ ] Push notifications for due reviews (UNUserNotificationCenter)
- [ ] Offline-first (same sync engine as v2.0, ported to Swift)
- [ ] CloudKit fallback for iCloud-only users (no Supabase account)
- [ ] App Store submission, TestFlight beta
- [ ] Feature parity with desktop CLI before moving to v2.2

### v2.2.0 - Mascot & Branding
- [ ] 2D mascot draft in Claude Design / Figma
      (kawaii style, candidates: shiba inu / sensei chibi / tanuki)
- [ ] 3D model in Blender (rigged for animation)
- [ ] Mascot states: idle, celebrating (correct answer),
      sad (wrong), studying, sleeping (streak broken)
- [ ] App icon redesign with mascot (iOS + desktop)
- [ ] Animated splash screen / first-run wizard
- [ ] Optional mascot toggle (some users prefer minimal UI)

### v2.3.0 - Android Native App (Java)
- [ ] Native Android app, Java (not Kotlin, not cross-platform)
- [ ] Started ONLY after iOS reaches full feature parity in v2.1
- [ ] Same architecture as iOS: embedded JSON content, local Room/SQLite,
      ported SRS, sync engine
- [ ] Material Design UI matching iOS feel where reasonable
- [ ] Push notifications via FCM
- [ ] Offline-first sync (shared backend with v2.0/v2.1)
- [ ] Play Store submission, internal testing track first

### v2.4.0 - Community Features
- [ ] Community-contributed translations (PR-based)
- [ ] Shared study decks (user-uploaded)
- [ ] Leaderboard / weekly challenges
- [ ] Friend list, side-by-side progress comparison

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
