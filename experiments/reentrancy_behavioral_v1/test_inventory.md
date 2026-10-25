# Existing tests and source review before new runs

Approved RQ unchanged: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?” This new phase is exploratory, AI-assisted developmental work with previous static, functional and controlled-reentry outcomes already known. Its freeze is before these new comparisons, not preregistration before all data.

Read-only sources: original reentrancy contracts/{baseline,cei,guard,cei_guard}/{etherstore,reentrancy_dao,reentrancy_simple}.sol, prior manifest; compatibility_v2/scripts/check_functions.py, fixtures/LocalFixtures.sol and validation/functional_20261022T105453.604060Z/evidence/{checks,functional_evidence,summary}.json.

1. **ABI/interface:** full ABI/signature equality in original qualification; neither state preservation nor vulnerability prevention follows from ABI equality.
2. **Ordinary functional tests:** deposit/withdraw, second allowed withdrawal (RE01 waits a week; RE02/03 redeposit), rejecting receiver rollback and later successful retry. These are appropriate and retained with the same legitimate actions.
3. **Security characterization:** one local receiver callback tries the same withdrawal once. The previous checker expected the baseline to pay twice and protected variants once. That is successful characterization, not a security pass for baseline. New uniform invariants must treat unauthorized extra payout/accounting corruption as violations regardless of variant. No static warning counts/PES are imported into behavioral outcomes.

Existing receiver fixture implements bounded retryOnce (one retry), reject flag and original selector-based fund/withdraw. It is reused byte-for-byte as a contract extract, compiled with its original fixture compiler0.4.24. Actual nested call status/data is read from host computation trees, not added instrumentation. A successful zero-value nested call in RE03 CEI is not automatically a vulnerability; payouts and state, not raw callback counts, define protection.

## Source suitability and implementation integrity

RE01 EtherStore, solc0.4.10, annotated call line27: checks balance/request<=1ether/week, then external value call, debit and time update. CEI moves both debit and time update ahead of call. Mutex guards the withdrawal and clears its lock after body. Combination retains both. RE01 normal two withdrawals require >=week after first; rejection must roll back debit/time/lock. A callback before debit/time update is the benchmark target. Original vulnerable path can wrap uint256 credit; raw value is recorded rather than silently repaired.

RE02 ReentrancyDAO, solc0.4.19, annotated call line18: cached account credit, aggregate balance decrement before call, account credit reset after. CEI moves reset before call; Mutex guards original withdrawal; combination both. Aggregate and mapping are private/default nonpublic: local storage observation avoids altering ABI. Aggregate may track actual ETH while understating remaining claims after overpayment; this is measured separately, not assumed to equal claim sum.

RE03 Reentrance, solc0.4.15, annotated call line24: call with userBalance before reset. CEI caches amount, resets then calls; Mutex guards original withdrawal; combination both. Public getBalance confirms storage reading. A nested zero-credit call under CEI may succeed without transferring extra; do not score it as inferior to a rejected nested call merely due to control-flow differences.

All twelve implementations are already existing, minimal and coherent for these scoped withdrawals from source inspection. No implementation is changed, weakened or corrected by this phase. Compiler pin is fixed per contract, not homogenized across contracts; native solc0.4.10 is used directly despite its known Mythril-wrapper exclusion. There is no analyzer invocation. Full behavior outside the chosen scenarios and inter-function reentry is not established.

## Read-only storage observation

Solidity0.4.x source declaration order plus uint256/mapping alignment gives the following slots; variants with the first private bool lock shift the following declarations by one slot. Each mapping element is keccak256(left-padded address || uint256 slot). Read using local get_storage_at; save raw words and offsets. Validate expected deposit deltas for both actors in every setup; cross-check RE01 balances/lastWithdrawTime and RE03 getBalance through their existing getters. No source instruments/getters are added.

| ID | V0/V1 credit mapping | V2/V3 credit mapping | Aggregate slot V0/V1 -> V2/V3 | Other slots |
|---|---:|---:|---|---|
| RE01 | 2 | 3 | N/A | lastWithdrawTime1->2; withdrawalLimit0->1; lock0 in V2/V3 |
| RE02 | 0 | 1 | 1->2 | lock0 in V2/V3 |
| RE03 | 0 | 1 | N/A | lock0 in V2/V3 |

Raw credit values use mathematical integers for claim summation; do not wrap Python sums to hide EVM storage corruption. No ledger is inferred from ABI absence. If slot/metadata/hash/setup validation fails, preserve the blocker and mark evidence inconclusive, not zero or security pass.
