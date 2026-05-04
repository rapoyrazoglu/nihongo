class Nihongo < Formula
  desc "JLPT Japanese learning app - SRS, quiz, kanji, grammar"
  homepage "https://github.com/rapoyrazoglu/nihongo"
  version "1.7.0-beta"
  license "MIT"

  on_macos do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-macos"
    sha256 "d09b89d30692be5924336ae03a0362a5b7da513bc9bc64e779f17a87ae6da91b"
  end

  on_linux do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-linux"
    sha256 "82487c6dd5cff255763768ec8296066c64dbd0bdec039d89c8832008525ca7fb"
  end

  def install
    binary = OS.mac? ? "nihongo-macos" : "nihongo-linux"
    bin.install binary => "nihongo"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/nihongo --version")
  end
end
