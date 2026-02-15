"""TTS modülü - Japonca sesli okuma.

Öncelik sırası:
1. edge-tts (Microsoft Neural TTS) + cache (ilk seferde üret, sonra offline)
2. macOS: say -v Kyoko
3. Linux: espeak-ng -v ja
4. Windows: PowerShell SAPI

edge-tts yoksa ilk kullanımda otomatik kurulur (pipx veya pip ile).
Üretilen ses dosyaları cache'lenir, sonraki kullanımlarda offline çalışır.
"""

import hashlib
import os
import subprocess
import sys
import shutil
import threading

from paths import _DB_DIR

_engine = None  # "edge-tts" | "say" | "espeak" | "espeak-ng" | "sapi" | None
_player = None  # "mpv" | "ffplay" | None
_setup_attempted = False
_CACHE_DIR = os.path.join(_DB_DIR, "tts_cache")


def _cache_path(text):
    """Metin için cache dosya yolunu döndür."""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return os.path.join(_CACHE_DIR, f"{h}.mp3")


def _auto_install_edge_tts():
    """edge-tts yoksa otomatik kur. True dönerse kurulum başarılı."""
    global _setup_attempted
    if _setup_attempted:
        return False
    _setup_attempted = True

    # pipx ile dene
    if shutil.which("pipx"):
        try:
            result = subprocess.run(
                ["pipx", "install", "edge-tts"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
            if result.returncode == 0 and shutil.which("edge-tts"):
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass

    # pip --user ile dene
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages",
             "edge-tts"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        if result.returncode == 0:
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass

    return False


def _detect_engine():
    """Kullanılabilir TTS motorunu tespit et (bir kez)."""
    global _engine, _player
    if _engine is not None:
        return _engine

    # MP3 çalabilecek player var mı?
    player = None
    for p in ("mpv", "ffplay"):
        if shutil.which(p):
            player = p
            break

    # edge-tts: neural TTS, en iyi kalite
    if player:
        # Cache varsa edge-tts kurulu olmasa bile çalışabilir
        if shutil.which("edge-tts") or os.path.isdir(_CACHE_DIR):
            _player = player
            _engine = "edge-tts"
            return _engine

        # edge-tts yok, otomatik kurmayı dene
        if _auto_install_edge_tts() and shutil.which("edge-tts"):
            _player = player
            _engine = "edge-tts"
            return _engine

    if sys.platform == "darwin":
        if shutil.which("say"):
            _engine = "say"
            return _engine

    if sys.platform.startswith("linux"):
        if shutil.which("espeak-ng"):
            _engine = "espeak-ng"
            return _engine
        if shutil.which("espeak"):
            _engine = "espeak"
            return _engine

    if sys.platform == "win32":
        _engine = "sapi"
        return _engine

    _engine = ""
    return _engine


def _play_file(path):
    """MP3/WAV dosyasını player ile çal."""
    try:
        if _player == "mpv":
            subprocess.run(
                ["mpv", "--no-video", "--really-quiet", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        elif _player == "ffplay":
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
    except (OSError, FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _generate_and_cache(text, cache_file):
    """edge-tts ile ses üret ve cache'e kaydet. Başarılıysa True."""
    if not shutil.which("edge-tts"):
        return False
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        result = subprocess.run(
            ["edge-tts", "--text", text, "--voice", "ja-JP-NanamiNeural",
             "--write-media", cache_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return result.returncode == 0 and os.path.exists(cache_file)
    except (OSError, subprocess.TimeoutExpired):
        return False


def _play_edge_tts(text):
    """Cache'den çal veya üretip cache'le, sonra çal."""
    cache_file = _cache_path(text)

    # Cache'de varsa direkt çal (offline)
    if os.path.exists(cache_file):
        _play_file(cache_file)
        return

    # Yoksa üret, cache'le, çal
    if _generate_and_cache(text, cache_file):
        _play_file(cache_file)


def speak(text):
    """Verilen Japonca metni sesli oku. Hata durumunda sessizce atlar."""
    if not text or not text.strip():
        return

    engine = _detect_engine()
    if not engine:
        return

    try:
        if engine == "edge-tts":
            t = threading.Thread(target=_play_edge_tts, args=(text,), daemon=True)
            t.start()
        elif engine == "say":
            subprocess.Popen(
                ["say", "-v", "Kyoko", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif engine in ("espeak", "espeak-ng"):
            subprocess.Popen(
                [engine, "-v", "ja", "-s", "110", "-a", "200", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif engine == "sapi":
            ps_cmd = (
                f'Add-Type -AssemblyName System.Speech; '
                f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$s.Speak("{text}")'
            )
            subprocess.Popen(
                ["powershell", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except (OSError, FileNotFoundError):
        pass


def download_all_audio(progress_callback=None):
    """Tüm vocab ve kanji okumalarını önceden indir (cache'le).
    progress_callback(current, total) ile ilerleme bildirimi yapılır.
    Returns (cached, skipped, failed) counts."""
    import db

    if not shutil.which("edge-tts"):
        if not _auto_install_edge_tts():
            return 0, 0, -1  # -1 = edge-tts kurulamadı

    os.makedirs(_CACHE_DIR, exist_ok=True)

    # Tüm benzersiz okumaları topla
    texts = set()
    for v in db.get_vocabulary():
        reading = v["reading"] or v["word"] or ""
        if reading.strip():
            texts.add(reading.strip())
    for k in db.get_kanji():
        for field in ("on_yomi", "kun_yomi"):
            val = k[field] or ""
            # Birden fazla okuma virgülle ayrılmış olabilir
            for part in val.split("、"):
                part = part.strip()
                if part:
                    texts.add(part)

    total = len(texts)
    cached = 0
    skipped = 0
    failed = 0

    for i, text in enumerate(sorted(texts)):
        cache_file = _cache_path(text)
        if os.path.exists(cache_file):
            skipped += 1
        elif _generate_and_cache(text, cache_file):
            cached += 1
        else:
            failed += 1

        if progress_callback:
            progress_callback(i + 1, total)

    return cached, skipped, failed
