# RE01–RE03 local behavioral protocol

Exploratory, AI-assisted developmental pilot. Previous reentrancy results are known; this is a developmental freeze before new comparative runs, not an all-data-naive preregistration. Approved RQ stays as quoted in test_inventory.md. UC01–UC03 are closed by immutable reference. No PES calculation/change, static warnings in behavioral metrics, new contract selection, source repair, public chain/testnet/RPC/fork or real assets.

## Conditions and reuse

Use exactly the existing original V0, CEI V1, Mutex V2 and CEI+Mutex V3 sources. V0 must match benchmark bytes and metadata category/lines. Freeze paths/hashes and read-only storage schema before runs. Source review is in test_inventory.md. Compile each four-version group using its existing exact native solc (.4.10 RE01, .4.19 RE02, .4.15 RE03), --combined-json abi,bin, optimizer disabled, timeout60s. Fixture is the unchanged LocalRecipient contract extracted from prior fixture, compiler0.4.24. Full ABI comparison is a separate interface result, not equivalence proof.

Same existing isolated Python environment. All in-process PyEVM ByzantiumVM, genesis timestamp2000000000,difficulty1,gas_limit30000000; tx gas12000000,gasPrice1. Fixtures and bank are deployed afresh per variant/scenario/repetition. Deterministic accounts: account0 controller/sender pays gas; account1 independent depositor (“other”), receiver fixture is withdrawing credited actor. Measuring receiver contract ETH avoids gas-cost confounding. Fixed U=10**18 wei, synthetic local ETH only. Same actions/values/budgets across four variants within each ID. No additional callbacks/robustness cases selected for V3 superiority.

## Three existing scenarios, same set for every variant

O1 ordinary_sequence (functional): receiver reject=false,retry=false. Deposit other actor2U and receiver2U for RE01 or U for RE02/03. Withdraw receiver once (RE01 requestedU, RE02/03 full creditedU). RE01 advance local timestamp by604801s and withdraw remainingU; RE02/03 deposit receiverU again, then withdraw. Measure each withdrawal separately before/after, and verify intermediate legitimate deposit/time advancement. The second allowed operation checks lock release; no private-lock read alone substitutes for it.

F1 rejecting_receiver_then_recovery (functional/rollback): other2U and receiverU funded. Configure reject=true,retry=false. Withdrawal must revert and preserve bank ETH, receiver ETH, both credits, RE01 timestamp, RE02 aggregate and lock. Change only reject=false, then retry withdrawal; it must succeed exactly once for U. All snapshots are before the actual withdrawal, after configuration, so configuration tx is not confused with rollback.

S1 one_bounded_reentry (security): other2U and receiverU funded; receiver reject=false,retryOnce=true. One external withdrawal, same selector/amount. Fallback tries that withdrawal once; it does not require nested success. Overall requested payout/entitlement cap=U. A safe successful outer operation pays U, debits actor credit byU, preserves other credit, and leaves bank covering all remaining tracked claims. A complete outer rejection with unchanged financial state can preserve security but would fail the independently defined permitted outer-operation functionality requirement in this fixture (nested failure is caught). Save actual nested success/failure and every value call but do not use it alone as the security outcome.

These are the previously used sequences, enriched with state/accounting observation. No victim extraction, multi-function reentry, attacker depth search or new attack scenario is introduced. Cases match source withdrawal entry points and annotated external call sites. State resets completely between scenarios/variants/repetitions, but O1/F1 intentionally preserve state across their declared sequential steps.

## Required state properties and measurements

For each withdrawal step, b0/b1=bank ETH, r0/r1=receiver ETH, c0/c1=receiver credit, o0/o1=other credit, g0/g1=RE02 aggregate (N/A others), t0/t1=RE01 lastWithdrawTime (N/A others), p=r1-r0, w=U expected legitimate amount. Read known-actor credit words by frozen storage schema, validate setup and existing public getters where present; no getter instrumentation. All listed amounts are integer wei; raw corrupted uint256 values preserved.

I1 payout_cap: p<=w and p>=0 (for S1 the one authorized request, not number of nested calls). For legitimate/recovery steps exact payout is additionally required by I6.
I2 accounting_consistency: credit decrease equals actual payout, c0-c1=p with 0<=c1<=c0, and o1=o0. RE02 additionally g1=g0-p and g1=c1+o1. This captures a stale/reset account credit or aggregate/claim mismatch. Other users are all known credited actors; no forced ETH or hidden deposits in these fixtures.
I3 financial_conservation: b0-b1=p, and b1+r1=b0+r0. No gas is charged to bank/receiver; they do not selfdestruct or forward assets in fallback.
I4 failed_transaction_rollback (only the intended rejected F1 step, or any actually reverted withdrawal): t=receipt0 and all financial/credit/aggregate/RE01-timestamp state unchanged, guard false afterward where applicable. A rollback is not automatically damage. For the intended rejected step success is a violation of this rejection requirement.
I5 claim_coverage: b1>=c1+o1. For RE02 additionally g1=c1+o1 and b1>=g1. Sum in unbounded host integers; never wrap the sum to conceal corrupted storage.
I6 permitted_operation (O1 withdrawals,F1 recovery,S1 outer request): receipt1,p=w,c1=c0-w,o1=o0, matching RE02 aggregate debit and RE01 lastWithdrawTime=current withdrawal block timestamp; mutex cleared for V2/V3. Also I3 passes. Nested attempts are not legitimate operations required to succeed. I6 for F1 intended rejection is N/A; rollback evaluated I4 instead.

Always record outer status, callback count (descriptive), actual nested CALL status/value/output, raw storage/getter agreement, credits/balances before/after, applicable invariant identities, violations, setup errors and raw paths. Missing/failed infrastructure is inconclusive, never pass or zero. Successful unsafe execution is completed with violated security properties, not an infrastructure error.

Consequences, measured separately (no combined score):
- excess payout E=max(0,p-w) wei for the one authorized withdrawal; E/U exact fraction (fixed positiveU).
- credit mismatch M=abs((c0-c1)-p) wei, with a separate credit-increased/wrap flag. This is an accounting inconsistency quantity, not additional economic damages, and enormous wrapped storage values are not plausible monetary valuation.
- claim-coverage shortfall D=max(0,c1+o1-b1) wei. It is a discrepancy of recorded claims vs assets in the tracked fixture, not proof of total recoverable losses. Raw malformed credit can dominate D; retain it and interpret alongside E.
- RE02 aggregate-vs-claims signed difference g1-(c1+o1), wei, N/A other IDs. Do not replace missing with0.
Do not sum E/M/D or combine with static finding counts, callbacks, gas or PES. Gas measured descriptively, transaction budget fixed; no near-OOG conclusions.

## Evidence and comparisons

Two independent clean-process launches; each includes3 original contracts ×4 existing source variants ×3 scenarios=36 scenario trials, 60 withdrawal steps (2O1+2F1+1S1 per variant); total72 scenarios/120 steps. Twelve source variants, not120 contracts. Record source/fixture hashes, compiler builds, ABI comparison, inputs, commands/environment, full compile stdout/stderr and actual receipts/computations even for expected revert. Preserve failures and skip blocked rows without substitutions. Primary security comparison S1 uses I1/I2/I3/I5 and E/M/D; I4 rollback observations and I6 normal functionality are reported separately and must not be hidden. S1 is one deterministic threat case per source, not an attack-prevention probability.

Compare V3 separately against V1 and V2, stratified by ID and matched repetitions/steps. Additional observed protection requires normal O1/F1 legitimate checks and rollback preserved, no worsening in security vector on any matched observation, and strict improvement in at least one security invariant/consequence. Equal vectors with required functionality preserved => equal observed protection. Reverse dominance => worse/security regression. Lost previously working permitted operations => functional regression; mixed security gains/losses or improvement plus functionality loss => trade-off. Missing/failed/not-comparable evidence => insufficient evidence. Benefit over BOTH only if both individual comparisons improve; retain ties, regressions and inconclusive rows. Actual nested call being rejected rather than a harmless zero-credit call is not additional protection when defined state/financial outcomes tie.

No contract implementation correction is warranted by current source inspection. If a real implementation problem is discovered, keep original source/output, document a separately reviewed version and do not silently replace one arm. Freeze protocol/input/schema before implementation and freeze runner/extracted fixture before execution. Derive results/comparisons from raw observations; rerun clean, verify byte-reproducible summaries and old hashes. Stop after RE01–RE03.
