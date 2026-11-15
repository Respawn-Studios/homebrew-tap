cask "traverse" do
  version "0.2.0,95"

  on_arm do
    sha256 "77d65165c5126b3d3af203e3a34bfa319f8d9df0fe6f830346234168b4db83e0"
    url "https://respawn-studios.com/products/traverse/direct-updates/archives/77d65165c5126b3d3af203e3a34bfa319f8d9df0fe6f830346234168b4db83e0.dmg"
  end

  on_intel do
    sha256 "93204efd61be78af69a177d856f482c85315e996b889f4f46e5f38354cc9c5df"
    url "https://respawn-studios.com/products/traverse/direct-updates-intel/archives/93204efd61be78af69a177d856f482c85315e996b889f4f46e5f38354cc9c5df.dmg"
  end

  name "Traverse"
  desc "Native macOS file explorer"
  homepage "https://respawn-studios.com/products/traverse/"

  depends_on macos: :sequoia

  app "Traverse.app"
end
