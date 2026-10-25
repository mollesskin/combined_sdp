# Exploratory, AI-assisted developmental behavioral pilot

Research question, unchanged: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?” This one operational case does not answer the RQ comprehensively.

This is NOT a preregistration made before all data. The reentrancy/static results, prior UC baseline channel-fixture outcomes, and the earlier checker’s proposed treatment expectations were already available to the AI-assisted implementation. This protocol is frozen before this pilot’s comparative executions, to prevent changing cases/metrics to obtain a preferred winner. Static PES, its thresholds and its old files remain separate and unchanged. No behavioral-to-PES conversion or new ordinal scale.

## Case, requirements and components — written before implementation

Select the first suitable registered case in UC01, UC02, UC03 order. UC01 is the original TokenBank, source `dataset/unchecked_low_level_calls/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol`, annotated line 44, pinned Solidity 0.4.19. V0 is copied byte-for-byte. No ownership/funding/init repair. The deployer remains original Ownable.owner; same deployer invokes initTokenBank, which writes the shadowed Token.owner. A local holder deposits 2 ether (synthetic local wei, not real funds) above MinDeposit=1 ether. The owner calls existing `WitdrawTokenToHolder(holder, token, 5)`. The contract clears Holders[holder] before calling its inherited WithdrawToken; revert of the outer transaction must roll that back.

Failure policy: **atomic rejection** of a token withdrawal that does not complete the intended transfer. Normal transfer must deliver exactly the requested amount and consume the pre-existing positive entitlement. A false return or execution revert must be reported by an outer revert and preserve entitlement and asset balances. This applies identically to every variant. Rationale: the withdrawal consumes a holder record with no pending/retry queue, failure return field, or success event; accepting nondelivery would erase that record without fulfilling the withdrawal. Introducing a recovery workflow would be an unrelated redesign. Holders is an ETH-denominated deposit/eligibility record, NOT a token ledger or a token-to-ETH valuation.

A (V1) validates the low-level EVM success flag with require. It guarantees that this call did not report EVM execution failure; it does not guarantee ERC20 transfer, true return, correct amount or honest token logic.

B (V2) validates the application return encoding: exactly 32 bytes, the full ABI word exactly 1. Return size is checked BEFORE copying; never use a stale memory word or a permissive nonzero bool. It does not separately require the EVM flag. Solidity 0.4.19 low-level CALL exposes that flag while Byzantium RETURNDATASIZE/RETURNDATACOPY expose return or revert payload independently. No typed high-level call is used: that would also propagate failure and confound B with A. This is an isolated, strict application-data validator, not a claim that B is a complete production-safe token wrapper. A deliberately reverting callee can return a boolean-looking revert payload; that fact is already known and is not added as a comparative scenario here. B is not weakened by accepting empty/malformed output: both are rejected by its exact decoding rule. B does not guarantee authenticity of the return channel or actual honest-token delivery.

V3 requires both the EVM flag and the same exact B decoder. Only the single annotated low-level transfer statement is modified. Original ABI, inheritance, storage, access checks, other calls and dataflow remain unchanged. Call success is captured in protected variants without adding storage or events. These are called defensive checks/components, not independently established named design patterns. Independence is operationally identifiable: EVM execution status and bytes returned are different observables, and the decoder can inspect bytes without testing the flag. If compilation shows hidden flag propagation or safe isolation cannot be implemented, stop rather than relabel a high-level call B-only. No prediction that V3 must win.

## Fixed conditions and synthetic inputs

- All sources including fixture: exact native solc 0.4.19; `--combined-json abi,bin`; no optimizer flags; compiler timeout 60 s. Do not change compiler to obtain treatment effects.
- Existing isolated Python environment from compatibility_v2; in-process EthereumTesterProvider/PyEVMBackend with ByzantiumVM, genesis timestamp 2000000000, difficulty 1, block gas limit 30000000. Explicit tx gas 12000000, gasPrice 1. Calls use identical budgets. No RPC, mainnet forks, public chain, real wallets or funds.
- Fresh backend with the same deterministic test keys/accounts for EVERY variant × scenario × repetition. account[0] deploys/administers; account[1] is holder and token recipient. Fixture token starts with 100 smallest units at the bank, 0 at holder. Intended token amount=5. No allowance is required by transfer; holder-to-bank allowance is recorded as 0 and stays 0. Initial holder entitlement=2000000000000000000 wei; bank ETH balance is the same amount.
- S1 mode 0: honest synthetic token debits bank 5, credits holder 5 and returns canonical true.
- S2 mode 1: normal EVM return with canonical false, no token movement.
- S3 mode 2: empty-data revert, no token movement.
- No robustness scenarios (empty/malformed successful returns or unusual revert payloads) are included. These are not representative ERC20 claims and must not be introduced after comparative outcomes. Mocks provide only these three fixed modes.
- Every trial first verifies deployment/setup and tests a normal withdrawal on a snapshot of that initial state (mode 0). Its actual receipt and states are saved. Restore the snapshot, set the scenario mode, verify matched initial state, then execute the scenario. Snapshots restore nonce/state as well as balances. Each variant also has S1 as a primary legitimate-operation trial.
- Execute two complete fresh-state repetitions, 4 variants × 3 scenarios = 12 primary trials per repetition, 24 total. Repetitions test determinism, not independent contracts or statistical replication. Each trial additionally has one legitimate-operation probe.

## Observations and invariants (fixed for all variants)

Compilation/deployment/setup/infrastructure failures are retained and marked inconclusive, never a security pass or zero discrepancy. Raw traces capture receipt, outer/inner computation error/status, calldata, output bytes, relevant before/after state and errors. PyEVM host-side computation observation is read-only, not contract instrumentation. Save the token child computation’s raw output even when the parent reverts; only receipt/state are authoritative for committed changes. If unavailable, report missing, never infer from token mode.

Let a=5; b0,b1 be token.balanceOf(bank) before/after; h0,h1 the holder token balances; e0,e1 the bank’s Holders[holder] in wei; q0,q1 bank ETH wei; t the actual outer receipt status; d=h1-h0.

- I1 acknowledged_delivery (all): t=1 implies d=a, b0-b1=a and e1=0. A successful outer transaction is an acknowledgement of this existing void-return operation; it is not an emitted event.
- I2 entitlement_preserved_on_nondelivery (all): d!=a implies e1=e0.
- I3 token_conservation (all): b1+h1=b0+h0, under the fixed fixture’s no-fee/no-mint-during-withdraw assumption.
- I4 atomic_failure_policy (S2/S3 only): t=0, b1=b0, h1=h0, e1=e0. A correctly rejected transfer is correct behavior, not financial damage.
- I5 ether_frame (all): q1=q0; token withdrawals must not move bank ETH.
- I6 legitimate_operation (S1 only, and each separate mode-0 probe): t=1, d=a, b0-b1=a, e1=0, q1=q0 and I3 true.

Record each applicable invariant independently, applicability, observed fields, pass/fail and violation identities/count. Counts are descriptive correlated checks, not independent vulnerabilities or a new protection score. Missing measurements make invariants inconclusive, not satisfied.

Contract-specific asset/accounting discrepancy: acknowledged token shortfall D=max(0,a-d) if t=1, else 0, in token smallest units. Normalize only this same-unit quantity as D/a using exact fractions, retaining D and denominator. This measures unfulfilled acknowledged delivery in this controlled operation, not economic loss probability or full damages. Separately record unfulfilled consumed entitlement E=max(0,e0-e1) if d!=a, else 0, in wei. Never add D and E or convert entitlement wei to tokens: no exchange rate or token ledger exists here. Record raw delivered delta and state even if discrepancy is 0. Infrastructure failure => D/E unknown (blank), not zero.

Negative-scenario requirements: among applicable completed S2/S3 trials, a scenario satisfies security requirements only when I1–I5 all pass. Report numerator and denominator per variant per repetition and pooled descriptive reproducibility totals. Never call this real-world attack-prevention probability. Denominators exclude infrastructure failures but always report excluded/expected counts; no complete-evidence claim if any are missing. Normal functionality must separately pass all defined legitimate probes and S1 before any superiority claim.

## Comparisons fixed before execution

Compare V3 vs V1 and V3 vs V2 separately using matched scenarios/inputs and both repetitions; do not pool incompatible units into a score. Evidence vector includes each applicable invariant, raw D and E, and legitimate functionality. Additional observed protection: no worse on any security invariant/discrepancy, strictly better on at least one, with all normal-functionality checks preserved. Equal observed protection: same per-scenario security pass vector and raw discrepancies, legitimate functionality preserved. Security regression is the reverse dominance with normal functionality preserved. Functional regression: V3 fails a legitimate check that comparator passes; if security improves at the same time, label trade-off. Mixed security gains/losses are trade-off. Missing/invalid/mismatched evidence is inconclusive. Strong additional benefit over BOTH requires additional observed protection in BOTH separate comparisons. A tie with B must be reported as a tie. No case replacement/test adaptation after outcomes.

## Freeze and execution

Save protocol, structured scenario inputs/invariant definitions, selection rationale and SHA-256/timestamp before coding treatments. Save implementation/fixture/runner hashes in a second pre-comparison execution lock. Label both as developmental freezes with prior knowledge disclosed, not all-data-naive preregistration. A preflight check enforces both locks and original V0 hash. Save full command, dependency/compiler versions, failures and raw receipts/computations before deriving CSV summaries. No Slither/Mythril invocation, no static experiment expansion, no change to approved RQ or frozen PES.
