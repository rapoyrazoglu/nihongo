#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== nihongo build ==="

# venv varsa aktive et
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# PyInstaller yoksa yükle
if ! python -m PyInstaller --version &>/dev/null; then
    echo "PyInstaller yükleniyor..."
    pip install pyinstaller
fi

echo "Binary derleniyor..."
python -m PyInstaller nihongo.spec --clean --noconfirm

echo ""
echo "Build tamamlandı: dist/nihongo"
echo "Test: ./dist/nihongo --version"
