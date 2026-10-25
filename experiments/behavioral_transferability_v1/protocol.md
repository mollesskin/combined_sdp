# Transferability protocol — frozen before coding/comparative runs

See source_applicability.md for qualification and explicit differences from UC01. This is exploratory AI-assisted developmental work with prior UC01/channel results known. Frozen static PES and approved RQ remain unchanged. Only UC02/UC03 enrolled, no substitutions, no Slither/Mythril, no network/forks or real assets.

A=require low-level EVM call success; B=exact returndata length 32 then full word==1 without CALL flag check; V3=A+B. Guarantees and limitations are unchanged from UC01: A cannot detect false application return; B cannot authenticate the return channel or truthful token behavior. Do not use typed high-level calls or omit decoding checks. Only annotated call sites change; V0 remains byte-identical. No unrelated baseline repair.

Same Python environment and ByzantiumVM/genesis/gas settings as UC01: timestamp 2000000000, difficulty 1, block gas limit 30000000, tx gas 12000000, gasPrice 1. solc --combined-json abi,bin without optimizer, 60s compile timeout. UC02 exact0.4.18; UC03 exact0.4.24; fixture compiled using same compiler per candidate. Record versions/hashes/commands/raw warnings/failures. Verify full ABI equality but never infer equivalence from ABI alone.

Fresh deterministic backend per contract/variant/scenario/repetition. account[0] deployer/caller/from/approved token owner, account[1] sole recipient. Synthetic initial owner token balance=10000, recipient=0, airdrop=0; allowance(owner,airdrop)=10000. No ETH funding; initial airdrop ETH=0. UC02 inputs tos=[recipient],vs=[5], a=5. UC03 inputs from=owner,tos=[recipient],v=5,decimals=2,a=500. Record input and deployed addresses. S1 mode0 normal transfer/true, S2 mode1 false/no transfer, S3 mode2 empty revert/no transfer. No robustness additions.

Failure policy remains atomic rejection: when transfer does not deliver, outer operation must revert with balances and allowance preserved, rather than return true. Both baselines explicitly return true after low-level calls; they have no error-recovery/pending-payment mechanism. No per-variant success definition. Setup success is mandatory. Each trial executes a normal probe, saves receipt/state, reverts the snapshot, verifies initial state restored, sets fixed scenario mode and executes the primary operation. Host-side PyEVM child-computation capture only; no added contract instrumentation. Save every actual call status/data and parent output including reverted traces.

## Applicable measurements/invariants

Let t=outer receipt status, a=fixed amount, f0/f1 source tokens, r0/r1 recipient tokens, c0/c1 airdrop tokens, l0/l1 source allowance for airdrop, q0/q1 airdrop ETH wei, d=r1-r0. Applicability:
- I1 acknowledged_delivery: if t=1, require d=a, f0-f1=a, c1=c0, l0-l1=a and actual parent return data canonical boolean true.
- I2 entitlement preservation: N/A, no internal entitlement ledger. E (UC01 consumed-unfulfilled-entitlement wei) is N/A/blank, not zero.
- I3 token conservation: f1+r1+c1=f0+r0+c0, fixed no-fee/no-rebasing fixture.
- I4 atomic_failure_policy (S2/S3 only): t=0, f1=f0,r1=r0,c1=c0,l1=l0.
- I5 ether_frame: q1=q0.
- I6 legitimate_operation (S1 and every separate normal probe): t=1, canonical parent true, d=a, f0-f1=a,c1=c0,l0-l1=a,I3 and I5 pass.
- Negative-scenario security requires all applicable I1,I3,I4,I5. Report numerator/completed denominator, expected denominator=2 per candidate/variant/repetition, infrastructure exclusions. Not attack-prevention probability. Different applicable-invariant counts must not be compared as a protection score to UC01.

D=max(0,a-d) if t=1 else0 token smallest units; D/a exact fraction with positive fixed a, same formula as UC01. Rejected nondelivery D=0 is correct handling, not financial damage. Record raw allowance consumption l0-l1 descriptively; no new combined measure, no conversion to entitlement or wei. Missing evidence yields unknown metrics and inconclusive invariants, never pass/zero.

Two separate clean-process repetitions, each 2 contracts ×4 variants ×3 scenarios =24 primary trials, 48 total; 48 additional normal probes. Exactly 2 source contracts, 8 variant sources (including 2 original V0 copies), not 48 contracts. Prior UC01 remains separate. Fix case/variant/scenario order UC02 then UC03, V0–V3, S1–S3. If setup qualification fails for one candidate, record blocked rows for it and no replacement; other candidate may proceed.

## Matched comparison and stop

Compare V3 vs V1, and V3 vs V2, separately per original contract over matched scenarios/repetitions. Evidence vector is applicable invariant outcomes, D, and legitimate-operation checks; E is omitted as N/A. Additional observed protection requires no regression on any component, strict improvement on at least one, and normal probes/S1 preserved. Equal vectors and normal functionality => equal observed protection. Reverse dominance => security regression. Lost legitimate functionality => functional regression; security gain plus functional loss or mixed security gain/loss => trade-off. Incomplete/failed/mismatched evidence or missing comparability => inconclusive. Benefit over both only if both pairwise classifications are additional protection. Gas is descriptive, fixed budget, not part of protection ranking. No inferred winner, no test changes to favor V3.

Freeze this protocol, applicability memo and inputs with timestamp/hash before implementation; freeze source/fixture/runner before comparative executions. Raw observations precede derived CSV/summary. Recompute summaries from saved outputs and verify clean-run determinism, prior-file preservation and compiler/ABI/source hashes. Stop after UC02/UC03; no new family, contract, scenario or PES calculation.
