# Maintainer: rapoyrazoglu
pkgname=nihongo
pkgver=1.5.3
pkgrel=1
pkgdesc="JLPT Japanese learning app - SRS, quiz, kanji, grammar"
arch=('x86_64')
url="https://github.com/rapoyrazoglu/nihongo"
license=('MIT')
depends=('espeak-ng')
optdepends=('fcitx5-mozc: Japanese input')
source=("${pkgname}-${pkgver}::${url}/releases/download/v${pkgver}/nihongo-linux")
sha256sums=('ecb9632903e080885bcb18728093ee3befd219dec6cce88673c356161add1675')

package() {
    install -Dm755 "${srcdir}/${pkgname}-${pkgver}" "${pkgdir}/usr/bin/nihongo"
}
