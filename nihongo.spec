# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for nihongo - JLPT öğrenme uygulaması."""

import os
import sys
import glob

block_cipher = None
ROOT = os.path.dirname(os.path.abspath(SPEC))

# UPX/strip Windows'ta Python DLL'ini bozuyor (LoadLibrary failure).
# Sadece Linux/macOS'te kullan; Windows'ta binary biraz büyür ama çalışır.
USE_UPX = sys.platform != 'win32'
USE_STRIP = sys.platform != 'win32'

# rich unicode data modülleri dinamik yükleniyor, PyInstaller yakalayamıyor
_rich_unicode = []
try:
    import rich._unicode_data
    _ud_dir = os.path.dirname(rich._unicode_data.__file__)
    for f in glob.glob(os.path.join(_ud_dir, 'unicode*.py')):
        name = os.path.basename(f).removesuffix('.py')
        _rich_unicode.append(f'rich._unicode_data.{name}')
except ImportError:
    pass

a = Analysis(
    ['src/nihongo.py'],
    pathex=[os.path.join(ROOT, 'src')],
    binaries=[],
    datas=[
        ('src/data/*.json', 'data'),
        ('src/lang/*.json', 'lang'),
        ('migrations/*.sql', 'migrations'),
    ],
    hiddenimports=_rich_unicode,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='nihongo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=USE_STRIP,
    upx=USE_UPX,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, 'assets', 'nihongo.ico'),
)
