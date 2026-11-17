cask "traverse" do
  version "0.3.0,99"

  on_arm do
    sha256 "0d6fd5ed62a2f1cee2ed2acbf0de0399dce0c06833f8feec1bfa3e196d635fe2"
    url "https://respawn-studios.com/products/traverse/direct-updates/archives/0d6fd5ed62a2f1cee2ed2acbf0de0399dce0c06833f8feec1bfa3e196d635fe2.dmg"
  end

  on_intel do
    sha256 "a38603594e65410d5763fc40ee0873e2245e62b1ca4a5a80e13305a066fe911b"
    url "https://respawn-studios.com/products/traverse/direct-updates-intel/archives/a38603594e65410d5763fc40ee0873e2245e62b1ca4a5a80e13305a066fe911b.dmg"
  end

  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on macos: :sequoia

  app "Traverse.app"
end
