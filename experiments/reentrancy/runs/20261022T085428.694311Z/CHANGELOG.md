# Change log

## Source transformations (v1, preserved by v2)

Each baseline is a byte-for-byte copy of its dataset source; manifest.json stores SHA-256 and upstream annotation. Unified diffs in patches/ enumerate every changed line.

| ID | Source | V1: CEI | V2: mutex | V3 |
|---|---|---|---|---|
| R01 | etherstore.sol | Move balances subtraction and lastWithdrawTime update before require(call). | Add private bool and nonReentrant modifier to withdrawFunds. | Both changes. |
| R02 | reentrancy_dao.sol | Move credit reset before external call; retain existing earlier balance subtraction and require. | Add private bool and nonReentrant modifier to withdrawAll. | Both changes. |
| R03 | reentrancy_simple.sol | Cache balance as amount, zero balance before call, retain throw failure path. | Add private bool and nonReentrant modifier to withdrawBalance. | Both changes. |

Mutex code requires unlocked state, sets the lock, executes the body, then releases it. Revert also rolls back lock state. No visibility, pragma, funding function or return signature is changed. Private guard storage and callback behavior intentionally differ. Original vulnerability line comments remain historical baseline annotations and must not be treated as variant ground truth.

## Infrastructure v2

Preserved existing variants and fixed sample. Added per-source selection reasons, V0–V3 IDs, machine-readable settings, compilation before analysis, optional Mythril, raw process records, CSV missingness, environment locking and verification. Replaced v1 runner; earlier raw preflight logs remain in runs/. Existing v1 lock was absent. Added verified official compiler downloader. Setup initially encountered restricted DNS and missing system CA certificates; retries use permitted network access and certifi with verification enabled. Slither's solc-select cache is scoped by VIRTUAL_ENV inside toolchain/.

## Infrastructure v3

Added explicit Mythril --solv and hash-checked local solcx registrations after reviewing installed compiler-selection code. Preserved the complete v2 diagnostic batch and lock. The full v3 batch repeats both tools without changing selected sources, variants, detectors or budgets. This correction addresses compiler reproducibility; findings are not used to choose sources or tool flags. Mythril's legacy runtime required setuptools 80.9.0; caches are scoped under toolchain. Both environments passed pip check before the v3 batch.

## Provenance clarification

The first chat stated criteria before initial variant generation, but v1 protocol.md was saved after generation. README and deviations.json now state this explicitly. V2 saved explicit criteria before the current preparation-metadata extension and before all compilation/analysis; selected Solidity content remained unchanged. This clarification does not alter the frozen sample or results.
