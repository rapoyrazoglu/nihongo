class Nihongo < Formula
  desc "JLPT Japanese learning app - SRS, quiz, kanji, grammar"
  homepage "https://github.com/rapoyrazoglu/nihongo"
  version "1.7.0-beta"
  license "MIT"

  on_macos do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-macos"
    sha256 "a7d4c852c9ea3f09e22a748ee381099b971eb8d393ca141064d818fd17014ea2"
  end

  on_linux do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-linux"
    sha256 "14a9589905b6309c704079b409483b4db13db0756ec991aa714e0c71e8bc6368"
  end

  def install
    binary = OS.mac? ? "nihongo-macos" : "nihongo-linux"
    bin.install binary => "nihongo"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/nihongo --version")
  end
end
