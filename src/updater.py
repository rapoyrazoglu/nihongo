"""Self-update module - download latest version from GitHub releases."""

import json
import os
import platform
import ssl
import stat
import sys
import tempfile
import urllib.request

from version import __version__
from i18n import t


def _ssl_context():
    """SSL context that works in PyInstaller bundles."""
    _CA_PATHS = [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/ca-certificates/extracted/tls-ca-bundle.pem",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/ca-bundle.pem",
        "/etc/ssl/cert.pem",
        "/usr/local/share/certs/ca-root-nss.crt",
    ]
    # Explicitly load known CA file (PyInstaller bundles can't find them)
    for ca_path in _CA_PATHS:
        if os.path.exists(ca_path):
            try:
                return ssl.create_default_context(cafile=ca_path)
            except Exception:
                continue
    # Try certifi
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # Try default (works on macOS / Windows)
    try:
        return ssl.create_default_context()
    except Exception:
        pass
    # Last resort: unverified
    ctx = ssl._create_unverified_context()
    return ctx

from paths import _DB_DIR

REPO = "rapoyrazoglu/nihongo"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
API_URL_ALL = f"https://api.github.com/repos/{REPO}/releases"
_UPDATE_INFO = os.path.join(_DB_DIR, ".update_info.json")


def _get_last_update_time():
    """Kaydedilmiş son güncelleme zamanını oku."""
    try:
        with open(_UPDATE_INFO, "r") as f:
            info = json.load(f)
        return info.get("asset_updated", "")
    except (OSError, json.JSONDecodeError):
        return ""


def _save_update_time(asset_updated):
    """Güncelleme zamanını kaydet."""
    try:
        with open(_UPDATE_INFO, "w") as f:
            json.dump({"asset_updated": asset_updated}, f)
    except OSError:
        pass


def _is_remote_newer(asset_updated):
    """Remote asset bizim kayıtlı zamandan yeni mi?"""
    if not asset_updated:
        return False
    last = _get_last_update_time()
    if not last:
        # İlk kez: binary dosya zamanını kullan
        exe = sys.executable if getattr(sys, "frozen", False) else None
        if exe and os.path.exists(exe):
            from datetime import datetime, timezone
            mtime = os.path.getmtime(exe)
            local_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            # GitHub API zamanı: "2026-02-15T08:52:00Z"
            try:
                remote_dt = datetime.fromisoformat(asset_updated.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return False
            return remote_dt > local_dt
        return False
    return asset_updated > last


def _get_asset_name():
    """Return correct binary name for this platform."""
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


_BG_RESULT_PATH = os.path.join(_DB_DIR, ".update_check.json")
_BG_TTL_SECONDS = 6 * 3600  # 6 saat


def _bg_load_cached():
    """Önceden kaydedilmiş arka plan sonucu (TTL içinde ise) döner."""
    try:
        with open(_BG_RESULT_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        from datetime import datetime, timezone
        ts = datetime.fromisoformat(cached["checked_at"])
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age < _BG_TTL_SECONDS:
            return cached
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        pass
    return None


def _bg_save(latest, download_url):
    """Arka plan kontrol sonucunu kaydet."""
    try:
        from datetime import datetime, timezone
        os.makedirs(os.path.dirname(_BG_RESULT_PATH), exist_ok=True)
        with open(_BG_RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "latest": latest,
                "download_url": download_url,
                "current": __version__,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }, f)
    except OSError:
        pass


def check_update_async(include_beta=None):
    """GitHub'dan en son sürümü arka planda kontrol et (non-blocking).
    Cache'lenmiş sonuç varsa hemen onu döner, yoksa bir thread başlatır.
    Returns: dict with 'latest', 'download_url', 'current' if newer available, else None.
    Thread kendi cache'ini diske yazar; bir sonraki açılışta hemen görünür.
    """
    if include_beta is None:
        # Eğer kullanıcı zaten beta kullanıyorsa beta'da kalsın
        include_beta = "-beta" in __version__ or "-alpha" in __version__ or "-rc" in __version__

    cached = _bg_load_cached()
    if cached:
        # Cache hâlâ taze ve gerçekten yeni sürüm varsa onu döndür
        try:
            latest_clean = cached["latest"].replace("-beta", "").replace("-alpha", "").replace("-rc", "")
            current_clean = __version__.replace("-beta", "").replace("-alpha", "").replace("-rc", "")
            if _parse_version(latest_clean) > _parse_version(current_clean):
                return cached
        except (KeyError, ValueError):
            pass
        # Cache var ama yeni sürüm yok — yine de erken çık
        return None

    # Cache yok / süresi dolmuş — arka planda kontrol başlat
    import threading

    def _worker():
        try:
            res = check_update(quiet=True, include_beta=include_beta)
            if res:
                latest, download_url, _ = res
                _bg_save(latest, download_url)
        except Exception:
            pass

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return None  # Bu launch'ta henüz sonuç yok; bir sonraki açılışta görünür


def check_update(quiet=False, include_beta=False):
    """Check latest version from GitHub. Returns (latest_version, download_url) or None."""
    try:
        ctx = _ssl_context()
        if include_beta:
            req = urllib.request.Request(API_URL_ALL, headers={"User-Agent": "nihongo-updater"})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                releases = json.loads(resp.read().decode())
            if not releases:
                return None
            data = releases[0]  # en yeni release (beta dahil)
        else:
            req = urllib.request.Request(API_URL, headers={"User-Agent": "nihongo-updater"})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                data = json.loads(resp.read().decode())
    except Exception as e:
        if not quiet:
            print(t("update.check_failed", error=e))
        return None

    latest = data.get("tag_name", "").lstrip("v")
    if not latest:
        return None

    current_clean = __version__.replace("-beta", "").replace("-alpha", "")
    latest_clean = latest.replace("-beta", "").replace("-alpha", "")

    if _parse_version(latest_clean) < _parse_version(current_clean):
        if not quiet:
            print(t("update.already_latest", version=__version__))
        return None

    asset_name = _get_asset_name()
    if not asset_name:
        if not quiet:
            print(t("update.no_binary", platform=platform.system()))
        return None

    # Asset'i bul
    download_url = None
    asset_updated = None
    for asset in data.get("assets", []):
        if asset["name"] == asset_name:
            download_url = asset["browser_download_url"]
            asset_updated = asset.get("updated_at", "")
            break

    if not download_url:
        if not quiet:
            print(t("update.asset_not_found", asset=asset_name))
        return None

    # Aynı versiyon ise build zamanını karşılaştır
    if latest == __version__:
        if not _is_remote_newer(asset_updated):
            if not quiet:
                print(t("update.already_latest", version=__version__))
            return None

    if _parse_version(latest_clean) == _parse_version(current_clean) and latest == current_clean:
        if not _is_remote_newer(asset_updated):
            if not quiet:
                print(t("update.already_latest", version=__version__))
            return None

    return latest, download_url, asset_updated


def do_update(include_beta=False):
    """Download and apply update."""
    result = check_update(quiet=False, include_beta=include_beta)
    if result is None:
        return False

    latest, url, asset_time = result
    print(f"\n{t('update.found', current=__version__, latest=latest)}")

    # Find binary location
    exe_path = sys.executable if getattr(sys, "frozen", False) else None
    if not exe_path:
        print(t("update.source_only"))
        print(t("update.source_hint"))
        return False

    print(t("update.downloading", url=url))
    try:
        ctx = _ssl_context()
        req = urllib.request.Request(url, headers={"User-Agent": "nihongo-updater"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()
    except Exception as e:
        print(t("update.download_failed", error=e))
        return False

    # Dizine yazma izni var mı kontrol et
    exe_dir = os.path.dirname(exe_path)
    needs_sudo = not os.access(exe_dir, os.W_OK)

    # Temp dosyayı yazılabilir bir dizine oluştur
    tmp_dir = exe_dir if not needs_sudo else tempfile.gettempdir()
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", prefix="nihongo_update_", dir=tmp_dir)
    try:
        os.write(fd, data)
        os.close(fd)

        # Make executable
        os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        if needs_sudo:
            # sudo ile kopyala (macOS /usr/local/bin gibi dizinler için)
            import subprocess
            print(t("update.need_sudo"))
            ret = subprocess.call(["sudo", "cp", tmp_path, exe_path])
            if ret != 0:
                print(t("update.permission_error"))
                os.unlink(tmp_path)
                return False
            subprocess.call(["sudo", "chmod", "+x", exe_path])
            os.unlink(tmp_path)
        else:
            # Normal güncelleme
            backup_path = exe_path + ".bak"
            try:
                os.replace(exe_path, backup_path)
            except PermissionError:
                print(t("update.permission_error"))
                os.unlink(tmp_path)
                return False

            os.replace(tmp_path, exe_path)
            os.chmod(exe_path, os.stat(exe_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            # Remove backup
            try:
                os.unlink(backup_path)
            except OSError:
                pass

        # Güncelleme zamanını kaydet
        if asset_time:
            _save_update_time(asset_time)

        print(f"\n{t('update.success', version=latest)}")
        print(t("update.restart"))
        return True

    except Exception as e:
        print(t("update.failed", error=e))
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False


def do_uninstall():
    """Nihongo'yu sistemden kaldır."""
    exe_path = sys.executable if getattr(sys, "frozen", False) else None

    s = platform.system().lower()
    data_dir = os.path.join(
        os.path.expanduser("~"),
        "Library/Application Support/nihongo" if s == "darwin"
        else ".local/share/nihongo"
    )
    if s == "windows":
        data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "nihongo")

    print(f"\n{t('delete.confirm')}")
    if exe_path:
        print(f"  - {exe_path}")
    print(f"  - {data_dir}")
    print()

    try:
        answer = input(f"{t('delete.ask')} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer not in ("y", "yes", "e", "evet"):
        print(t("delete.cancelled"))
        return False

    import shutil

    # Veri dizinini sil
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)
        print(f"  {t('delete.removed')}: {data_dir}")

    # Binary'yi sil
    if exe_path and os.path.exists(exe_path):
        exe_dir = os.path.dirname(exe_path)
        needs_sudo = not os.access(exe_dir, os.W_OK)
        if needs_sudo:
            import subprocess
            print(t("update.need_sudo"))
            subprocess.call(["sudo", "rm", "-f", exe_path])
        else:
            os.unlink(exe_path)
        print(f"  {t('delete.removed')}: {exe_path}")

    print(f"\n{t('delete.done')}")
    return True
