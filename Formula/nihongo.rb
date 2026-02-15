class Nihongo < Formula
  desc "JLPT Japanese learning app - SRS, quiz, kanji, grammar"
  homepage "https://github.com/rapoyrazoglu/nihongo"
  version "1.6.0-beta"
  license "MIT"

  on_macos do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-macos"
    sha256 "ac97e9411b50aae772ee4a4b487b3d3b7cec35d5aec16fd65fc0ebd9b04dbe00"
  end

  on_linux do
    url "https://github.com/rapoyrazoglu/nihongo/releases/download/v#{version}/nihongo-linux"
    sha256 "41b16a58adf2aa85424b4523b312743e5f099cc27985f51d2317fb582b887d8b"
  end

  def install
    binary = OS.mac? ? "nihongo-macos" : "nihongo-linux"
    bin.install binary => "nihongo"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/nihongo --version")
  end
end
