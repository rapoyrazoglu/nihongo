"""Sıfır bağımlılık TTS modülü - Sistem TTS ile Japonca sesli okuma.

macOS: say -v Kyoko
Linux: espeak -v ja (veya espeak-ng)
Windows: PowerShell SAPI
Hiçbiri yoksa sessizce atlar. Non-blocking (Popen).
"""

import subprocess
import sys
import shutil

_engine = None  # "say" | "espeak" | "espeak-ng" | "sapi" | None


def _detect_engine():
    """Kullanılabilir TTS motorunu tespit et (bir kez)."""
    global _engine
    if _engine is not None:
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


def speak(text):
    """Verilen Japonca metni sesli oku. Non-blocking, hata durumunda sessizce atlar."""
    if not text or not text.strip():
        return

    engine = _detect_engine()
    if not engine:
        return

    try:
        if engine == "say":
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
