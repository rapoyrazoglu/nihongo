class Nihongo < Formula
  desc "JLPT Japanese learning app - SRS, quiz, kanji, grammar"
  homepage "https://github.com/rapoyrazoglu/nihongo"
  version "1.4.0"
  license "MIT"

  on_macos do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-macos"
    sha256 "41337d64961d035292553425321e1d583788dbba54c33deb8e7de158d36cc868"
  end

  on_linux do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-linux"
    sha256 "df5d67d1924e4291ff3857801b30a5e582270ebc6725cde6da1ba2300a63be31"
  end

  def install
    binary = OS.mac? ? "nihongo-macos" : "nihongo-linux"
    bin.install binary => "nihongo"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/nihongo --version")
  end
end
