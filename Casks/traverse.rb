cask "traverse" do
  version "0.4.0,105"

  on_arm do
    sha256 "d9fe77874d818dbac33d817bdaf3f2a536a7ff65fe99b04867190bef6ea192c2"
    url "https://respawn-studios.com/products/traverse/direct-updates/archives/d9fe77874d818dbac33d817bdaf3f2a536a7ff65fe99b04867190bef6ea192c2.dmg"
  end

  on_intel do
    sha256 "bd61aecc2137b0fef1f9ae4230c4fb2f9c6c7a7c05130a2886aa4ab64839d6fc"
    url "https://respawn-studios.com/products/traverse/direct-updates-intel/archives/bd61aecc2137b0fef1f9ae4230c4fb2f9c6c7a7c05130a2886aa4ab64839d6fc.dmg"
  end

  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on macos: :sequoia

  app "Traverse.app"
end
