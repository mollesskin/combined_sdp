# UC01: exploratory, AI-assisted developmental behavioral pilot

Approved research question remains: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?” This is one bounded operational case, not a comprehensive answer or assignment submission. Implementation/execution were AI-assisted. Earlier static/pilot results and token-channel fixture results were already known. The locks are developmental freezes before this pilot’s comparative executions, not preregistration before all data.

The selected SmartBugs Curated UC01 source is `dataset/unchecked_low_level_calls/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` at repository revision `230e649123477eff332742a59a1c7cc6dc286cab`. Selection used the registered UC01 → UC02 → UC03 order; UC01 qualified first. See selection_decision.md. V0 is unchanged; no owner, initialization or funding bugs were silently repaired. The studied existing entry is `WitdrawTokenToHolder` because it consumes the real Holders record before the token operation.

A is EVM-level CALL-success validation. B strictly requires a 32-byte application return word equal to 1, without a typed high-level call or an EVM-success requirement. A+B does both. B is not a complete safe-token wrapper: application bytes alone do not authenticate the return channel or honest transfer. The three declared mock modes do not test unusual revert payloads. See protocol.md and source_changes.md for guarantees, limitations, independent operationalization and minimal patches.

All four variants and the synthetic token fixture were compiled with exact native solc 0.4.19, optimizer disabled, then deployed in fresh in-process Byzantium chains. Normal setup/probe/scenario inputs and gas budgets match across variants. Results are in generated_results.md and the CSVs, derived by tests/summarize.py from raw observations. ABI equality is verified but is not claimed as behavioral equivalence.

## Evidence layout

```
protocol.md                    # requirements, invariants, metrics, comparison rules
scenario_inputs.json           # fixed synthetic inputs
protocol.lock.json             # before treatment coding/comparative runs
selection_decision.md
source_changes.md
source_manifest.json
variants/{V0,V1,V2,V3}/TokenBank.sol
variants/{V1,V2,V3}.patch
fixtures/BehaviorToken.sol      # synthetic fixture, not benchmark
execution.lock.json            # runner/fixture/treatments frozen before comparison
 tests/run_pilot.py             # no analyzer or external-provider calls
 tests/summarize.py             # derives CSV and comparisons from saved raw data
 tests/validate_evidence.py     # preservation, trace and recomputation checks
runs/<run-id>/raw/              # exact inputs, versions, commands, compile logs,
                               # receipts, computation trees, setup/probe/state
runs/<run-id>/behavioral_results.csv
runs/<run-id>/invariant_results.csv
runs/<run-id>/summary.json
comparison/{comparison,reproducibility}.json
run_log.json
validation.json
preservation_snapshot.json
artifact.lock.json
```

Original run IDs: `20261022T_behavioral_repeat1` and `20261022T123234Z`. The first uses a descriptive date-prefixed identifier rather than a complete UTC timestamp; its exact execution UTC times remain in raw/command.json and raw/execution_summary.json. This naming deviation does not alter trials; original evidence was not renamed or rewritten. No trial/scenario/metric deviations were made. No robustness cases were appended after results.

CSV invariant rows include applicability and inconclusive states. Low-level output/status come from the actual PyEVM child computation, retained even if the parent reverts; they are not guessed from fixture mode. Token success flag follows that child computation’s is_error under CALL semantics. Outer receipts and post-transaction states determine committed effects. Errors and warnings are retained; successful security reverts are not infrastructure errors.

The token discrepancy is an unfulfilled **acknowledged delivery**, not proven theft/economic damages. Consumed holder entitlement is reported separately in wei: Holders is not a token ledger and there is no token/ETH exchange-rate conversion. The bank’s ETH staying unchanged is recorded. Security proportions use only the declared negative scenarios, not real-world attack-prevention probability. Repeat counts are reproducibility checks on one contract.

## Exact reproduction commands

From this project root, reuse the existing unchanged local environment and compiler:

```sh
cd /Users/moldir_2024icloud.com/smartbugs-curated
pilot_python="$PWD/experiments/multi_vulnerability/compatibility_v2/toolchain/venv/bin/python"
pilot_run1="experiments/behavioral_pilot_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r1"
PYTHONDONTWRITEBYTECODE=1 "$pilot_python" experiments/behavioral_pilot_v1/tests/run_pilot.py --output "$pilot_run1" --repetition 1
pilot_run2="experiments/behavioral_pilot_v1/runs/$(date -u +%Y%m%dT%H%M%SZ)_r2"
PYTHONDONTWRITEBYTECODE=1 "$pilot_python" experiments/behavioral_pilot_v1/tests/run_pilot.py --output "$pilot_run2" --repetition 2
PYTHONDONTWRITEBYTECODE=1 "$pilot_python" experiments/behavioral_pilot_v1/tests/summarize.py "$pilot_run1" "$pilot_run2" --comparison-output "experiments/behavioral_pilot_v1/comparison/$(date -u +%Y%m%dT%H%M%SZ)_reproduction"
```

Use fresh output paths; the runner rejects existing run directories. Each command runs an independent Python process and constructs fresh state per trial. The runner verifies the protocol/implementation locks before execution. Native compiler path is fixed in run_pilot.py; its SHA/version is recorded in each run. Reproducing on another OS requires the same solc build/compatible runtime or a separately documented portability qualification, not silently changing compiler.

Actual Python and package versions are in each raw/versions.json; full pinned dependency lists are in raw/requirements.txt. Existing environment: Python 3.12.0, web3 8.0.0, eth-tester 0.14.0b1, py-evm 0.12.1b1, eth-abi 6.0.0. No packages were installed or upgraded for this pilot. Compiler is 0.4.19+commit.c4cbbb05.Darwin.appleclang. Fixed local VM/genesis/budgets are in scenario_inputs.json. Nothing uses HTTP, WebSocket, mainnet/testnet/forks, real wallets or real funds. No Slither/Mythril/PES work was performed.

Current source diffs, original hashes, raw logs and the two freezes are kept alongside results. Prior artifacts are verified unchanged by validation.json; toolchain/cache trees were used read-only, and bytecode-cache writes were disabled. Validation also cross-checks all primary receipts/child traces and reproduces derived CSV/summary bytes in a temporary directory. Tests cover this defined behavior only; gas-near-exhaustion, nonstandard/fee/rebasing/dishonest tokens, malformed return data, unusual revert payloads and other contract functions are outside scope. Scaling or adding these cases requires a separate reviewed phase.
