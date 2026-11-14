# Respawn Studios Homebrew Tap

Install Traverse from our official tap:

```sh
brew install --cask respawn-studios/tap/traverse
```

Traverse is a free, open-source Mac file explorer with tabs, panes, server
connections, archives and a native text editor. This release requires **Apple
silicon and macOS 15 or later**. Intel and Universal builds are not yet available.

The cask downloads the same signed, notarized installer offered on
[GitHub Releases](https://github.com/Respawn-Studios/Traverse/releases), with its
SHA-256 checked by Homebrew. The studio's digest-named download route redirects
to that exact GitHub release asset. No quarantine bypass is used.

## Updates and removal

```sh
brew update
brew upgrade --cask traverse
brew uninstall --cask traverse
```

Uninstall removes the application. It does not remove your profiles, saved
versions, recovery records or Keychain entries. Finish pending operations before
removing an earlier beta. The direct edition keeps separate local app data.

If you installed Traverse manually, finish your work and quit it before changing
installation methods. Homebrew may refuse to replace an existing application;
keep its data and avoid force or zap options just to get past that check.
For an identical existing app, Homebrew can adopt it with:

```sh
brew install --cask --adopt respawn-studios/tap/traverse
```

## Source and help

- [Traverse source and GPLv3 license](https://github.com/Respawn-Studios/Traverse)
- [Feature guide](https://github.com/Respawn-Studios/Traverse/blob/main/docs/guides/features.md)
- [Report a problem](https://github.com/Respawn-Studios/Traverse/issues)
- [Discord](https://discord.gg/UdKp2uQBQy)
- [Buy the studio a coffee](https://buymeacoffee.com/respawnstudios)

Support is optional. Every Traverse feature stays free.

The original cask and documentation in this tap are provided under the
[MIT license](LICENSE). Traverse itself is licensed under GPLv3, with third-party
notices included in its source and application.
