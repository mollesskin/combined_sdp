# SimpleDAO V0–V3 behavioral comparison

Case: `dataset/reentrancy/simple_dao.sol` (SHA-256 `40ffea56c722280688eba923676992d20be7623dcf724393c1c7ca1ef24e0ae5`). This case was not among the historical 23 full comparisons. The original file is the unchanged V0 input.

## Treatments and independence

- V0: original benchmark bytes.
- V1 / A: Checks–Effects–Interactions (CEI): decrement the caller's credit before the external value call, without adding a lock.
- V2 / B: contract-local mutex on `withdraw`, without moving the credit update.
- V3: both A and B, with each edit identical to its standalone arm.

A protects accounting during an external callback. B refuses a nested entry into the protected function. Both apply to the same reentrancy exploit through different control points; neither edit includes the other. This case tests whether both standalone mechanisms work and whether combining them changes the measured outcome. It does not assume that V3 is superior; this fixture may show equivalent protection. No treatment is claimed to fix the separate ignored `bool res` result.

## Fixed conditions and oracle

All four arms use native `solc 0.4.2`, unoptimized `--combined-json abi,bin`, the same local Hardhat EVM, and the same attacker bytecode. A source diff against V0 is saved. Deploy a fresh DAO for each scenario/arm.

1. Ordinary workflow: an EOA donates 1 ether to itself, queries credit 1 ether, withdraws 1 ether, then has credit 0 and DAO balance 0. The withdrawal must succeed.
2. Nested callback: a donor funds a separate credit of 1 ether; an attacker contract receives 1 ether credit. The attacker calls `withdraw(1 ether)` and its payable fallback makes exactly one nested `withdraw(1 ether)` attempt. The nested call uses a low-level call so a lock rejection does not revert the outer payment. Observe attacker's received ether, remaining attacker credit, and DAO balance. V0 is expected to pay 2 ether and wrap the attacker's credit. A protected arm must pay at most its 1 ether credit and leave credit 0. The donor credit remains 1 ether.
3. Rejected callback: a receiver that rejects ether withdraws 1 ether after being credited. Record credit and DAO balance to expose the unchanged unchecked-call limitation. Do not include this scenario in the reentrancy protection score.

The unit is this one source contract, not each run or each arm. Compare V3 with V1 and V2 separately, and report any loss of ordinary behavior. A single deterministic run is a functional check; no statistical inference or static-detector score follows from it. Exact compiler, variant, fixture, command, and result artifacts are retained in this directory.
