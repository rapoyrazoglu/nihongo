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

REPO = "rapoyrazoglu/nihongo"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"


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


def check_update(quiet=False):
    """Check latest version from GitHub. Returns (latest_version, download_url) or None."""
    try:
        ctx = _ssl_context()
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

    if _parse_version(latest) <= _parse_version(__version__):
        if not quiet:
            print(t("update.already_latest", version=__version__))
        return None

    asset_name = _get_asset_name()
    if not asset_name:
        if not quiet:
            print(t("update.no_binary", platform=platform.system()))
        return None

    for asset in data.get("assets", []):
        if asset["name"] == asset_name:
            return latest, asset["browser_download_url"]

    if not quiet:
        print(t("update.asset_not_found", asset=asset_name))
    return None


def do_update():
    """Download and apply update."""
    result = check_update(quiet=False)
    if result is None:
        return False

    latest, url = result
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

    # Write to temp file, then replace
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", prefix="nihongo_update_")
    try:
        os.write(fd, data)
        os.close(fd)

        # Make executable
        os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Replace old binary with new
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

        print(f"\n{t('update.success', version=latest)}")
        print(t("update.restart"))
        return True

    except Exception as e:
        print(t("update.failed", error=e))
        # Restore backup if exists
        if os.path.exists(backup_path) and not os.path.exists(exe_path):
            os.replace(backup_path, exe_path)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False
