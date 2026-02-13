class Nihongo < Formula
  desc "JLPT Japanese learning app - SRS, quiz, kanji, grammar"
  homepage "https://github.com/rapoyrazoglu/nihongo"
  version "1.5.3"
  license "MIT"

  on_macos do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-macos"
    sha256 "172a5e6ccc2240e9357c11904c1268e473ec738f13b397fc21a08e812dd6d213"
  end

  on_linux do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-linux"
    sha256 "ecb9632903e080885bcb18728093ee3befd219dec6cce88673c356161add1675"
  end

  def install
    binary = OS.mac? ? "nihongo-macos" : "nihongo-linux"
    bin.install binary => "nihongo"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/nihongo --version")
  end
end
