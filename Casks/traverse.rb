cask "traverse" do
  version "0.1.1,94"
  sha256 "16fcf1df778a96ac744bbc18500d479bf9e5a17bb6028bfba08603678186b603"

  url "https://respawn-studios.com/products/traverse/direct-updates/archives/16fcf1df778a96ac744bbc18500d479bf9e5a17bb6028bfba08603678186b603.dmg"
  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on arch: :arm64
  depends_on macos: :sequoia

  app "Traverse.app"
end
