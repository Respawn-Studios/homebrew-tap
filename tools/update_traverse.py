#!/usr/bin/env python3
"""Update the official cask only after immutable release assets agree."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Respawn-Studios/Traverse"
TAP = "Respawn-Studios/homebrew-tap"
API = "https://api.github.com/repos/" + REPOSITORY
ORIGIN = "https://respawn-studios.com/products/traverse/"
PUBLIC_KEY = "MG4sBFr76ad6D4nGo+i2VuZ4hxVMEQZToBUjYyui3IA="
VERSION = r"(?:0|[1-9][0-9]{0,2})(?:\.(?:0|[1-9][0-9]{0,2})){2}"
SHA = re.compile(r"[a-f0-9]{64}\Z")
HOSTS = {"api.github.com", "github.com", "release-assets.githubusercontent.com",
         "objects.githubusercontent.com", "respawn-studios.com"}
JSON_LIMIT, DMG_LIMIT = 1 << 20, 128 << 20


class Refused(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


class Redirects(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, url):
        target = urlsplit(url)
        require(target.scheme == "https" and target.hostname in HOSTS
                and target.port in (None, 443)
                and not target.username and not target.password, "Unexpected download redirect")
        if request.has_header("Authorization"):
            require(target.hostname == "api.github.com", "Refused credential forwarding")
        return super().redirect_request(request, file, code, message, headers, url)


class Client:
    def __init__(self):
        self.opener = build_opener(Redirects())

    def open(self, url):
        parts = urlsplit(url)
        require(parts.scheme == "https" and parts.hostname in HOSTS
                and parts.port in (None, 443)
                and not parts.username and not parts.password, "Unexpected download URL")
        headers = {"User-Agent": "Respawn-Studios-Traverse-Tap"}
        if parts.hostname == "api.github.com":
            headers.update(Accept="application/vnd.github+json", **{"X-GitHub-Api-Version": "2022-11-28"})
            if token := os.environ.get("GITHUB_TOKEN"):
                headers["Authorization"] = "Bearer " + token
        return self.opener.open(Request(url, headers=headers), timeout=45)

    def json(self, url, asset=None):
        with self.open(url) as response:
            data = response.read(JSON_LIMIT + 1)
        require(0 < len(data) <= JSON_LIMIT, "Release JSON exceeds its bound")
        if asset is not None:
            require(len(data) == asset["size"]
                    and "sha256:" + hashlib.sha256(data).hexdigest() == asset["digest"],
                    "Catalog bytes differ from GitHub's release digest")
        return json.loads(data)

    def verify_image(self, url, size, digest):
        total, observed = 0, hashlib.sha256()
        with self.open(url) as response:
            while chunk := response.read(1 << 20):
                total += len(chunk)
                require(total <= size and total <= DMG_LIMIT, "Installer exceeds its declared bound")
                observed.update(chunk)
        require(total == size and observed.hexdigest() == digest, "Installer bytes do not match the release")


def asset_map(release):
    require(release.get("draft") is False and release.get("prerelease") is False
            and release.get("immutable") is True, "Only an immutable full release may update the tap")
    tag = release.get("tag_name", "")
    require(isinstance(tag, str) and re.fullmatch("v" + VERSION, tag), "Unexpected release tag")
    assets = release.get("assets")
    require(isinstance(assets, list) and 1 <= len(assets) <= 32, "Unexpected release inventory")
    result = {}
    for item in assets:
        require(isinstance(item, dict) and isinstance(item.get("name"), str)
                and item["name"] not in result, "Duplicate or invalid release asset")
        result[item["name"]] = item
    return tag[1:], result


def validated_catalogs(release, client):
    version, assets = asset_map(release)
    lanes, build = {}, None
    for arch in ("arm64", "x86_64"):
        pattern = re.compile(r"Traverse-" + re.escape(version) + r"-([1-9][0-9]{0,9})-" + arch + r"-updates\.json\Z")
        matches = [(name, item, pattern.fullmatch(name)) for name, item in assets.items() if pattern.fullmatch(name)]
        require(len(matches) == 1, "Exactly one catalog per architecture is required")
        name, asset, match = matches[0]
        current_build = match[1]
        require(int(current_build) <= 2_147_483_647 and (build is None or build == current_build), "Architecture builds differ")
        build = current_build
        expected_url = f"https://github.com/{REPOSITORY}/releases/download/v{version}/{name}"
        require(asset.get("browser_download_url") == expected_url
                and type(asset.get("size")) is int and 0 < asset["size"] <= JSON_LIMIT
                and isinstance(asset.get("digest"), str) and re.fullmatch(r"sha256:[a-f0-9]{64}", asset["digest"]),
                "Catalog identity differs from the official release")
        catalog = client.json(expected_url, asset)
        require(isinstance(catalog, dict) and catalog.get("schema") == 1 and catalog.get("channel") == "direct-public-free-v1"
                and catalog.get("publicKey") == PUBLIC_KEY, "Unexpected update catalog policy")
        item, app = catalog.get("artifact", {}), catalog.get("app", {})
        filename = f"Traverse-{version}-{build}-{arch}.dmg"
        require(item.get("filename") == filename and item.get("version") == version
                and item.get("build") == build and item.get("architecture") == arch
                and item.get("minimumOS") == "15.0" and type(item.get("bytes")) is int
                and 0 < item["bytes"] <= DMG_LIMIT and isinstance(item.get("sha256"), str)
                and SHA.fullmatch(item["sha256"]), "Invalid installer catalog")
        admission = item.get("admission", {})
        require(app.get("bundleID") == "com.respawnstudios.traverse"
                and app.get("architecture") == arch and app.get("accessPolicy") == "local-user-v1"
                and app.get("releasePurpose") == "direct-shipping-v1"
                and isinstance(app.get("appCDHash"), str)
                and re.fullmatch(r"[a-f0-9]{40}", app["appCDHash"])
                and app["appCDHash"] == admission.get("appCDHash")
                and admission.get("schema") == 1
                and admission.get("bundleID") == "com.respawnstudios.traverse"
                and admission.get("version") == version and admission.get("build") == build
                and admission.get("channel") == "Developer ID" and admission.get("container") == "dmg"
                and admission.get("timestamped") is True
                and admission.get("team") == "CDLNJRG82U" and admission.get("gatekeeper") == "accepted"
                and admission.get("containerGatekeeper") == "accepted"
                and admission.get("stapled") is True and admission.get("containerStapled") is True,
                "Installer admission is incomplete")
        binary = assets.get(filename, {})
        require(binary.get("browser_download_url") == f"https://github.com/{REPOSITORY}/releases/download/v{version}/{filename}"
                and binary.get("size") == item["bytes"] and binary.get("digest") == "sha256:" + item["sha256"],
                "Installer identity differs from GitHub's release digest")
        lanes[arch] = catalog
    require(lanes["arm64"].get("sourceKit") == lanes["x86_64"].get("sourceKit")
            and isinstance(lanes["arm64"].get("sourceKit"), dict)
            and lanes["arm64"].get("buildSourceSHA256") == lanes["x86_64"].get("buildSourceSHA256")
            and isinstance(lanes["arm64"].get("buildSourceSHA256"), dict)
            and bool(lanes["arm64"]["buildSourceSHA256"]), "Architecture source inventories differ")
    source = lanes["arm64"]["sourceKit"]
    require(source.get("format") == "traverse-source-kit-v1"
            and isinstance(source.get("sha256"), str) and SHA.fullmatch(source["sha256"])
            and type(source.get("bytes")) is int and 0 < source["bytes"] <= 256 << 20
            and isinstance(source.get("sourceCommit"), str)
            and re.fullmatch(r"[a-f0-9]{40}", source["sourceCommit"]), "Corresponding source identity is incomplete")
    require(any(item.get("digest") == "sha256:" + source["sha256"] and item.get("size") == source["bytes"]
                and item.get("browser_download_url") == f"https://github.com/{REPOSITORY}/releases/download/v{version}/" + item["name"]
                for item in assets.values()), "Corresponding source is missing from the release")
    return version, build, lanes


def image_url(arch, digest):
    lane = "direct-updates" if arch == "arm64" else "direct-updates-intel"
    return ORIGIN + lane + "/archives/" + digest + ".dmg"


def render(version, build, lanes):
    blocks = []
    for arch, name in (("arm64", "arm"), ("x86_64", "intel")):
        digest = lanes[arch]["artifact"]["sha256"]
        blocks.append(f'  on_{name} do\n    sha256 "{digest}"\n    url "{image_url(arch, digest)}"\n  end')
    return (f'cask "traverse" do\n  version "{version},{build}"\n\n'
            + "\n\n".join(blocks)
            + '\n\n  name "Traverse"\n  desc "Native macOS file explorer"\n'
              f'  homepage "{ORIGIN}"\n\n  depends_on macos: :sequoia\n\n  app "Traverse.app"\nend\n').encode()


def current_recipe(original):
    version = re.search(rb'^  version "(' + VERSION.encode() + rb'),([1-9][0-9]*)"$', original, re.MULTILINE)
    digests = re.findall(rb'^    sha256 "([a-f0-9]{64})"$', original, re.MULTILINE)
    require(version is not None and len(digests) == 2, "Unrecognized current cask")
    current_version, build = version[1].decode(), version[2].decode()
    lanes = {arch: {"artifact": {"sha256": digest.decode()}}
             for arch, digest in zip(("arm64", "x86_64"), digests)}
    require(render(current_version, build, lanes) == original,
            "Current cask has changes that need maintainer review")
    return current_version, build


def accepted_cask(release, client, version, build, lanes, recipe):
    # Publisher attestation stays editable after immutable prerelease assets lock.
    # It is separate from the immutable artifact identities checked above.
    marker = "<!-- traverse-homebrew-acceptance-v1"
    body = release.get("body")
    require(isinstance(body, str) and body.count(marker) == 1,
            "Release needs exactly one Homebrew acceptance record")
    # GitHub's browser form submits textarea line endings as CRLF.
    body = body.replace("\r\n", "\n")
    match = re.search(r"(?m)^<!-- traverse-homebrew-acceptance-v1\n([^\n]{1,4096})\n-->\s*\Z", body)
    require(match is not None, "Malformed Homebrew acceptance record")
    prefix = body[:match.start()]
    fence = None
    for line in prefix.splitlines():
        candidate = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if candidate is None:
            continue
        run, suffix = candidate.groups()
        if fence is None:
            if run[0] != "`" or "`" not in suffix:
                fence = (run[0], len(run))
        elif run[0] == fence[0] and len(run) >= fence[1] and not suffix.strip():
            fence = None
    require(fence is None, "Quoted Homebrew acceptance record")
    raw = match[1]
    proof = json.loads(raw)
    fields = {"schema", "purpose", "version", "build", "caskSHA256", "installerSHA256",
              "bothArchitectureReadall", "arm64InstallAndColdStart"}
    require(isinstance(proof, dict) and set(proof) == fields
            and json.dumps(proof, sort_keys=True, separators=(",", ":")) == raw,
            "Noncanonical Homebrew acceptance record")
    require(type(proof.get("schema")) is int and proof["schema"] == 1
            and proof.get("purpose") == "traverse-homebrew-acceptance-v1"
            and proof.get("version") == version and proof.get("build") == build
            and proof.get("caskSHA256") == hashlib.sha256(recipe).hexdigest()
            and proof.get("installerSHA256") == {a: lanes[a]["artifact"]["sha256"] for a in lanes}
            and proof.get("bothArchitectureReadall") is True
            and proof.get("arm64InstallAndColdStart") is True,
            "Homebrew acceptance does not cover this cask and installer pair")


def update(release, client, target):
    require(not target.is_symlink(), "Redirected cask path")
    original = target.read_bytes()
    version, build, lanes = validated_catalogs(release, client)
    recipe = render(version, build, lanes)
    if recipe == original:
        return False
    current_version, current_build = current_recipe(original)
    require(tuple(map(int, version.split("."))) >= tuple(map(int, current_version.split(".")))
            and int(build) > int(current_build), "Refused an older or reissued build")
    accepted_cask(release, client, version, build, lanes, recipe)
    for arch in ("arm64", "x86_64"):
        item = lanes[arch]["artifact"]
        client.verify_image(image_url(arch, item["sha256"]), item["bytes"], item["sha256"])
    require(not target.is_symlink() and target.read_bytes() == original, "Cask changed during verification")
    fd, name = tempfile.mkstemp(prefix=".traverse-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(recipe); output.flush(); os.fsync(output.fileno())
        os.chmod(name, 0o644)
        os.replace(name, target)
        parent = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return True


def publish(target, previous_blob):
    require(os.environ.get("GITHUB_REPOSITORY") == TAP and os.environ.get("GITHUB_REF") == "refs/heads/main",
            "Publishing is restricted to this tap's main workflow")
    token = os.environ.get("GITHUB_TOKEN")
    require(bool(token), "The repository workflow token is required")
    body = json.dumps({"message": "Update Traverse from its verified full release", "branch": "main",
                       "sha": previous_blob, "content": base64.b64encode(target.read_bytes()).decode()}).encode()
    request = Request("https://api.github.com/repos/" + TAP + "/contents/Casks/traverse.rb", data=body, method="PUT",
                      headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json",
                               "User-Agent": "Respawn-Studios-Traverse-Tap"})
    with build_opener(Redirects()).open(request, timeout=45) as response:
        data = response.read(JSON_LIMIT + 1)
    require(0 < len(data) <= JSON_LIMIT, "GitHub response exceeds its bound")
    result = json.loads(data)
    expected = hashlib.sha1(b"blob " + str(target.stat().st_size).encode() + b"\0" + target.read_bytes()).hexdigest()
    require(re.fullmatch(r"[a-f0-9]{40}", result.get("commit", {}).get("sha", ""))
            and result.get("content", {}).get("path") == "Casks/traverse.rb"
            and result["content"].get("sha") == expected, "GitHub did not confirm the cask commit")
    remote = Client().json("https://api.github.com/repos/" + TAP + "/contents/Casks/traverse.rb?ref=main")
    require(remote.get("sha") == expected and remote.get("encoding") == "base64"
            and base64.b64decode(remote.get("content", "")) == target.read_bytes(),
            "Published cask readback differs")
    print("Published verified cask update")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="Commit the verified cask in the tap's main workflow")
    args = parser.parse_args()
    target = ROOT / "Casks/traverse.rb"
    previous_blob = subprocess.check_output(["git", "rev-parse", "HEAD:Casks/traverse.rb"], cwd=ROOT, text=True).strip()
    client = Client()
    if update(client.json(API + "/releases/latest"), client, target):
        if args.publish:
            publish(target, previous_blob)
        else:
            print("Verified cask update prepared locally")
    else:
        print("Traverse cask already matches the latest full release")


if __name__ == "__main__":
    try:
        main()
    except (Refused, KeyError, TypeError, AttributeError, json.JSONDecodeError) as error:
        raise SystemExit("Cask update refused: " + (str(error) if isinstance(error, Refused) else "invalid release data"))
