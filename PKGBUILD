# Maintainer: rapoyrazoglu
pkgname=nihongo
pkgver=1.7.0-beta
pkgrel=1
pkgdesc="JLPT Japanese learning app - SRS, quiz, kanji, grammar"
arch=('x86_64')
url="https://github.com/rapoyrazoglu/nihongo"
license=('MIT')
depends=('espeak-ng')
optdepends=('fcitx5-mozc: Japanese input')
source=("${pkgname}-${pkgver}::${url}/releases/download/v${pkgver}/nihongo-linux")
sha256sums=('82487c6dd5cff255763768ec8296066c64dbd0bdec039d89c8832008525ca7fb')

package() {
    install -Dm755 "${srcdir}/${pkgname}-${pkgver}" "${pkgdir}/usr/bin/nihongo"
}
