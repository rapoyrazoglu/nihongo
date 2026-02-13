"""Self-update module - GitHub releases'dan en son surumu indir."""

import json
import os
import platform
import ssl
import stat
import sys
import tempfile
import urllib.request

from version import __version__


def _ssl_context():
    """SSL context that works in PyInstaller bundles."""
    # Try system certs first
    try:
        ctx = ssl.create_default_context()
        # Test if it actually works
        return ctx
    except Exception:
        pass
    # Try certifi bundle
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # Fallback: try common system CA paths
    for ca_path in [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/ca-bundle.pem",
        "/etc/ssl/cert.pem",
    ]:
        if os.path.exists(ca_path):
            return ssl.create_default_context(cafile=ca_path)
    # Last resort
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

REPO = "rapoyrazoglu/nihongo"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"


def _get_asset_name():
    """Platform'a gore dogru binary adini dondur."""
    s = platform.system().lower()
    if s == "linux":
        return "nihongo-linux"
    elif s == "darwin":
        return "nihongo-macos"
    elif s == "windows":
        return "nihongo-windows.exe"
    return None


def _parse_version(v):
    """'1.5.0' -> (1, 5, 0) tuple."""
    return tuple(int(x) for x in v.lstrip("v").split("."))


def check_update(quiet=False):
    """GitHub'dan son surumu kontrol et. (latest_version, download_url) veya None dondur."""
    try:
        ctx = _ssl_context()
        req = urllib.request.Request(API_URL, headers={"User-Agent": "nihongo-updater"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        if not quiet:
            print(f"Surum kontrolu basarisiz: {e}")
        return None

    latest = data.get("tag_name", "").lstrip("v")
    if not latest:
        return None

    if _parse_version(latest) <= _parse_version(__version__):
        if not quiet:
            print(f"Zaten en guncel surum: v{__version__}")
        return None

    asset_name = _get_asset_name()
    if not asset_name:
        if not quiet:
            print(f"Bu platform icin binary bulunamadi: {platform.system()}")
        return None

    for asset in data.get("assets", []):
        if asset["name"] == asset_name:
            return latest, asset["browser_download_url"]

    if not quiet:
        print(f"Release'de {asset_name} bulunamadi.")
    return None


def do_update():
    """Guncellemeyi indir ve uygula."""
    result = check_update(quiet=False)
    if result is None:
        return False

    latest, url = result
    print(f"\nYeni surum bulundu: v{__version__} -> v{latest}")

    # Binary'nin yerini bul
    exe_path = sys.executable if getattr(sys, "frozen", False) else None
    if not exe_path:
        print("Guncelleme sadece derlenmi binary icin destekleniyor.")
        print(f"Kaynak koddan calisiyorsaniz: git pull && pip install -r requirements.txt")
        return False

    print(f"Indiriliyor: {url}")
    try:
        ctx = _ssl_context()
        req = urllib.request.Request(url, headers={"User-Agent": "nihongo-updater"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Indirme basarisiz: {e}")
        return False

    # Gecici dosyaya yaz, sonra uzerine kopyala
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", prefix="nihongo_update_")
    try:
        os.write(fd, data)
        os.close(fd)

        # Calistirilabilir yap
        os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Eski binary'yi yenisiyle degistir
        backup_path = exe_path + ".bak"
        try:
            os.replace(exe_path, backup_path)
        except PermissionError:
            print(f"Izin hatasi. Deneyin: sudo nihongo --update")
            os.unlink(tmp_path)
            return False

        os.replace(tmp_path, exe_path)
        os.chmod(exe_path, os.stat(exe_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Backup'i sil
        try:
            os.unlink(backup_path)
        except OSError:
            pass

        print(f"\nGuncelleme basarili! v{latest}")
        print("Uygulamayi yeniden baslatin: nihongo")
        return True

    except Exception as e:
        print(f"Guncelleme basarisiz: {e}")
        # Backup varsa geri yukle
        if os.path.exists(backup_path) and not os.path.exists(exe_path):
            os.replace(backup_path, exe_path)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False
