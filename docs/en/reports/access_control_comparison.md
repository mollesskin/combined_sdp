# Access-control study: completed results

This is an AI-assisted local research implementation. The approved research question and multifamily plan were retained; this is not assignment submission text. Arithmetic was not rerun or changed: a read-only hash audit of all 1,760 files passed. DoS had not yet been run at this stage and was the next planned study.

## Scope and completed checks

All **16 of 16** access-control files in the saved pinned baseline `test-results.json` were reviewed. Completed evaluations were:

- **Two full V0/V1/V2/V3 comparisons:** `arbitrary_location_write_simple` and `wallet_04_confused_sign`.
- **Twelve V0/F1 single-fix comparisons:** three `incorrect_constructor_name` files, `mapping_write`, `multiowned_vulnerable`, `mycontract`, `parity_wallet_bug_2`, `phishable`, `simple_suicide`, `unprotected0`, `wallet_02_refund_nosub`, and `wallet_03_wrong_constructor`. These are excluded from combination comparisons.
- **Two unresolved cases:** `FibonacciBalance` and `proxy`. Their V0 copies, original hashes, reviews, and reasons were retained. Both V0 files compiled; comparative executions and metrics are N/A.

Thirty-four source variants were saved, of which 32 were executed. Including the fixture, 35 Solidity source files compiled. Every variant actually used **solc 0.4.25** with optimization enabled at 200 runs, and the local Hardhat **Shanghai** fork without an external-network fork. New projects use the same compiler matrix and network settings. The configuration changed only in the reporter, with the exact diff saved. Node v20.20.0, npm 10.8.2, and Hardhat 2.22.5 were used; dependencies were not upgraded.

There are 47 unique case-by-scenario definitions and 110 variant-by-scenario instances per run. Each scenario begins with `hardhat_reset`, a fresh deployment, and the same external conditions. Each final run recorded **266 observations**: 258 measured transactions and eight separate deployment-owner checks. Deployment and setup transactions are saved as evidence but are not added to those 258. Two final runs produced 532 observations; they are repetitions, not additional original contracts.

Under the reviewed `AC_INIT_CLONE` grouping, the three Missing files form one group. There are 14 groups in total, 12 executed: two full-comparison groups and ten single-fix groups. Singleton status does not prove independence. File-level and group-level results are saved separately in `file_summary.csv` and `group_summary.csv`.

## V3 compared with A and B

| Comparison | Security requirements | Permitted functionality | Overall call oracle |
|---|---|---|---|
| V3 vs V1/A | 8 ties, 0 improvements or regressions | 14 ties, 0 improvements or regressions | 22 ties |
| V3 vs V2/B | 8 ties, 0 improvements or regressions | 12 ties and 2 improvements, 0 regressions | 20 ties and 2 improvements |

For `arbitrary_location_write_simple`, A, B, and A+B passed all nine observations. Both mechanisms address the same no-underflow property: a nonempty-array check before the operation, and checked subtraction with a post-result check. They overlap; they are not two independent threat classes.

For `wallet_04`, V1 and V3 passed all 13 observations. V2 passed 11/13: the original incorrect `>=`, deliberately retained in B, rejects zero and partial withdrawals when credit is nonzero. This is one inherited functional defect observed in two calls, not two vulnerabilities. V0 also rejects those calls. V3 restores the permitted domain through A. The combination showed **no additional protective effect** over A or B in the tested scenarios. Adding B to A caused no new functional regression. B cannot be described as fully preserving permitted functionality.

Gas was compared separately only when inputs, pre-call contract state, and execution status matched. For V3−A, 14 successful comparable calls had gas differences from 0 to 135; eight reverted calls had a difference of zero. For V3−B, 12 comparable successful calls ranged from −2 to 0 gas; eight reverted calls ranged from −7,121 to 0 gas. The two calls with different functionality under V3 and B were not compared for gas. An early guard versus a late rollback after transfer can explain lower cost for a forbidden call. Deployment gas and a cost-effectiveness score were not calculated.

## Single-fix outcomes and concrete effects

All 12 F1 variants passed the common oracle in the executed scenarios: **54/54 permitted observations** and **35/35 security observations** (33 forbidden/no-effect and two must-revert). This is the tested set, not proof that every possible legitimate behavior is preserved.

- Constructor fixes assign the deployer as owner/creator at deployment and remove the misnamed runtime initializer. No artificial post-deployment workflow was introduced. The ABI/lifecycle change is disclosed. In Missing, a call to the removed selector can succeed through the fallback but has no effect on authority; that is a correct no-effect outcome.
- `mapping_write` retains the arbitrary uint256 key domain. A mapping prevents an array index from overwriting the owner slot. Owner remains zero because its initialization was not repaired. The artificial 1-wei funding is disclosed; lawful owner withdrawal is N/A. An absent key now reads as zero rather than producing the old array behavior, a semantic extension rather than full equivalence.
- `multiowned` preserves assignment and revocation of delegated rights and permitted payouts. An outsider cannot appoint itself.
- The `tx.origin` fixes allow a direct owner call and prevent an intermediary from inheriting the origin's authority. No recipient allowlist was introduced.
- Parity was evaluated only as a directly deployed `WalletLibrary`, as in the author's test. A guard covers all three initialization entry points while the existing `only_uninitialized` remains. A proxy-compatible deployment-authority and storage policy was not resolved or claimed as tested.
- For `simple_suicide`, deployer authority was explicitly inferred from the owner role in the functional test; it was not claimed to exist in the original source. The no-argument signature and code removal under Shanghai were checked. This is one experimental lifecycle policy, with no invented second mechanism.
- The refund fix preserves each depositor's right to a refund and atomic rollback when the recipient reverts. An independent mathematical claim ledger records two excess payouts of **6 wei** each at separate points in one V0 scenario; these are not treated as independent vulnerabilities. F1 has no excess payout. In `wallet_04`, a V0 forbidden withdrawal of 11 wei with a credit of 10 produces a 1-wei excess; a 1-wei withdrawal with no credit also produces a 1-wei excess. Protected variants revert both calls.

Protection was not judged by reverts alone: successful harmless no-op calls, correct rejections, and recipient state adjusted for transaction gas were retained. Address, credit, ETH, and violation measures were not combined into PES or a universal scale.

## Unresolved requirements

**FibonacciBalance:** The source explicitly permits fallback library calls, but shared storage layout permits changing the library pointer. An architectural comparison needs precise permitted selector/`setStart` semantics and a correct Fibonacci sequence/payout model. A simple owner-only ban would remove part of the original workflow without justification.

**Proxy:** Neither source nor test defines the trusted set of callees and delegated users. A benign method in the same attacker fixture does not justify an allowlist. A caller guard plus target policy would introduce new requirements solely to create a combination.

Neither case was replaced with another file or converted into a zero effectiveness value.

## Clean repetition and reproduction

Final `runs/run1` and `runs/run2` matched in all observations, exact inputs, states, setup, receipts/errors, and gas, apart from new raw output paths. The second run followed a clean and recompilation. **All 107 evidence checks passed**; the final runs had no infrastructure, setup, or compilation errors. Every reverted transaction preserved observed rollback. V0 contract violations and V2 functional rejections remain data, not infrastructure errors.

From the repository root:

```bash
bash experiments/multifamily_behavioral_v1/access_control_comparison_v1/reproduce.sh
```

The script creates a fresh `runs/reproduction_<UTC>_<pid>` directory, performs clean/compile/run twice in the access-control project, and executes `analyze.py`. It never overwrites an existing output directory. The command was additionally run successfully; its new path is recorded in `reproduction_check.log`, with two runs and `validation.log` in that directory. These repetitions do not increase the primary sample size.

To validate saved final results:

```bash
python3 experiments/multifamily_behavioral_v1/access_control_comparison_v1/analyze.py
```

`project/node_modules` links to the installed baseline at `stand_reproduction/20261023T024815Z_oJrMgr/project/node_modules`; moving the study requires preserving that installation. Reproduction does not install packages or invoke public networks, arithmetic, or DoS. The build generator runs only from the repository root; ordinary measurement reproduction does not need it. Running it again regenerates source/registry files and requires new execution metadata.

## Verifiable artifacts

- `PROTOCOL_RU.md`, `CASE_REVIEW_RU.md`, and `registry.json`: per-file permission models, baseline defects, existing mechanisms, targets, and decisions.
- `project/contracts/{V0,V1,V2,V3,F1}`, `diffs/`, and `SHA256SUMS.json`: sources, exact diffs, and hashes. `ResearchDebit` is an AI-assisted helper, not an original third-party library.
- `project/measure.js`, `analyze.py`, and `reproduce.sh`: measurement code, oracle, ledger, and evidence checks.
- `runs/run1` and `runs/run2`: CSV/JSON, individual raw receipts/errors/setup output, compiler settings, ABI comparisons, and scenario manifests. ABI equality checks only the interface; constructor changes are recorded separately.
- `compilation_manifest.json`: actual compiler and settings for all 34 saved variants, including unresolved V0 files.
- `summary.json`, `file_summary.csv`, `group_summary.csv`, and `comparisons.csv`: file/group summaries and separate V3−A/V3−B results.
- `inputs/`: unchanged source review, author tests, saved report, and baseline log. The working baseline `project/scripts/test-results.json` was absent on inspection; the historical pinned report (195/91) and reproduction log (71/33) have different provenance and are not presented as new protected-variant results.
- `frozen_before_first_run/`, `runs/initial_01`, `initial_01.log`, and `ERRORS_RU.md`: original protocol/instrument and complete preliminary run with a subsequently corrected oracle type error. Final files did not replace them.
- Version, dependency, config-diff, command, compile/run/validation logs: environment, configuration, and command evidence.
- `arithmetic_before.json` and `preservation_check.json`: read-only confirmation that the prior study was preserved.

In final measurement JSON/CSV, uint256, wei, arithmetic discrepancies, and gas are decimal strings. Small step, status, and receipt metadata can be numeric. N/A/null is not converted to zero; an applicable numeric zero is a real zero result. `contract_outflow_wei` is a signed net decrease and is negative for an incoming deposit, not a “negative attack.” `unauthorized_outflow_wei` applies only to forbidden financial calls. `excess_payout_wei` separates payout above credit or the correct amount from the entire forbidden transaction. Sender balances before and after a reverted transaction differ due to gas in raw accounts; comparison normalizes actual paid gas. Storage coverage is disclosed in `observe()`: this is observed rollback, not formal verification of the entire EVM state space.

The study is limited to these scenarios, the chosen single-fix permission models, and the stated local fork. Exhaustive/fuzz verification, full equivalence, and reconstruction of the historical Parity proxy architecture are not claimed.
