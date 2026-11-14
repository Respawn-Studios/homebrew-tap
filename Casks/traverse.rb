cask "traverse" do
  version "0.1.0,93"
  sha256 "4512adfe4b81af80b4eb28c169a3ea3ffd3fe66af23c31174af38ea0d4ed2238"

  url "https://respawn-studios.com/products/traverse/direct-updates/archives/4512adfe4b81af80b4eb28c169a3ea3ffd3fe66af23c31174af38ea0d4ed2238.dmg"
  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on arch: :arm64
  depends_on macos: :sequoia

  app "Traverse.app"
end
