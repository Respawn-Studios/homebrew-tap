cask "traverse" do
  version "0.4.1,106"

  on_arm do
    sha256 "4bb9c1e9dda94490b0c0c3d32d764b5f4cfb498b5be697f2bf8a2c6fd2a09b11"
    url "https://respawn-studios.com/products/traverse/direct-updates/archives/4bb9c1e9dda94490b0c0c3d32d764b5f4cfb498b5be697f2bf8a2c6fd2a09b11.dmg"
  end

  on_intel do
    sha256 "cdb35991bc60cbbddd5517a4102d8c8e36ad333babf5e0fe1f5ba9fb921d5b4b"
    url "https://respawn-studios.com/products/traverse/direct-updates-intel/archives/cdb35991bc60cbbddd5517a4102d8c8e36ad333babf5e0fe1f5ba9fb921d5b4b.dmg"
  end

  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on macos: :sequoia

  app "Traverse.app"
end
