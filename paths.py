"""Merkezi path çözümlemesi - frozen (PyInstaller) vs source ayrımı."""

import os
import sys

# PyInstaller ile derlenmiş mi?
FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    # PyInstaller one-file: veriler _MEIPASS temp dizininde
    _BASE_DIR = sys._MEIPASS
else:
    # Kaynak koddan çalışıyor
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JSON veri dosyaları dizini (data/*.json)
DATA_DIR = os.path.join(_BASE_DIR, "data")

# Veritabanı: kullanıcı dizininde (OS'e göre)
if sys.platform == "win32":
    _DB_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "nihongo")
elif sys.platform == "darwin":
    _DB_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "nihongo")
else:
    _DB_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "nihongo")
os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, "nihongo.db")
