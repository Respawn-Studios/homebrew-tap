# Respawn Studios Homebrew Tap

Install Traverse from our official tap:

```sh
brew install --cask respawn-studios/tap/traverse
```

Traverse is a free, open-source Mac file explorer with tabs, panes, server
connections, archives and a native text editor. It supports **Apple Silicon and Intel Macs on macOS 15 or later**.
Homebrew selects the matching signed package automatically. Intel editor, ZIP
and scanner checks passed under Rosetta; physical Intel testing is still welcome.

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

## Keeping the tap current

The [update workflow](.github/workflows/update-traverse.yml) checks the latest
full Traverse release hourly. It can also be run manually from Actions.
Previews and drafts stay out of the tap. Before changing the cask, it checks
both architecture catalogs, their matching source kit, GitHub asset digests and
the actual installers served by the download routes. A release-specific
publisher acceptance comment in the official release notes must also cover the cask, both installer hashes, parsing for
both architectures and a real ARM install with cold startup. An incomplete release
leaves the existing cask in place and makes the workflow fail visibly. The comment
records the publisher’s completed checks; it is separate from immutable asset
metadata and is not an independent test service.

The workflow uses this repository's temporary GitHub token; no personal token
or extra secret is needed. Homebrew users still choose when to run `brew update`
and `brew upgrade`. To check a proposed update locally without publishing:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B tools/update_traverse.py
```

The original cask and documentation in this tap are provided under the
[MIT license](LICENSE). Traverse itself is licensed under GPLv3, with third-party
notices included in its source and application.
