#!/usr/bin/env python3
"""Validate the two fixed behavioral runs and write a case-level conclusion."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ETHER = 10**18


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    runs = []
    for run_id in ("r1", "r2"):
        path = HERE / f"behavioral_results_{run_id}.json"
        report = json.loads(path.read_text())
        if report["runId"] != run_id or set(report["cases"]) != {"V0", "V1", "V2", "V3"}:
            raise ValueError(f"Invalid run record: {path}")
        runs.append(report)
    if runs[0]["cases"] != runs[1]["cases"]:
        raise ValueError("Repeated run measurements disagree")
    cases = runs[0]["cases"]
    for name, case in cases.items():
        normal = case["ordinary"]
        nested = case["nested"]
        failed = case["rejectedCallback"]
        if normal != {"creditBefore": str(ETHER), "creditAfter": "0", "daoBalanceAfter": "0"}:
            raise ValueError(f"Ordinary workflow differs in {name}")
        if nested["callbacks"] != "1" or nested["donorCreditAfter"] != str(ETHER):
            raise ValueError(f"Nested scenario inputs differ in {name}")
        paid = int(nested["attackerReceived"])
        if name == "V0":
            if paid != 2 * ETHER:
                raise ValueError("Baseline exploit was not observed")
        elif paid != ETHER or nested["attackerCreditAfter"] != "0":
            raise ValueError(f"Reentrancy protection failed in {name}")
        if failed != {"recipientBalance": "0", "recipientCreditAfter": "0",
                      "daoBalanceAfter": str(ETHER)}:
            raise ValueError(f"Unchecked send limitation differs in {name}")
    conclusion = {
        "case": "dataset/reentrancy/simple_dao.sol",
        "runs": 2,
        "variants": 4,
        "scenarios_per_variant_per_run": 3,
        "both_runs_identical": True,
        "normal_workflow_passes_all_variants": True,
        "baseline_nested_callback_overpays": True,
        "V1_CEI_prevents_measured_overpayment": True,
        "V2_mutex_prevents_measured_overpayment": True,
        "V3_combination_prevents_measured_overpayment": True,
        "V3_better_than_V1_or_V2_on_measured_scenario": False,
        "unchecked_failed_send_persists_in_all_variants": True,
        "limitations": "One benchmark and one bounded callback pattern; deterministic local behavior only. No static-detector or production claim.",
        "evidence_sha256": {f"behavioral_results_{run_id}.json": sha256(HERE / f"behavioral_results_{run_id}.json")
                            for run_id in ("r1", "r2")},
    }
    (HERE / "summary.json").write_text(json.dumps(conclusion, indent=2) + "\n")
    print(json.dumps(conclusion, indent=2))


if __name__ == "__main__":
    main()
