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
sha256sums=('14a9589905b6309c704079b409483b4db13db0756ec991aa714e0c71e8bc6368')

package() {
    install -Dm755 "${srcdir}/${pkgname}-${pkgver}" "${pkgdir}/usr/bin/nihongo"
}
