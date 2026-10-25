#!/usr/bin/env python3
"""Record conservative pair qualification without inventing treatment arms."""

import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = ("source_path", "family", "source_sha256", "baseline_compiled",
          "prior_evaluation_type", "strict_pair_status", "reason", "next_action")

NA_BY_FILE = {
    "dataset/arithmetic/integer_overflow_benign_1.sol":
        "Annotated subtraction assigns an unused local result; no observable protected-state outcome or independent second pattern is defined.",
    "dataset/access_control/arbitrary_location_write_simple.sol":
        "Historical pre-decrement and post-result guards both exclude the same empty-array underflow; the second guard adds no distinct failure condition under this strict pair rule.",
    "dataset/access_control/incorrect_constructor_name1.sol":
        "The exposed misnamed initializer has one validated root fix: make it a constructor. A second independent, behavior-preserving target defense is not established.",
    "dataset/access_control/incorrect_constructor_name2.sol":
        "The exposed misnamed initializer has one validated root fix: make it a constructor. A second independent, behavior-preserving target defense is not established.",
    "dataset/access_control/incorrect_constructor_name3.sol":
        "The exposed misnamed initializer has one validated root fix: make it a constructor. A second independent, behavior-preserving target defense is not established.",
    "dataset/access_control/wallet_03_wrong_constructor.sol":
        "The exposed initializer has one validated root fix: make it a constructor. A second independent, behavior-preserving target defense is not established.",
    "dataset/access_control/mycontract.sol":
        "The validated authorization repair replaces tx.origin with msg.sender; no distinct, comparable second authorization policy is established.",
    "dataset/access_control/phishable.sol":
        "The validated authorization repair replaces tx.origin with msg.sender; no distinct, comparable second authorization policy is established.",
    "dataset/access_control/multiowned_vulnerable.sol":
        "The validated repair adds the existing owner guard to the exposed function; no distinct second policy is established.",
    "dataset/access_control/simple_suicide.sol":
        "The validated repair introduces deployment authority and a guard; a second independent, baseline-compatible target policy is not established.",
    "dataset/access_control/unprotected0.sol":
        "The validated repair uses the existing owner guard; no distinct second policy is established.",
    "dataset/denial_of_service/auction.sol":
        "Historical PULL and FALLBACK arms are alternative refund workflows sharing deferred credit, so a simultaneous A+B arm is not an independent pair.",
    "dataset/denial_of_service/dos_simple.sol":
        "Incremental cleanup was validated as a single fix; an added capacity limit duplicates the existing bounded input and is not a justified independent second pattern.",
    "dataset/denial_of_service/send_loop.sol":
        "The source has no public path to populate payable refunds for its fixed recipients; a comparable recipient-failure versus large-loop behavioral fixture is not established.",
    "dataset/short_addresses/short_address_example.sol":
        "Minimum calldata-length guard and strict ABI decoding reject the same malformed-input condition; a distinct second target pattern is not established.",
}

FAMILY_NA = {
    "arithmetic": "Checked arithmetic and exact operand preconditions enforce the same no-wrap domain. A distinct, behavior-preserving second target defense is not established in the current design.",
    "other": "Annotated uninitialized-storage-pointer repair has no second independently justified target defense under the current design.",
}


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    inventory = read_csv(HERE / "inventory.csv")
    compile_status = {row["source_path"]: row for row in read_csv(HERE / "baseline_compilation.csv")}
    if len(inventory) != 143 or len(compile_status) != 143:
        raise ValueError("Expected one inventory and compilation row per source")
    rows = []
    for item in inventory:
        path = item["source_path"]
        if path not in compile_status:
            raise ValueError(f"Missing compilation: {path}")
        compile_row = compile_status[path]
        if compile_row["status"] != "compiled":
            raise ValueError(f"Baseline not compiled: {path}")
        if item["new_evaluation_type"]:
            status, reason, action = (
                "completed_new_pair",
                "CEI and withdrawal mutex were compiled and measured separately and together in two local runs.",
                "retain_case_evidence",
            )
        elif path in NA_BY_FILE or item["family"] in FAMILY_NA:
            status = "N/A_current_strict_pair_design"
            reason = NA_BY_FILE.get(path, FAMILY_NA.get(item["family"], ""))
            action = "retain_prior_evidence_if_any; reconsider_only_with_new_independent_policy"
        elif item["next_step"] == "audit_prior_pair_independence":
            status, reason, action = (
                "historical_full_pair_audit_pending",
                "Full comparison exists, but pair independence and workflow fit have not been reaccepted under the new strict criterion.",
                "audit_prior_pair_and_regressions",
            )
        else:
            status, reason, action = (
                "source_specific_review_pending",
                "No two source-specific, independent, workflow-compatible treatments and frozen behavioral oracle are qualified yet.",
                "inspect_annotated_operation_and_design_oracle",
            )
        rows.append({
            "source_path": path,
            "family": item["family"],
            "source_sha256": item["source_sha256"],
            "baseline_compiled": "true",
            "prior_evaluation_type": item["previous_evaluation_type"],
            "strict_pair_status": status,
            "reason": reason,
            "next_action": action,
        })
    with (HERE / "pair_qualification.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "total_sources": len(rows),
        "baseline_compiled": sum(row["baseline_compiled"] == "true" for row in rows),
        "strict_pair_statuses": dict(sorted(Counter(row["strict_pair_status"] for row in rows).items())),
        "note": "N/A means no justified second pattern in the current design, not that no future defense can exist. Pending is not counted as N/A or a completed comparison.",
    }
    (HERE / "pair_qualification_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
