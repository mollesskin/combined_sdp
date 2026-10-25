# Behavioral transferability v1 — UC02 / UC03 only

Exploratory, AI-assisted developmental work. Approved RQ unchanged: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?” Prior UC01 and channel/static outcomes were already known; neither freeze is a claim of preregistration before all data.

Source review qualified both registered candidates, with no replacements. UC02 is AirDropContract with caller-funded transferFrom, solc 0.4.18. UC03 is airDrop with explicit from and decimal scaling, solc 0.4.24. Benchmark revision: 230e649123477eff332742a59a1c7cc6dc286cab. Original sources, V0 copies, preregistered registries, reentrancy and every old package are unchanged. No unrelated owner/authority/arithmetic/validation repair. A/B are defensive checks/components, not independently sourced named design patterns.

A requires the low-level EVM success flag; B requires exactly 32 returned bytes encoding the full word 1, without checking that flag; A+B does both. No high-level call confounding B. As in UC01, B is not a complete production-safe wrapper: revert payload authenticity or dishonest token behavior is not guaranteed by a boolean decoder. No unusual payload case was introduced. Each variant uses the same compiler as its V0 and the fixture, no optimizer, same VM/genesis/gas budgets.

## Results and comparability

See generated_results.md, comparison/comparison.csv and each run’s CSV/raw evidence. These files are generated from recorded outputs, not manually entered performance values. Two original contracts, eight variant sources including two V0 copies, two full clean-process launches (two repetitions per contract), 48 primary trials plus 48 normal probes. Repetitions are reproducibility checks, not independent contracts. No new UC01 execution or pooled UC01 dataset.

**Pre-execution adapters:** source_applicability.md and protocol.md were saved/locked before coding. These sources lack Holders/internal token accounting, so I2/E are N/A/blank, not 0. TransferFrom allowance is observed explicitly, with expected debit on successful transfer and preservation on failure. UC02 operation amount=5; UC03 v=5,decimals=2 gives amount=500. The same D=max(0,a-delivery) on outer success, otherwise0, and exact D/a normalization apply; D is an unfulfilled acknowledged delivery, not a claim of economic loss. Different raw units, compiler pins and applicable invariant counts must not be pooled as if fully comparable to UC01. No new scale or PES.

Same S1–S3: successful true transfer, false without transfer, empty revert without transfer. Atomic failure policy for both negative cases remains the same across all conditions. Single-recipient batches preserve the one-token-call protocol; multi-recipient partial failures, batching capacity, arbitrary from authorization, overflow, fees/rebasing, malformed returns and unusual revert payloads are out of scope. No scenario or metric was added to obtain a V3 advantage. Ordinary functionality checks are separate and mandatory for superiority claims.

## Evidence layout

- source_applicability.md: both source reviews, suitability and adaptations before implementation.
- protocol.md / scenario_inputs.json / protocol.lock.json: developmental protocol freeze.
- source_changes.md / source_manifest.json / variants/{UC02,UC03}/{V0,V1,V2,V3}/Contract.sol / *.patch: exact minimal treatment diffs and original hashes.
- fixtures/TransferFromToken.sol: explicitly synthetic, compiled per candidate pin.
- tests/run_transfer.py and tests/summarize.py / execution.lock.json: implementation frozen before comparisons.
- runs/<UTC-run-id>/raw/: commands/versions/dependencies, full compiler stdout/stderr, receipts/computation trees, setup, normal probes, snapshots, state, errors. First ID omits ISO `T` separator but raw timestamps are complete and preserved.
- runs/<UTC-run-id>/behavioral_results.csv, invariant_results.csv, summary.json: derived outputs with N/A/error distinctions.
- comparison/: per-contract V3-vs-V1 and V3-vs-V2 results and clean-run comparison.
- generated_results.md: automatically built report.
- validation.json: old-file preservation, byte-identical metric recomputation, trace and initial-state checks.
- run_log.json, preservation_snapshot.json, artifact.lock.json: commands, timestamps, provenance and file hashes.

Each trial has a new in-process EthereumTesterProvider/PyEVMBackend ByzantiumVM. A normal mode-0 probe is saved then snapshot-reverted; matched initial state is checked before the primary scenario. No provider URL, RPC, public chain/testnet, mainnet fork, real wallet or real funds. Actual CALL child computations expose status/output, even if the parent rolls back; committed state comes from actual receipts and post-state. ABIs match within each contract; no claim of full equivalence follows from ABI matching.

## Exact reproduction

Use fresh output paths; existing raw runs are never overwritten. From this project root:

```sh
cd /Users/moldir_2024icloud.com/smartbugs-curated
transfer_python="$PWD/experiments/multi_vulnerability/compatibility_v2/toolchain/venv/bin/python"
transfer_run1="experiments/behavioral_transferability_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r1"
PYTHONDONTWRITEBYTECODE=1 "$transfer_python" experiments/behavioral_transferability_v1/tests/run_transfer.py --output "$transfer_run1" --repetition 1
transfer_run2="experiments/behavioral_transferability_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r2"
PYTHONDONTWRITEBYTECODE=1 "$transfer_python" experiments/behavioral_transferability_v1/tests/run_transfer.py --output "$transfer_run2" --repetition 2
transfer_comparison="experiments/behavioral_transferability_v1/comparison/$(date -u +%Y%m%dT%H%M%SZ)_reproduction"
PYTHONDONTWRITEBYTECODE=1 "$transfer_python" experiments/behavioral_transferability_v1/tests/summarize.py "$transfer_run1" "$transfer_run2" --comparison-output "$transfer_comparison"
```

The runner verifies developmental locks and V0 byte identity before execution. Source compilation commands/cwd/60s timeout/compiler hashes and version stdout are in raw/compile and raw/versions.json. Native compilers are reused read-only from experiments/multi_vulnerability/design_v1/toolchain/solc-0.4.18 and solc-0.4.24. Existing isolated Python environment/dependencies are reused with bytecode-cache writes disabled; no installs/upgrades. Python/package/platform evidence and complete pip-freeze lists are saved per launch. Other OS/compiler/runtime combinations require separate portability qualification; this claim is behavior transferability to UC02/UC03 in the pinned local environment, not platform independence.

No Slither/Mythril, static PES calculation, new scenario/family/contract, or changes to the approved RQ. Work stops after these two candidates.
