# Maintainer: rapoyrazoglu
pkgname=nihongo
pkgver=1.4.0
pkgrel=1
pkgdesc="JLPT Japanese learning app - SRS, quiz, kanji, grammar"
arch=('x86_64')
url="https://github.com/rapoyrazoglu/nihongo"
license=('MIT')
depends=('espeak-ng')
optdepends=('fcitx5-mozc: Japanese input')
source=("${pkgname}-${pkgver}::${url}/releases/download/v${pkgver}/nihongo-linux")
sha256sums=('df5d67d1924e4291ff3857801b30a5e582270ebc6725cde6da1ba2300a63be31')

package() {
    install -Dm755 "${srcdir}/${pkgname}-${pkgver}" "${pkgdir}/usr/bin/nihongo"
}
