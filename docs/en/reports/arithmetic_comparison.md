# Completed arithmetic study

Thirteen registered original files were reviewed, and all 13 received full V0/V1/V2/V3 comparisons. The study created 52 variants with exact source diffs and SHA-256 hashes. All 52 compiled under Solidity 0.4.25 with optimization enabled at 200 runs and identical settings within each comparison. Their ABIs matched; that is not proof of full behavioral equivalence.

The two final runs produced 244 records each, 488 in total. Each variant had 61 measured calls: 43 permitted calls (including setup and early branches), 16 unsafe arithmetic calls, and two ordinary rejections under the original conditions. Deployment and reset are not counted as separate scenarios. Eighty-five evidence checks passed. States, inputs, receipts/errors, gas, and classifications matched between runs apart from raw output paths.

V0 executed all 16 unsafe calls; V1, V2, and V3 rejected all 16 with complete rollback of observed state. All four variants passed the 43 permitted calls, with no functional regressions observed in the executed scenarios. Both ordinary baseline rejections remained. In the insufficient-balance self-transfer case, V0 can restore the same final balance but still violates the requirement to avoid an intermediate underflow and reject safely. This is recorded separately from the observed modular final state.

Against V1, V3 had 61 oracle ties, zero improvements, and zero regressions. Against V2, it also had 61/0/0. No additional protective effect from the combination was observed in this set. The comparison involves overlapping arithmetic protections; it is not evidence that A and B are independent or that their combination is superior.

Gas is a secondary measure. For 43 comparable successful calls, V3 used the same gas in nine and more in 34: the V3−V1 difference ranged from 0 to 601 gas, and V3−V2 from 0 to 345 gas. For 18 rejected calls (16 unsafe plus two business rejections), V3−V1 ranged from −33 to +71 gas, while V3−V2 was zero. These are per-call ranges, not a universal effectiveness scale; deployment cost was not compared.

All 13 file-level full comparisons were completed. Under the reviewed `AR_ADDER_CLONE` grouping, they represent 12 groups. In each group, V0 accepted at least one unsafe input, while protected variants rejected unsafe inputs and preserved permitted calls. The two adder files are not counted as independent implementations. The other singleton groups also do not establish independence; clone review was limited to the original review.

No files were excluded and no four-variant comparisons remained unfinished. Exhaustive/fuzz verification, opcode tracing, formal equivalence, and measurements of local unused `res` values in `overflow_single_tx` were not performed; those three operations were unchanged and outside the treatment. The reachable permitted mapping debit is limited to zero because the original contract has no funding path. Results are not generalized to untested inputs or other categories.

## Artifacts

- `PROTOCOL_RU.md` and `registry.json`: rules, targets, limitations, helper provenance, and groups.
- `project/contracts/V0` through `V3` and `diffs/`: source files and minimal changes.
- `project/measure.js`: shared BigInt instrument; `analyze.py`: evidence checks and aggregation.
- `runs/run1` and `runs/run2`: measurement JSON/CSV, individual raw receipts/errors, ABI, and compiler settings.
- `file_summary.csv`, `group_summary.csv`, `comparisons.csv`, and `summary.json`: file and group summaries and separate V3−V1/V3−V2 results.
- Compile, run, validation, version, dependency, and error logs: execution and environment evidence.
- `review_inputs/`: unchanged technical review documents. `runs/initial_instrumentation` is a preliminary execution made before the export was expanded and is excluded from final results.

In JSON/CSV, uint256, wei, seconds, arithmetic discrepancies, and gas are decimal strings. Small step indexes, statuses, and chain metadata may be numeric. For unsafe calls, `expected` is the pre-call state (the required rollback); `unsafe_mathematical_state` and `arithmetic_trace` show the mathematically impossible result. `field_discrepancies` for a successful unsafe call are calculated against that mathematical state, not against rollback. The arithmetic trace is derived from source and operands; it is not an EVM opcode trace. Discrepancies for reverted calls are null, not zero.

## Reproduction

From the repository root, using already installed baseline dependencies without upgrades:

```bash
bash experiments/multifamily_behavioral_v1/arithmetic_comparison_v1/reproduce.sh
```

The command creates a new `runs/reproduction_<UTC>_<pid>` directory, cleans only the new project twice, compiles and executes in separate processes, and runs validation. No public-network access is needed. `project/node_modules` points to the dependencies in `stand_reproduction/20261023T024815Z_oJrMgr/project/node_modules`; moving the study requires preserving that installation. The original Hardhat configuration was copied with only its reporter changed to `spec`; dependencies and compiler/network settings were unchanged.

To check the saved final results:

```bash
python3 experiments/multifamily_behavioral_v1/arithmetic_comparison_v1/analyze.py
```

`build_variants.py` is the saved AI-assisted source generator. It runs from the repository root and regenerates sources and the registry from the saved baseline and review in Downloads. After regeneration, the registry needs execution metadata for the new run; this generator is not needed to reproduce measurements.

This is a local AI-assisted research implementation, not assignment submission text. The approved research question and multifamily plan were retained. At the time of this stage, arithmetic was complete and access control and DoS were planned as later stages.

The reproduction command was additionally run and validated in `runs/reproduction_20261023T041750Z_60407`: two more 244-record runs and all 85 evidence checks passed. This checked the reproduction command; it did not add original contracts. The primary summary refers to `runs/run1` and `runs/run2`.
