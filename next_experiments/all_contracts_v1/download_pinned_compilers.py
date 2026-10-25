#!/usr/bin/env python3
"""Download dataset-pinned macOS solc binaries from the official archive."""

import csv
import hashlib
import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "toolchain"
BASE_URL = "https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/macosx-amd64/"


def download(url, context):
    with urllib.request.urlopen(url, context=context, timeout=90) as response:
        return response.read()


def main():
    with (ROOT / "versions.csv").open(newline="") as stream:
        versions = sorted({row["compiled version"] for row in csv.DictReader(stream)})
    context = ssl.create_default_context()
    listing = json.loads(download(BASE_URL + "list.json", context))
    builds = {item["path"]: item for item in listing["builds"]}
    OUT.mkdir(parents=True, exist_ok=True)
    for version in versions:
        filename = listing["releases"][version]
        expected = builds[filename]["sha256"].removeprefix("0x")
        destination = OUT / f"solc-{version}"
        if destination.is_file():
            data = destination.read_bytes()
        else:
            data = download(BASE_URL + filename, context)
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch for solc {version}")
        if not destination.is_file():
            destination.write_bytes(data)
            destination.chmod(0o755)
        provenance = {"version": version, "source": BASE_URL + filename, "sha256": actual}
        (OUT / f"solc-{version}.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        print(f"solc {version}: verified")


if __name__ == "__main__":
    main()
