"""TTS modülü - Japonca sesli okuma.

Öncelik sırası:
1. edge-tts (Microsoft Neural TTS - en iyi kalite, internet gerekir)
2. macOS: say -v Kyoko
3. Linux: espeak-ng -v ja
4. Windows: PowerShell SAPI
Hiçbiri yoksa sessizce atlar.
"""

import os
import subprocess
import sys
import shutil
import tempfile
import threading

_engine = None  # "edge-tts" | "say" | "espeak" | "espeak-ng" | "sapi" | None
_player = None  # "mpv" | "ffplay" | "paplay" | "aplay" | None


def _detect_engine():
    """Kullanılabilir TTS motorunu tespit et (bir kez)."""
    global _engine, _player
    if _engine is not None:
        return _engine

    # edge-tts: neural TTS, en iyi kalite (tüm platformlarda çalışır)
    if shutil.which("edge-tts"):
        # MP3 çalabilecek bir player lazım (mpv veya ffplay)
        for p in ("mpv", "ffplay"):
            if shutil.which(p):
                _player = p
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


def _play_edge_tts(text):
    """edge-tts ile ses üret ve çal (ayrı thread'de)."""
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3", prefix="nihongo_tts_")
        os.close(fd)

        # edge-tts ile MP3 oluştur
        result = subprocess.run(
            ["edge-tts", "--text", text, "--voice", "ja-JP-NanamiNeural",
             "--write-media", tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )

        if result.returncode != 0:
            return

        # Player ile çal
        if _player == "mpv":
            subprocess.run(
                ["mpv", "--no-video", "--really-quiet", tmp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        elif _player == "ffplay":
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
    except (OSError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def speak(text):
    """Verilen Japonca metni sesli oku. Hata durumunda sessizce atlar."""
    if not text or not text.strip():
        return

    engine = _detect_engine()
    if not engine:
        return

    try:
        if engine == "edge-tts":
            # Ayrı thread'de çalıştır (blocking ama UI'yi kilitlemez)
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
