#!/usr/bin/env python3
"""Install only the missing 0.4.21 native compiler from official solc-bin."""

import hashlib
import json
import ssl
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
VERSION = "0.4.21"
BASE_URL = "https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/macosx-amd64/"
DEST = OUT / "toolchain" / f"solc-{VERSION}"
CA_FILE = ROOT / "experiments/reentrancy/toolchain/venv/lib/python3.13/site-packages/certifi/cacert.pem"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if DEST.exists():
        raise FileExistsError(f"Refusing to overwrite {DEST}")
    context = ssl.create_default_context(cafile=str(CA_FILE) if CA_FILE.is_file() else None)
    with urllib.request.urlopen(BASE_URL + "list.json", context=context, timeout=30) as response:
        listing = json.load(response)
    filename = listing["releases"][VERSION]
    expected = next(item["sha256"].removeprefix("0x") for item in listing["builds"] if item["path"] == filename)
    with urllib.request.urlopen(BASE_URL + filename, context=context, timeout=60) as response:
        binary = response.read()
    actual = sha(binary)
    if actual != expected:
        raise ValueError("Official solc-bin SHA-256 mismatch")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(binary)
    DEST.chmod(0o755)
    (OUT / "toolchain" / "solc-0.4.21.provenance.json").write_text(
        json.dumps({"version": VERSION, "source": BASE_URL + filename, "sha256": actual}, indent=2) + "\n"
    )
    print(json.dumps({"path": str(DEST), "sha256": actual}))


if __name__ == "__main__":
    main()
