# RE01–RE03: exploratory, AI-assisted developmental behavioral pilot

Approved RQ unchanged: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?” This is a bounded local pilot on the three existing reentrancy sources, not assignment prose or a comprehensive answer. Earlier static and controlled local observations were already known. Protocol and implementation locks precede these new runs, not all project data. No PES change/calculation or combination of static warnings with behavioral metrics.

UC01–UC03 are closed as exploratory behavioral pilots by immutable reference (prior_branch_closure.md). Their results/limitations remain unchanged. No search/extension for a combination advantage. Twelve pre-existing reentrancy variants are reused without source edits: V0 original, V1 CEI, V2 Mutex, V3 CEI+Mutex. Existing implementations were inspected and no correction was required for this scoped study. No silent arm replacement or weakened individual mechanism.

## Tests and conditions

The test inventory explicitly separates interface ABI checks, ordinary functional checks, and security properties. The three prior scenarios are reused: ordinary sequential withdrawals (O1), rejecting receiver followed by recovery (F1), one bounded reentry attempt (S1). The old receiver contract body is reused byte-identically; source extraction/fixture provenance is recorded. Its generic withdraw sends amount calldata even to zero-argument RE02/RE03 selectors, as in the previous suite; these legacy dispatchers accept trailing data. Actual calldata and computation trees are saved.

The earlier checker’s variant-specific expectations characterized vulnerable behavior. The new protocol uses the same correct-state requirements for every arm and records baseline violations rather than treating expected exploitation as a security pass. No new adversarial scenario was added to make V3 win. Normal operations, accounting, rollback, coverage and allowed payout are fixed before new comparisons in protocol.md and scenario_inputs.json.

RE01 EtherStore uses existing solc0.4.10, RE02 ReentrancyDAO0.4.19, RE03 Reentrance0.4.15. Fixture uses original compiler0.4.24 in every condition. Per-contract compiler pins remain identical across V0–V3 and repeats. --combined-json abi,bin, no optimizer, 60s compile timeout. Native old solc is used directly; Mythril’s old-version wrapper exclusion is unrelated because no analyzer is invoked. Version strings/hashes/paths and stdout/stderr are in each run.

In-process EthereumTesterProvider/PyEVMBackend ByzantiumVM, genesis timestamp2000000000,difficulty1,gas limit30000000; transaction gas12000000,gasPrice1. Fresh deterministic backend per contract/variant/scenario/repetition. No RPC/public chain/testnet/live contracts/forks or real funds. Source manifests, benchmark paths/category/line annotations, actors, funding and amounts are fixed in inputs. Same initial financial/credit state across four arms, with explicit storage-slot shifts for existing private mutex fields.

Closed credits/aggregate are read from local storage using frozen source-order slots and mapping-key formula, not new public getters. Deposits validate both tracked credit positions; RE01/RE03 existing public getters independently cross-check them. Raw words/slots and normalized fields are saved. No state patching or instrumented benchmark source. Full ABI equality is separately verified and never presented as full behavioral equivalence.

## Outputs and interpretation

See generated_results.md, comparison/comparison.csv and per-run summary.json. Counts: 3 source contracts, 12 existing variant sources, 2 clean-process launches/two repetitions per source, 72 scenario trials and 120 withdrawal steps. Repeats are reproducibility checks, not additional source contracts.

Each withdrawal records pre/post bank/receiver ETH, both actor credits, applicable aggregate/timestamp/guard, actual nested calls/outputs/value, outer status/gas, property applicability and violations. Consequences are separate: excess payout E, accounting mismatch M, claim/asset shortfall D in wei, with E normalized by fixed positive1ether; aggregate difference N/A where absent. They are not added into a scale or mixed with static findings. An actual reverted trial is not an infrastructure failure. A complete unsafe baseline execution has failed security properties, not a manufactured successful protection result.

RE01 baseline can wrap its uint256 credit. Raw enormous values and resulting claim-accounting discrepancies are retained; they must not be interpreted as economic valuation. RE02 aggregate may differ from remaining claims even when it tracks current ETH. A harmless successful nested zero-credit call under CEI is not called inferior to Mutex’s rejection when payout/accounting properties tie. Fixed transaction budget is identical; consumed gas can differ and is descriptive, not a protection outcome.

## Files

```
prior_branch_closure.md
 test_inventory.md                   # existing ABI/function/security tests; source/slot review
protocol.md, scenario_inputs.json, protocol.lock.json
fixture_provenance.json, fixtures/LocalRecipient.sol
execution.lock.json
 tests/run_reentrancy.py              # no static analyzer or network provider
 tests/summarize.py                   # derive CSV/properties/comparisons from observations
 tests/validate_evidence.py           # trace, old-file, ABI, storage and recomputation checks
 tests/report.py                     # generate human-readable report
runs/<timestamp>/{behavioral_results.csv,invariant_results.csv,summary.json}
runs/<timestamp>/raw/{inputs,versions,command,abi_comparison,execution_summary}.json
runs/<timestamp>/raw/compile/         # raw compiler stdout/stderr/execution events
runs/<timestamp>/raw/trials/<ID>/<V>/<scenario>/
                                     # full receipts/computations, setup, steps, errors
comparison/{comparison.csv,comparison.json,reproducibility.json}
generated_results.md, validation.json, run_log.json
preservation_snapshot.json, artifact.lock.json
```

## Exact reproduction commands

From the same project root, reusing the unchanged local Python environment and existing native compilers:

```sh
cd /Users/moldir_2024icloud.com/smartbugs-curated
re_python="$PWD/experiments/multi_vulnerability/compatibility_v2/toolchain/venv/bin/python"
re_run1="experiments/reentrancy_behavioral_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r1"
PYTHONDONTWRITEBYTECODE=1 "$re_python" experiments/reentrancy_behavioral_v1/tests/run_reentrancy.py --output "$re_run1" --repetition 1
re_run2="experiments/reentrancy_behavioral_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r2"
PYTHONDONTWRITEBYTECODE=1 "$re_python" experiments/reentrancy_behavioral_v1/tests/run_reentrancy.py --output "$re_run2" --repetition 2
re_comparison="experiments/reentrancy_behavioral_v1/comparison/$(date -u +%Y%m%dT%H%M%SZ)_reproduction"
PYTHONDONTWRITEBYTECODE=1 "$re_python" experiments/reentrancy_behavioral_v1/tests/summarize.py "$re_run1" "$re_run2" --comparison-output "$re_comparison"
PYTHONDONTWRITEBYTECODE=1 "$re_python" experiments/reentrancy_behavioral_v1/tests/validate_evidence.py "$re_run1" "$re_run2" --output "$re_comparison/validation.json"
```

Use fresh paths: the runner rejects existing directories; original raw evidence is not overwritten. The last validator also checks comparison equivalence against the delivered original comparison; any mismatch is retained/reported rather than silently replacing it. Do not run report.py over the frozen delivered report during reproduction. New summary outputs belong to new paths.

Actual originals: runs/20261022T134046Z_r1 and runs/20261022T134111Z_r2. Complete versions and pip-freeze lists are saved per run. Existing environment is reused read-only with bytecode-cache writes disabled; no install/upgrade. Reproducing on another OS/compiler/runtime requires separately documented qualification, not silent compiler replacement. Validation checks prior hashes, byte-identical derived CSV/summary recomputation, comparison recomputation, actual trace/state consistency and matched setups.

Scope limits: three known benchmark contracts, one bounded callback case, fixed receiver/amount/gas, direct closed-storage schema, ordinary and rejection/recovery sequences only. No general equivalence proof, exhaustive reentrancy coverage, cross-function/state-space search or real-world prevention probability. No extra contract/scenario/family is authorized; work stops here.
