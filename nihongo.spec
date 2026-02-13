# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for nihongo - JLPT öğrenme uygulaması."""

import os
import glob

block_cipher = None
ROOT = os.path.dirname(os.path.abspath(SPEC))

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
    ['nihongo.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('data/*.json', 'data'),
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
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
