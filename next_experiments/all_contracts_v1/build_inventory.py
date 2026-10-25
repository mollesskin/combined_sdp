#!/usr/bin/env python3
"""Inventory all benchmark originals without changing historical experiments."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXPECTED_NEW_SOURCE_SHA256 = "40ffea56c722280688eba923676992d20be7623dcf724393c1c7ca1ef24e0ae5"
COMPILER_DIRS = (
    OUT / "toolchain",
    ROOT / "experiments/reentrancy/toolchain",
    ROOT / "experiments/multi_vulnerability/design_v1/toolchain",
)
FIELDS = (
    "source_path",
    "family",
    "source_sha256",
    "annotated_lines",
    "pinned_solc",
    "local_compiler_path",
    "previous_evaluation_type",
    "previous_A",
    "previous_B",
    "new_evaluation_type",
    "next_step",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    versions = {row["file"]: row for row in read_csv(ROOT / "versions.csv")}
    annotations = {row["path"]: row for row in json.loads((ROOT / "vulnerabilities.json").read_text())}
    earlier = {
        row["benchmark_identity"]: row
        for row in read_csv(OUT / "prior_case_registry_public.csv")
    }
    new_summary_path = OUT / "simple_dao_v1/summary.json"
    new_summary = json.loads(new_summary_path.read_text()) if new_summary_path.is_file() else None
    new_full_path = new_summary["case"] if new_summary else None
    files = sorted((ROOT / "dataset").rglob("*.sol"))
    paths = {p.relative_to(ROOT).as_posix() for p in files}
    if not (len(files) == len(paths) == len(versions) == len(annotations) == 143):
        raise ValueError("Expected exactly 143 uniquely indexed source files")
    if paths != set(versions) or paths != set(annotations):
        raise ValueError("Dataset, version table, and annotations disagree")

    rows: list[dict[str, str]] = []
    for source in files:
        relative = source.relative_to(ROOT).as_posix()
        entry = annotations[relative]
        family = source.parent.name
        labels = {item["category"] for item in entry["vulnerabilities"]}
        if labels != {family}:
            raise ValueError(f"Annotation/category mismatch: {relative}")
        pinned = versions[relative]["compiled version"]
        compiler = next(
            (path / f"solc-{pinned}" for path in COMPILER_DIRS if (path / f"solc-{pinned}").is_file()),
            None,
        )
        old = earlier.get(relative)
        if old and old["exact_source_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError(f"Historical registry source hash mismatch: {relative}")
        old_type = old["evaluation_type"] if old else "not_selected_previously"
        full = old_type in {"full V0-V1-V2-V3 comparison", "exploratory full comparison"}
        new_full = relative == new_full_path
        if new_full and (full or hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_NEW_SOURCE_SHA256):
            raise ValueError("New comparison overlaps an old one or source hash changed")
        rows.append(
            {
                "source_path": relative,
                "family": family,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "annotated_lines": json.dumps(
                    sorted({line for item in entry["vulnerabilities"] for line in item["lines"]})
                ),
                "pinned_solc": pinned,
                "local_compiler_path": compiler.relative_to(ROOT).as_posix() if compiler else "",
                "previous_evaluation_type": old_type,
                "previous_A": old["mechanism_A"] if old and old["mechanism_A"] != "N/A" else "",
                "previous_B": old["mechanism_B"] if old and old["mechanism_B"] != "N/A" else "",
                "new_evaluation_type": "full V0-V1-V2-V3 behavioral comparison" if new_full else "",
                "next_step": "complete_new_comparison" if new_full else
                             ("audit_prior_pair_independence" if full else "qualify_two_distinct_treatments"),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "total_original_solidity_files": len(rows),
        "families": dict(sorted(Counter(row["family"] for row in rows).items())),
        "previous_evaluation_types": dict(
            sorted(Counter(row["previous_evaluation_type"] for row in rows).items())
        ),
        "existing_full_comparisons": sum(row["next_step"] == "audit_prior_pair_independence" for row in rows),
        "new_full_comparisons": sum(row["next_step"] == "complete_new_comparison" for row in rows),
        "total_full_comparisons_historical_plus_new": sum(row["next_step"] in
            {"audit_prior_pair_independence", "complete_new_comparison"} for row in rows),
        "need_pair_qualification": sum(row["next_step"] == "qualify_two_distinct_treatments" for row in rows),
        "missing_local_compiler_versions": sorted(
            {row["pinned_solc"] for row in rows if not row["local_compiler_path"]}
        ),
        "new_treatment_sources_generated": 3 if new_summary else 0,
        "new_security_outcomes_measured": 1 if new_summary else 0,
    }
    (OUT / "inventory_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
