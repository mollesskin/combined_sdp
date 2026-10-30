# DoS comparison v1 — executed evidence

AI-assisted local research implementation, not an assignment submission. The approved research question is unchanged:

“How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?”

All **4/4 original files** were evaluated. Completed groups: **2 full V0–V3 comparisons** (`dos_address`, `dos_number`), **1 single-fix comparison** (`dos_simple`) and **1 alternative-workflow comparison** (`auction`: V0/PULL/FALLBACK). There are no blocked/unresolved cases in this declared scope. Thirteen source variants were compiled; fixtures are not additional source cases. The existing review specifies no clone group for these four files; four singleton groups do not establish independence.

Arithmetic and access control were neither executed nor edited. Read-only hashes confirmed preservation of all **1760 arithmetic files and1626 access-control files**, including their code, protocols and results. Earlier pilots, vendor, baseline runs and PES were not changed. Work stops after DoS.

## Checkpoint, design and corrections

At recovery, source variants, test code and protocol had been prepared and compiled, but no DoS runs existed. Their hashes matched the saved checkpoint. The project was reused. All subsequent executions have distinct timestamped output directories.

The saved design and parameters were retained: original batches of350, workloads1750/5950, capacity1750, incremental cleanup350, transaction limit12m gas,20 cleanup steps/240m cleanup budget, and full workflow budget300m or444m depending on the load. Capacity1750 is the smallest complete350-record batch capacity that can cross the required >1500 transition. It is an explicit capacity trade-off, not an original business requirement or universal remedy.

Instrument v1's first execution is preserved as development evidence: four out-of-gas transactions returned hashes in `error.data.transactionHash`; v1 looked only at the top level and classified them as infrastructure errors without receipts. Versioned instrument v2 retrieves that nested hash and checks the actual mined receipt. It also preserves unknown oversize completion as null. All four were confirmed as reverted with12m gas and observed rollback. No Solidity variant, workload or budget was adjusted after seeing outcomes. See `CHECKPOINT_AND_CHANGES.md`, `instrument_versions/`, `protocol_versions/` and the frozen original checkpoint.

## Array workloads and complete operations

Here “completed” means records physically removed by the explicitly requested cleanup, after admission and record-integrity verification. It does not mean merely one successful chunk. Before cleanup, every accepted record was checked. After cleanup/failure, every previously allocated record slot was checked against the required retained-prefix/zero-tail state. Rejection is retained in the requested denominator.

| File/load | Condition | Accepted/requested | Completed/requested | Cleanup tx | Whole requested task |
|---|---|---|---|---:|---|
| address,1750 | V0 / A / B / A+B | 1750/1750 | 1750/1750 | 1 /5 /1 /5 | Complete in all |
| number,1750 | V0 / A / B / A+B | 1750/1750 | 1750/1750 | 1 /5 /1 /5 | Complete in all |
| address,5950 | V0 | 5950/5950 | 0/5950 | 1 reverted | Not completed within budget |
| address,5950 | A | 5950/5950 | 5950/5950 | 17 | Complete |
| address,5950 | B / A+B | 1750/5950 | 1750/5950 | 1 /5 | Partial:4200 rejected |
| number,5950 | V0 | 5950/5950 | 0/5950 | 1 reverted | Not completed within budget |
| number,5950 | A | 5950/5950 | 5950/5950 | 17 | Complete |
| number,5950 | B / A+B | 1750/5950 | 1750/5950 | 1 /5 | Partial:4200 rejected |

Both original large atomic cleanups reverted with zero committed progress and retained all5950 records. This is a failure under the declared12m transaction budget, not evidence of permanent unavailability at every possible budget. The protocol stops after a mined no-progress revert rather than spending the remaining step budget on identical attempts.

A completed the full5950-record operation in34 measured workflow transactions (17 load +17 cleanup). B completed only the accepted portion in18 (17 requests including12 rejected +1 cleanup), and A+B in22 (same17 requests +5 cleanup). Their accepted-part completion is100%; their requested-work completion remains1750/5950, approximately29.4%. Rejected4200 records are not deleted from the denominator or counted as processed. All completed cleanups allowed a verified new350-record cycle. A/B admission guards do not change access rights to owner-only.

The separate `dos_number.clear()` logical-reset/reuse operation passed in all four conditions, retaining the allocated suffix and replacing the reused prefix with the new value. A single5000-number insertion failed in all variants under12m gas: V0/A ran out of gas, B/A+B rejected capacity. All accepted/committed volumes were0/5000. This does not count as availability success or demonstrate a bounded insertion loop.

### V3 against each component

For both factorial source files:

- **Against A:** full-request completion ties at1750; V3 is worse at5950 because it rejects4200 records that A accepts and processes. No additional protection/availability effect was observed.
- **Against B:** requested and accepted-part outcomes tie at both loads. V3 requires5 cleanup transactions instead of1 for the same1750 accepted records, without an observed completion benefit at the saved budget.

The machine-readable comparison also includes the two number-specific functionality/scope scenarios: V3−A has4 ties and2 worsenings; V3−B has6 ties. These are scenario observations, not independent vulnerabilities or a combined score.

### Gas costs

Whole array-workflow gas includes every prescribed admission request, including rejected requests, and cleanup calls. Post-completion refill is separate. Comparisons of different accepted workloads are not called gas-efficiency improvements.

| Source/load | V0 | A | B | A+B |
|---|---:|---:|---:|---:|
| address1750 | 46,460,957 | 46,554,816 | 46,461,627 | 46,555,446 |
| address5950 | 145,717,663 (unfinished) | 158,200,428 | 46,742,055 (partial) | 46,861,818 (partial) |
| number1750 | 47,841,775 | 47,982,839 | 47,843,160 | 47,984,199 |
| number5950 | 150,461,052 (unfinished) | 163,014,491 | 48,128,652 (partial) | 48,295,503 (partial) |

Exact source-specific gas, rejected workload and applicability are in `array_results.csv` and `combination_comparisons.csv`. Whole-operation results and individual receipt gas remain separate from financial amounts and violations; no PES or composite score is computed.

## dos_simple: preserved existing capacity

The original function already grows only to1750 before entering its clear branch. Adding another cap would duplicate baseline behavior. F1 only introduces bounded cleanup and a persistent phase flag.

At the fixed budget, both V0 and F1 completed the natural1750-record cycle and a new fill. V0 needed1 cleanup transaction; F1 needed5. Load+cleanup gas was **46,443,817 vs46,577,621**, an additional133,804 gas with no demonstrated completion improvement in this scenario. This is a valid tie/cost result, not evidence that baseline is permanently blocked.

With automine disabled and a30m block budget, each condition submitted4 fill transactions. One remained pending after the first mined block; all four executed successfully by the second block, preserving1400 records. The pending observation was transient noninclusion, not a reverted execution. Each deliberately over-block-budget probe was rejected before inclusion, with no receipt/gasUsed. Mining settings were restored in finally and the local network reset. `mining_status_summary.csv` counts unique transactions rather than duplicate observations across blocks.

## Auction: preserved debt and eventual payment

Ordinary bidder10 wei → higher bid20 wei completed in all three conditions. V0/FALLBACK paid10 immediately; PULL registered a10-wei claim and paid it on a later authorized claim. With a refusing former bidder:

- V0 rejected the new bid. The old live bid10 remained backed; it was not treated as an erased refund debt because no outbid occurred. Recovery metrics are N/A for that unmet prerequisite.
- PULL and FALLBACK accepted the20-wei bid and preserved the former bidder's10-wei claim.
- A claim directed to the refusing fixture reverted and retained the entire claim. The entitled fixture's controller then directed payment to an accepting EOA:10 wei paid, claim0. Repeating the claim paid0 extra. The final auction balance20 backed the current bid.

PULL and FALLBACK share deferred-credit/claim handling and are alternative workflows, not two independent components or a fictional A+B. There is no batching in auction.

`operations.json` totals include the prescribed invalid-bid, failed-claim and zero-repeat checks. `auction_results.csv` also reports transactions/gas up to the first completed refund state in the actual trace, plus bid/claim-phase and verification-phase costs:

| Scenario/condition | Measured calls incl checks | Gas incl checks | Calls to first completion in actual trace | Gas to first completion |
|---|---:|---:|---:|---:|
| ordinary V0/FALLBACK | 3 | 129,778 | 2 | 106,490 |
| ordinary PULL | 5 | 195,453 | 4 | 171,363 |
| refusing V0 | 3 | 148,178 | N/A | N/A |
| refusing PULL | 6 | 259,635 | 5 | 229,533 |
| refusing FALLBACK | 6 | 269,279 | 5 | 239,177 |

The trace includes an equal-bid rejection before recovery and, for refusing receivers, a failed claim attempt. These are observed trace costs, not hypothetical minimum transaction counts. PULL adds a claim step for accepting bidders; FALLBACK retains immediate payout when send succeeds.

## Repetition and validation

Primary runs are selected by `evaluation_paths.json`:

- `runs/evaluation_v2_1_20261023T053001Z`
- `runs/evaluation_v2_2_20261023T053111Z`

Each contains **338 measured transactions**,34 variant-scenario operation records over10 case-scenario definitions,8 additional submitted mining-diagnostic transactions and2 intentionally submission-rejected diagnostic probes. Each primary measured set has275 successful and63 reverted transactions; no infrastructure errors or unavailable receipts. These repetitions do not increase the four-file sample.

The second process clean-compiled the same sources and reset each scenario. All primary observations, operation outcomes and raw status histories matched, except output paths. **638 evidence checks passed**, including source hashes, exact record vectors, budget/denominator accounting, mined receipt status/gas, rollback, obligations, declared ABI changes and prior-stage preservation. See `repeat_comparison.json`; the validator preserves future differences instead of forcing a match.

All13 variants used actual solc **0.4.25**, identical optimizer settings (enabled,200 runs), the same Shanghai EVM/runtime parameters and30m block budget. Node20.20.0, npm10.8.2, Hardhat2.22.5, Python3.13.1. Dependency manifests match baseline; no packages were installed/updated. Config differences (explicit block budget and reporter) are saved. ABI additions are disclosed in `abi_deltas.json`; ABI equality is not a proof of full behavioral equivalence.

## Reproduce and inspect

From the repository root, for new executions with new timestamped directories:

```bash
bash experiments/multifamily_behavioral_v1/dos_comparison_v1/reproduce.sh
```

This script clean-compiles and executes **only DoS**, twice, then validates and exports tables. It reuses the existing installed baseline dependencies through `project/node_modules`; preserve that installation when moving the project. The script has been syntax-checked and uses the already executed commands; it was not run for unnecessary additional evaluations after the completed primary pair.

To verify saved evidence without executing contracts:

```bash
python3 experiments/multifamily_behavioral_v1/dos_comparison_v1/validate.py
python3 experiments/multifamily_behavioral_v1/dos_comparison_v1/export_tables.py
```

Artifact map:

- `PROTOCOL_RU.md`, `protocol_versions/`, `registry.json`: fixed rules, scopes, permission/workflow models, versioned corrections.
- `project/contracts/`, `diffs/`, `SHA256SUMS.json`: V0/protected source variants, exact diffs/hashes and local fixtures.
- `project/measure.js`, `instrument_versions/`, `validate.py`, `export_tables.py`, `reproduce.sh`: runnable measurement/oracle/validation code.
- Selected run directories: per-step raw JSON receipts/errors, exact inputs/before/after states, full record vectors, operations/measurements CSV and JSON, compiler settings, ABI and status histories.
- `array_results.csv`, `auction_results.csv`, `combination_comparisons.csv`, `mining_status_summary.csv`, `file_summary.csv`, `group_summary.csv`, `summary.json`: separate comparison groups and units.
- `repeat_comparison.json`, `validation_checks.json`, `preservation_check.json`: validation and reproducibility evidence.
- `CHECKPOINT_AND_CHANGES.md`, original development run, frozen checkpoint and logs: prepared-vs-executed history and instrument error, not hidden or relabelled as success.
- `versions.txt`, `dependencies.json`, `environment_validation.json`, `COMMANDS.md`, compile/execution logs: exact environment and commands.

BigInt quantities are exported as decimal strings. Small receipt metadata/indices may remain numeric. Null denotes N/A/unavailable measurements, not measured zero. Processed work is committed cleanup/insertion progress, not attempted writes later reverted. No claim is made about exhaustive inputs, formal equivalence, permanent unavailability at all budgets or production deployment safety. The evidence is limited to the declared local workloads and workflows.
