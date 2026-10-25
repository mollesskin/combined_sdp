#!/usr/bin/env python3
"""Compile every unchanged benchmark with its recorded compiler, offline."""

import csv
import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 60
FIELDS = (
    "source_path",
    "source_sha256",
    "pinned_solc",
    "compiler_path",
    "compiler_sha256",
    "status",
    "exit_code",
    "elapsed_seconds",
    "stdout_path",
    "stdout_sha256",
    "stderr_path",
    "stderr_sha256",
    "error_type",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_one(item: dict[str, str]) -> dict[str, str]:
    source = ROOT / item["source_path"]
    if sha(source.read_bytes()) != item["source_sha256"]:
        raise ValueError(f"Source changed after inventory: {item['source_path']}")
    compiler_rel = item["local_compiler_path"]
    result = {
        "source_path": item["source_path"],
        "source_sha256": item["source_sha256"],
        "pinned_solc": item["pinned_solc"],
        "compiler_path": compiler_rel,
        "compiler_sha256": "",
        "status": "missing_compiler" if not compiler_rel else "",
        "exit_code": "",
        "elapsed_seconds": "",
        "stdout_path": "",
        "stdout_sha256": "",
        "stderr_path": "",
        "stderr_sha256": "",
        "error_type": "",
    }
    if not compiler_rel:
        return result
    compiler = ROOT / compiler_rel
    result["compiler_sha256"] = sha(compiler.read_bytes())
    command = [str(compiler), "--combined-json", "abi,bin", item["source_path"]]
    started = time.monotonic()
    stdout = b""
    stderr = b""
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=TIMEOUT_SECONDS)
        stdout, stderr = completed.stdout, completed.stderr
        result["exit_code"] = str(completed.returncode)
        result["status"] = "compiled" if completed.returncode == 0 else "compiler_error"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        result["status"] = "timeout"
        result["error_type"] = "TimeoutExpired"
    except OSError as exc:
        stderr = str(exc).encode()
        result["status"] = "launch_error"
        result["error_type"] = type(exc).__name__
    result["elapsed_seconds"] = f"{time.monotonic() - started:.3f}"
    raw_dir = OUT / "compile_raw" / source.parent.name / source.stem
    raw_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = raw_dir / "stdout.txt"
    stderr_path = raw_dir / "stderr.txt"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    (raw_dir / "command.json").write_text(
        json.dumps({"argv": command, "cwd": str(ROOT), "timeout_seconds": TIMEOUT_SECONDS}, indent=2) + "\n"
    )
    result["stdout_path"] = stdout_path.relative_to(OUT).as_posix()
    result["stdout_sha256"] = sha(stdout)
    result["stderr_path"] = stderr_path.relative_to(OUT).as_posix()
    result["stderr_sha256"] = sha(stderr)
    return result


def main() -> None:
    with (OUT / "inventory.csv").open(newline="") as stream:
        inventory = list(csv.DictReader(stream))
    if len(inventory) != 143:
        raise ValueError("Inventory must have exactly 143 original files")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(compile_one, inventory))
    with (OUT / "baseline_compilation.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    statuses = {status: sum(row["status"] == status for row in results) for status in sorted({row["status"] for row in results})}
    summary = {
        "original_sources": len(results),
        "status_counts": statuses,
        "missing_compiler_sources": [row["source_path"] for row in results if row["status"] == "missing_compiler"],
        "failed_or_timed_out_sources": [row["source_path"] for row in results if row["status"] in {"compiler_error", "timeout", "launch_error"}],
        "treatment_variants_compiled": 0,
        "security_outcomes_measured": 0,
    }
    (OUT / "baseline_compilation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
