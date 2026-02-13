#!/bin/bash
# Fcitx5 + Mozc Kurulum Scripti (Arch Linux)
# Japonca yazma desteği için gerekli paketleri kurar ve yapılandırır.
#
# Kullanım: bash setup_fcitx5.sh

set -e

echo "=== Fcitx5 + Mozc Kurulumu ==="
echo ""

# Paketleri kur
echo "[1/3] Paketler yükleniyor..."
sudo pacman -S --needed fcitx5 fcitx5-mozc fcitx5-gtk fcitx5-qt fcitx5-configtool

# Ortam değişkenlerini ayarla
echo ""
echo "[2/3] Ortam değişkenleri ayarlanıyor..."

# ~/.pam_environment (genel yöntem)
ENV_FILE="$HOME/.pam_environment"
if [ ! -f "$ENV_FILE" ] || ! grep -q "XMODIFIERS" "$ENV_FILE" 2>/dev/null; then
    cat >> "$ENV_FILE" << 'EOF'
GTK_IM_MODULE DEFAULT=fcitx
QT_IM_MODULE  DEFAULT=fcitx
XMODIFIERS    DEFAULT=@im=fcitx
EOF
    echo "  ~/.pam_environment güncellendi."
else
    echo "  ~/.pam_environment zaten ayarlı."
fi

# Bash/Zsh profili için de ekle
for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC_FILE" ] && ! grep -q "GTK_IM_MODULE=fcitx" "$RC_FILE" 2>/dev/null; then
        cat >> "$RC_FILE" << 'EOF'

# Fcitx5 Japonca giriş
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
EOF
        echo "  $(basename $RC_FILE) güncellendi."
    fi
done

# Fcitx5 yapılandırmasını oluştur
echo ""
echo "[3/3] Fcitx5 yapılandırması..."
mkdir -p "$HOME/.config/fcitx5/profile"

# Autostart
mkdir -p "$HOME/.config/autostart"
if [ -f /usr/share/applications/org.fcitx.Fcitx5.desktop ]; then
    cp /usr/share/applications/org.fcitx.Fcitx5.desktop "$HOME/.config/autostart/"
    echo "  Otomatik başlatma ayarlandı."
fi

echo ""
echo "=== Kurulum Tamamlandı ==="
echo ""
echo "Sonraki adımlar:"
echo "  1. Sistemi yeniden başlatın veya çıkış/giriş yapın"
echo "  2. Fcitx5 Configuration Tool'u açın (fcitx5-configtool)"
echo "  3. Input Method bölümünden 'Mozc' ekleyin"
echo "  4. Ctrl+Space ile Japonca/İngilizce arasında geçiş yapın"
echo ""
echo "Test: Herhangi bir metin alanında Ctrl+Space yaparak"
echo "      ローマ字 (romaji) ile Japonca yazabilirsiniz."
