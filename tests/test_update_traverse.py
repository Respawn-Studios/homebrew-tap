import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("updater", ROOT / "tools/update_traverse.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class FixtureClient(updater.Client):
    def __init__(self):
        self.responses = {}
        self.requests = []

    def open(self, url):
        self.requests.append(url)
        return io.BytesIO(self.responses[url])


class ReleaseUpdateTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".build").mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=ROOT / ".build")
        self.addCleanup(self.directory.cleanup)
        self.target = Path(self.directory.name) / "traverse.rb"
        self.original = updater.render("0.2.0", "95", {a: {"artifact": {"sha256": "e" * 64}}
                                                      for a in ("arm64", "x86_64")})
        self.target.write_bytes(self.original)
        self.client = FixtureClient()
        self.release = {"tag_name": "v0.3.0", "draft": False,
                        "prerelease": False, "immutable": True, "assets": []}
        self.catalogs = {}
        source = b"generated corresponding source"
        source_asset = self.asset("Traverse-0.3.0-99-source.tar.gz", source)
        for arch in ("arm64", "x86_64"):
            binary = ("generated " + arch).encode()
            name = f"Traverse-0.3.0-99-{arch}.dmg"
            asset = self.asset(name, binary)
            digest = hashlib.sha256(binary).hexdigest()
            self.client.responses[updater.image_url(arch, digest)] = binary
            admission = {"appCDHash": "a" * 40, "team": "CDLNJRG82U",
                         "gatekeeper": "accepted", "containerGatekeeper": "accepted",
                         "stapled": True, "containerStapled": True, "schema": 1,
                         "bundleID": "com.respawnstudios.traverse", "version": "0.3.0",
                         "build": "99", "channel": "Developer ID", "container": "dmg", "timestamped": True}
            catalog = {"schema": 1, "channel": "direct-public-free-v1", "publicKey": updater.PUBLIC_KEY,
                       "artifact": {"filename": name, "version": "0.3.0", "build": "99",
                                    "architecture": arch, "minimumOS": "15.0", "bytes": len(binary),
                                    "sha256": digest, "admission": admission},
                       "app": {"bundleID": "com.respawnstudios.traverse", "architecture": arch,
                               "accessPolicy": "local-user-v1", "releasePurpose": "direct-shipping-v1",
                               "appCDHash": "a" * 40},
                       "sourceKit": {"format": "traverse-source-kit-v1", "sha256": source_asset["digest"][7:],
                                     "bytes": len(source), "sourceCommit": "b" * 40},
                       "buildSourceSHA256": {"source.swift": "c" * 64}}
            self.catalogs[arch] = catalog
            self.asset(f"Traverse-0.3.0-99-{arch}-updates.json", json.dumps(catalog).encode())
        self.proof = {"schema": 1, "purpose": "traverse-homebrew-acceptance-v1", "version": "0.3.0", "build": "99",
                      "caskSHA256": hashlib.sha256(updater.render("0.3.0", "99", self.catalogs)).hexdigest(),
                      "installerSHA256": {a: c["artifact"]["sha256"] for a, c in self.catalogs.items()},
                      "bothArchitectureReadall": True, "arm64InstallAndColdStart": True}
        self.acceptance()

    def acceptance(self):
        self.release["body"] = ("Release notes.\n\n<!-- traverse-homebrew-acceptance-v1\n"
                                + json.dumps(self.proof, sort_keys=True, separators=(",", ":")) + "\n-->")

    def asset(self, name, data):
        url = f"https://github.com/{updater.REPOSITORY}/releases/download/v0.3.0/{name}"
        asset = {"name": name, "browser_download_url": url, "size": len(data),
                 "digest": "sha256:" + hashlib.sha256(data).hexdigest()}
        self.release["assets"].append(asset)
        self.client.responses[url] = data
        return asset

    def refresh(self, arch):
        name = f"Traverse-0.3.0-99-{arch}-updates.json"
        asset = next(a for a in self.release["assets"] if a["name"] == name)
        data = json.dumps(self.catalogs[arch]).encode()
        asset.update(size=len(data), digest="sha256:" + hashlib.sha256(data).hexdigest())
        self.client.responses[asset["browser_download_url"]] = data

    def refuse(self, message):
        with self.assertRaisesRegex(updater.Refused, message):
            updater.update(self.release, self.client, self.target)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_updates_both_architectures_and_second_run_is_inert(self):
        self.assertTrue(updater.update(self.release, self.client, self.target))
        contents = self.target.read_text()
        self.assertIn('version "0.3.0,99"', contents)
        self.assertIn("on_arm do", contents)
        self.assertIn("on_intel do", contents)
        self.assertNotIn("zap", contents)
        self.assertNotIn("system_command", contents)
        self.client.requests.clear()
        self.assertFalse(updater.update(self.release, self.client, self.target))
        self.assertFalse(any(url.endswith(".dmg") for url in self.client.requests))

    def test_corrupt_second_image_keeps_original(self):
        item = self.catalogs["x86_64"]["artifact"]
        self.client.responses[updater.image_url("x86_64", item["sha256"])] = b"bad"
        self.refuse("Installer bytes do not match")

    def test_catalog_digest_must_match_github(self):
        asset = next(a for a in self.release["assets"] if a["name"].endswith("arm64-updates.json"))
        self.client.responses[asset["browser_download_url"]] += b" "
        self.refuse("Catalog bytes differ")

    def test_sources_must_agree(self):
        self.catalogs["x86_64"]["buildSourceSHA256"]["source.swift"] = "d" * 64
        self.refresh("x86_64")
        self.refuse("source inventories differ")

    def test_corresponding_source_asset_required(self):
        self.release["assets"] = [a for a in self.release["assets"] if "source.tar.gz" not in a["name"]]
        self.refuse("Corresponding source is missing")

    def test_notarized_container_required(self):
        self.catalogs["arm64"]["artifact"]["admission"]["containerStapled"] = False
        self.refresh("arm64")
        self.refuse("admission is incomplete")

    def test_missing_cdhash_in_both_objects_is_refused(self):
        del self.catalogs["arm64"]["app"]["appCDHash"]
        del self.catalogs["arm64"]["artifact"]["admission"]["appCDHash"]
        self.refresh("arm64")
        self.refuse("admission is incomplete")

    def test_new_release_needs_matching_homebrew_acceptance(self):
        self.proof["caskSHA256"] = "0" * 64
        self.acceptance()
        self.refuse("acceptance does not cover")

    def test_absent_duplicate_malformed_and_quoted_records_refused(self):
        valid = self.release["body"]
        for body, message in (("", "exactly one"), (valid + "\n" + valid, "exactly one"),
                              (valid.replace("\n-->", "\nnot a comment"), "Malformed"),
                              ("```text\n" + valid, "Quoted"),
                              ("   ```text\n" + valid, "Quoted"),
                              ("   ```text\n   ```still-code\n" + valid, "Quoted"),
                              ("````text\n```\n" + valid, "Quoted"),
                              ("~~~text\n```\n" + valid, "Quoted")):
            with self.subTest(message=message):
                self.release["body"] = body
                self.refuse(message)

    def test_extra_fields_and_wrong_architecture_refused(self):
        self.proof["untested"] = True
        self.acceptance()
        self.refuse("Noncanonical")
        del self.proof["untested"]
        self.proof["installerSHA256"]["intel"] = self.proof["installerSHA256"].pop("x86_64")
        self.acceptance()
        self.refuse("acceptance does not cover")

    def test_owner_stanza_is_not_silently_overwritten(self):
        self.original = self.original.replace(b'  app "Traverse.app"', b'  auto_updates true\n  app "Traverse.app"')
        self.target.write_bytes(self.original)
        self.refuse("changes that need maintainer review")

    def test_both_catalogs_required(self):
        self.release["assets"] = [a for a in self.release["assets"] if not a["name"].endswith("x86_64-updates.json")]
        self.refuse("Exactly one catalog per architecture")

    def test_duplicate_asset_refused(self):
        self.release["assets"].append(copy.deepcopy(self.release["assets"][0]))
        self.refuse("Duplicate or invalid")

    def test_only_full_immutable_release_allowed(self):
        for field, value in (("draft", True), ("prerelease", True), ("immutable", False)):
            with self.subTest(field=field):
                saved = self.release[field]
                self.release[field] = value
                self.refuse("Only an immutable full release")
                self.release[field] = saved

    def test_version_is_validated_before_any_download(self):
        self.release["tag_name"] = 'v0.3.0"\nsystem_command'
        self.refuse("Unexpected release tag")
        self.assertEqual(self.client.requests, [])

    def test_reissued_build_refused(self):
        self.original = self.original.replace(b"0.2.0,95", b"0.3.0,99")
        self.target.write_bytes(self.original)
        self.refuse("older or reissued")

    def test_credentials_never_follow_cross_origin_redirect(self):
        request = Request("https://api.github.com/example", headers={"Authorization": "Bearer generated"})
        with self.assertRaisesRegex(updater.Refused, "credential forwarding"):
            updater.Redirects().redirect_request(request, None, 302, "", {}, "https://github.com/example")

    def test_untrusted_redirects_refused(self):
        request = Request("https://github.com/example")
        for target in ("http://github.com/example", "https://example.com", "https://user@github.com/file",
                       "https://github.com:8443/file"):
            with self.subTest(target=target), self.assertRaisesRegex(updater.Refused, "Unexpected download redirect"):
                updater.Redirects().redirect_request(request, None, 302, "", {}, target)


if __name__ == "__main__":
    unittest.main()
