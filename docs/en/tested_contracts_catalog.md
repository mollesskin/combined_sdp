# Tested contract descriptions

This catalog describes **38 original SmartBugs Curated source files** for which a defense variant was executed and compared with the original contract. A source file is counted once, even when a contract has multiple functions, scenarios, repetitions, or generated variants. The 37 historical cases are recorded in `experiments/final_evidence_v1/master_case_registry.csv`; `simple_dao.sol` is the one new case. All 143 benchmark originals passed a separate compiler preflight, but compilation alone does not place a file in this catalog.

**Variant notation.** V0 is the original benchmark. A/V1 and B/V2 apply the named changes separately; V3 combines them. F1 is a single repair. The auction compares two alternative refund workflows and has no V3. Each historical completed comparison has two saved primary clean runs. The new SimpleDAO case has two independent local runs. Statements below refer to those specific fixtures and tested behavior, not to universal contract security.

**Evidence and publication scope.** The local historical `master_results.csv`, `single_fix_results.csv`, and `alternative_workflows.csv` contain exact scenario outcomes; the new case has its own [summary](../../next_experiments/all_contracts_v1/simple_dao_v1/summary.json). The current GitHub publication carries English reading copies and a [redacted prior-case registry](../../next_experiments/all_contracts_v1/prior_case_registry_public.csv), while the historical raw runs remain local. This catalog does not add new measurements. Some historical A/B arithmetic arms enforce the same no-wrap rule, so their V3 result is a tested combination of edits rather than evidence of two independent defenses.

## Access control — 14 files

### 1. [`arbitrary_location_write_simple.sol`](../../dataset/access_control/arbitrary_location_write_simple.sol) — full V0–V3

`Wallet` stores bonus codes in a dynamic array. `PopBonusCode()` checks `0 <= bonusCodes.length`, which is always true for an unsigned length, then decrements the length; calling it on an empty array can underflow the length and expose unintended storage locations. A checks that the array is nonempty **before** decrementing; B checks the length subtraction result; V3 includes both. In the recorded oracle, V0 passed 2/5 security observations, whereas A, B, and V3 each passed 5/5 while preserving 4/4 allowed observations. The two checks exclude the same empty-array underflow, so V3 added no measured benefit.

### 2. [`incorrect_constructor_name1.sol`](../../dataset/access_control/incorrect_constructor_name1.sol) — single repair

The `Missing` contract exposes `IamMissing()` as a public function because its name does not match the contract name. A later caller can invoke this intended initializer and gain the authority it assigns. F1 makes initialization a real constructor and removes the runtime entry point. Security observations changed from 0/4 in V0 to 4/4 in F1; allowed observations changed from 2/4 to 4/4. No second independent pattern was tested.

### 3. [`incorrect_constructor_name2.sol`](../../dataset/access_control/incorrect_constructor_name2.sol) — single repair

Here the public intended initializer is named `missing()` with the wrong capitalization for contract `Missing`. It is callable after deployment and can reassign control. F1 replaces it with a constructor. Security observations changed from 0/4 to 4/4 and allowed observations from 2/4 to 4/4. This is a separate benchmark file, not another repetition of case 2.

### 4. [`incorrect_constructor_name3.sol`](../../dataset/access_control/incorrect_constructor_name3.sol) — single repair

`Constructor()` is an ordinary public function in contract `Missing`, not a Solidity constructor. The experiment tests post-deployment invocation and repeated invocation of that exposed initializer. F1 uses constructor syntax so initialization occurs during deployment only. Security observations changed from 0/4 to 4/4 and allowed observations from 2/4 to 4/4; there is no V2 or V3.

### 5. [`mapping_write.sol`](../../dataset/access_control/mapping_write.sol) — single repair

`Map.set(key, value)` expands a dynamic array to `key + 1` and then writes at `map[key]`. A caller-chosen large index can manipulate array length/storage in the vulnerable design. F1 replaces the dynamic array with a mapping and removes length manipulation. The recorded security observation changed from 0/1 to 1/1; allowed observations changed from 3/5 to 5/5. The absent-key `get` behavior extends to zero instead of a possible out-of-bounds revert, so this is a documented behavior change.

### 6. [`multiowned_vulnerable.sol`](../../dataset/access_control/multiowned_vulnerable.sol) — single repair

`MultiOwnable.newOwner()` can add an owner without the `onlyOwner` modifier already used by other privileged operations. This can create unauthorized access to the inherited withdrawal function. F1 applies the existing owner guard to `newOwner`; it does not introduce a new grant workflow. Security observations changed from 1/3 to 3/3, with allowed observations remaining 10/10.

### 7. [`mycontract.sol`](../../dataset/access_control/mycontract.sol) — single repair

`MyContract.sendTo()` authorizes a transfer using `tx.origin`. That condition can remain true through an intermediate contract call, so it does not authenticate the immediate caller. F1 uses `msg.sender` for the owner check. Security observations changed from 1/2 to 2/2; the tested allowed transfer remained 1/1.

### 8. [`parity_wallet_bug_2.sol`](../../dataset/access_control/parity_wallet_bug_2.sol) — single repair

This wallet has multi-owner and daily-limit initialization entry points. An `only_uninitialized` check prevents a second initialization but does not establish who may perform the first one, allowing unauthorized first initialization. F1 applies one deployment-authority rule to the three initialization entry points while retaining the existing single-use guard. Security observations changed from 2/6 to 6/6; allowed observations remained 7/7. The experiment does not claim to repair every feature of this large wallet.

### 9. [`phishable.sol`](../../dataset/access_control/phishable.sol) — single repair

`Phishable.withdrawAll()` uses `tx.origin == owner`, so a contract that the owner interacts with can initiate a withdrawal to a supplied recipient. F1 checks `msg.sender == owner` and leaves the payable fallback and recipient argument in place. Security observations changed from 1/2 to 2/2; the tested legitimate withdrawal remained 1/1.

### 10. [`simple_suicide.sol`](../../dataset/access_control/simple_suicide.sol) — single repair

`SimpleSuicide.sudicideAnyone()` calls `selfdestruct(msg.sender)` without an authority check. F1 assigns an owner at deployment and guards this function. The tested unauthorized-destruction observation changed from 0/1 to 1/1, while the authorized operation remained 1/1. The deployment-owner policy is an explicit experimental choice because the source does not define one.

### 11. [`unprotected0.sol`](../../dataset/access_control/unprotected0.sol) — single repair

`Unprotected.changeOwner()` exposes an ownership change without using the contract's existing `onlyowner` restriction. F1 applies that modifier to the exposed function. Security observations changed from 0/2 to 2/2, and allowed observations remained 2/2. No acceptance phase or additional owner policy was introduced.

### 12. [`wallet_02_refund_nosub.sol`](../../dataset/access_control/wallet_02_refund_nosub.sol) — single repair

`Wallet.refund()` transfers the recorded balance without clearing the caller's credit. F1 sets the credit to zero before the transfer, using the accounting order of Checks–Effects–Interactions. The saved oracle reports 2/2 security observations for both V0 and F1, but allowed observations improved from 6/10 to 10/10 under the tested refund and repeat-call workflows. This record should not be presented as a measured security-observation gain.

### 13. [`wallet_03_wrong_constructor.sol`](../../dataset/access_control/wallet_03_wrong_constructor.sol) — single repair

`Wallet.initWallet()` assigns `creator` but remains publicly callable after deployment instead of serving as a constructor. F1 moves this assignment into construction and removes the runtime initializer. Security observations changed from 0/4 to 4/4, and allowed observations from 3/5 to 5/5. The lifecycle/API change is part of the documented repair.

### 14. [`wallet_04_confused_sign.sol`](../../dataset/access_control/wallet_04_confused_sign.sol) — full V0–V3

`Wallet.withdraw(amount)` incorrectly requires `amount >= balances[msg.sender]`, permitting over-withdrawal while rejecting some ordinary partial withdrawals. A corrects the entitlement comparison to `amount <= balance`; B checks the debit but retains the reversed comparison; V3 includes both. V0 passed 1/3 security and 8/10 allowed observations. A and V3 passed 3/3 security and 10/10 allowed; B passed 3/3 security but only 8/10 allowed. V3 tied A rather than outperforming it.

## Arithmetic — 13 files

For every arithmetic case in this section, A adds a checked-arithmetic helper at the frozen target operations, B adds exact operand/range preconditions at those same targets, and V3 applies both. Every tested unsafe arithmetic scenario was rejected by A, B, and V3, while all tested allowed scenarios remained correct. **These two edits overlap on the no-wrap invariant**; the 13 full comparisons are valid historical measurements but do not establish a benefit from combining independent protections.

### 15. [`BECToken.sol`](../../dataset/arithmetic/BECToken.sol) — full V0–V3

This token supports batch transfers. The target multiplication `recipientCount * value` can wrap before the balance check, allowing an incorrect total amount. The benchmark already contains a SafeMath library, but the raw multiplication does not use it. V0 rejected 0/1 unsafe test; A, B, and V3 rejected 1/1, and all four arms passed 3/3 allowed operations. V3 equaled both single checks.

### 16. [`integer_overflow_1.sol`](../../dataset/arithmetic/integer_overflow_1.sol) — full V0–V3

`Overflow.add(value)` increases a private seller balance without checking whether the sum fits in `uint`. V0 rejected 0/1 unsafe addition; A, B, and V3 rejected 1/1, with 3/3 allowed operations in each arm. The experiment reads the stored balance to measure wrapping and leaves the unrelated boolean return behavior unchanged.

### 17. [`integer_overflow_add.sol`](../../dataset/arithmetic/integer_overflow_add.sol) — full V0–V3

`IntegerOverflowAdd.run(input)` adds a user-provided value to public `count`. A large value can wrap the counter. V0 rejected 0/1 unsafe addition; all three protected arms rejected 1/1 and preserved 3/3 allowed operations. This example is structurally close to `overflow_simple_add.sol` and should not be treated as an independent population sample.

### 18. [`integer_overflow_mapping_sym_1.sol`](../../dataset/arithmetic/integer_overflow_mapping_sym_1.sol) — full V0–V3

`init(k, v)` subtracts `v` from `map[k]`; a fresh key starts at zero, so a positive `v` underflows despite the filename containing “overflow.” V0 rejected 0/1 unsafe operation; A, B, and V3 rejected 1/1, and each arm preserved the one tested allowed operation. The description follows the actual subtraction target rather than the filename.

### 19. [`integer_overflow_minimal.sol`](../../dataset/arithmetic/integer_overflow_minimal.sol) — full V0–V3

`run(input)` subtracts from public `count` without checking that the input is affordable. V0 rejected 0/1 unsafe subtraction; each protected arm rejected 1/1 and retained 2/2 allowed operations, including the declared boundary behavior. V3 added no measured protection beyond either single arm.

### 20. [`integer_overflow_mul.sol`](../../dataset/arithmetic/integer_overflow_mul.sol) — full V0–V3

`run(input)` multiplies a stored counter without an overflow check. V0 rejected 0/1 unsafe multiplication; A, B, and V3 rejected 1/1 while preserving 2/2 allowed operations. The range-precondition arm handles a zero multiplier explicitly, avoiding division by zero in the guard.

### 21. [`integer_overflow_multitx_multifunc_feasible.sol`](../../dataset/arithmetic/integer_overflow_multitx_multifunc_feasible.sol) — full V0–V3

The contract has separate `init()` and `run(input)` calls. `run` returns early before initialization, then later subtracts `input` from `count` without a bounds check. The fixture preserves this transaction order and early return. V0 rejected 0/1 unsafe sequence; A, B, and V3 rejected 1/1 and kept 6/6 allowed sequence observations.

### 22. [`integer_overflow_multitx_onefunc_feasible.sol`](../../dataset/arithmetic/integer_overflow_multitx_onefunc_feasible.sol) — full V0–V3

The first `run(input)` call only marks the contract initialized; a subsequent call performs an unchecked subtraction from `count`. The experiment distinguishes those two calls. V0 rejected 0/1 unsafe sequence; A, B, and V3 rejected 1/1, with 4/4 allowed observations preserved in all arms.

### 23. [`overflow_simple_add.sol`](../../dataset/arithmetic/overflow_simple_add.sol) — full V0–V3

`Overflow_Add.add(deposit)` adds to public `balance` without checking for wraparound. V0 rejected 0/1 unsafe input; the three protected variants rejected 1/1, with 3/3 allowed operations retained. It is a near-duplicate of `integer_overflow_add.sol` after normalizing names and compiler pragma.

### 24. [`overflow_single_tx.sol`](../../dataset/arithmetic/overflow_single_tx.sol) — full V0–V3

This benchmark offers addition, multiplication, and subtraction to persistent `count`, plus three local-result-only arithmetic functions. The measured state-changing targets can wrap in V0. V0 rejected 0/3 unsafe state-changing tests; A, B, and V3 rejected 3/3 and preserved 4/4 allowed operations. The three local-only functions are annotated in the source but are not claimed as covered behavioral targets.

### 25. [`timelock.sol`](../../dataset/arithmetic/timelock.sol) — full V0–V3

Deposits set a withdrawal lock. `increaseLockTime(seconds)` adds an unchecked increment, allowing the lock timestamp to wrap to an earlier value. V0 rejected 0/1 unsafe test; A, B, and V3 rejected 1/1 and preserved 4/4 allowed operations. The treatment target is the lock extension, not every arithmetic operation in the contract.

### 26. [`token.sol`](../../dataset/arithmetic/token.sol) — full V0–V3

`Token.transfer()` subtracts from the sender and adds to the recipient. Its unsigned `balances[sender] - value >= 0` condition does not prevent underflow, and balance updates can wrap. V0 rejected 0/2 unsafe tests; A, B, and V3 rejected 2/2, while all arms preserved 4/4 allowed transfers. The target set includes the precondition and debit arithmetic.

### 27. [`tokensalechallenge.sol`](../../dataset/arithmetic/tokensalechallenge.sol) — full V0–V3

`TokenSaleChallenge` buys and sells tokens using `numTokens * PRICE_PER_TOKEN` and updates per-user token balances. An unchecked multiplication or balance update can break payment/accounting relationships. V0 rejected 0/1 unsafe sequence; A, B, and V3 rejected 1/1, with 4/4 allowed buy/sell observations maintained. Both arms were applied to the same declared buy/sell target set.

## Denial of service — 4 files

### 28. [`auction.sol`](../../dataset/denial_of_service/auction.sol) — alternative workflows

`DosAuction.bid()` sends the old bid back to the current leader and requires that send to succeed. A leader whose fallback rejects ether can therefore stop a higher bid. The PULL alternative records a refund debt to be claimed later; the FALLBACK alternative tries the immediate refund and records debt only on failure. Both allowed the tested higher bid despite a refusing previous leader and preserved eventual refund entitlement. They are alternative workflows sharing deferred credit, so **no independent A+B/V3 arm was tested**.

### 29. [`dos_address.sol`](../../dataset/denial_of_service/dos_address.sol) — full V0–V3

`DosGas` appends creditor addresses and later attempts to clear a grown array in one transaction; large cleanup can run out of gas. A clears at most 350 records per step while retaining progress. B caps accepted records at 1,750; V3 combines the cap with incremental cleanup. At 5,950 requested records, V0 accepted 5,950 but completed 0, A completed all 5,950, whereas B and V3 accepted/completed 1,750 and rejected 4,200. V3 was worse than A on requested-work completion, despite performing less total work.

### 30. [`dos_number.sol`](../../dataset/denial_of_service/dos_number.sol) — full V0–V3

`DosNumber` inserts numbers into a growing array and has a bulk `clearDOS()` path. The experiment targets work that becomes impractical when the array is large. A adds incremental cleanup with progress; B limits capacity to 1,750 records; V3 applies both. Under the 5,950-record request, V0 completed 0, A completed 5,950, and B/V3 completed only the 1,750 they accepted while rejecting 4,200. The cap makes V3 worse than A on full requested capacity.

### 31. [`dos_simple.sol`](../../dataset/denial_of_service/dos_simple.sol) — single repair

`DosOneFunc.ifillArray()` appends 350 addresses while the list is below 1,500, then resets the list on a later call. F1 changes cleanup into bounded incremental steps. V0 and F1 both completed the tested 1,750-record request and retained correct refill behavior; F1 used five cleanup calls instead of one. The source already bounds growth, so adding a duplicate capacity pattern was not justified.

## Reentrancy — 4 files

For these comparisons, A uses Checks–Effects–Interactions (record the withdrawal effect before the external call), B uses a contract-local withdrawal mutex, and V3 applies both. The two edits act at different points, but the measured bounded callback may be stopped by either one. The results do not show V3 outperforming both single defenses.

### 32. [`etherstore.sol`](../../dataset/reentrancy/etherstore.sol) — exploratory full V0–V3

`EtherStore.withdrawFunds()` sends ether before reducing the caller's balance and recording the last withdrawal time. A recipient contract can reenter during that call. In the saved bounded scenario V0 overpaid by 1 ether; A, B, and V3 had zero excess payout, zero measured accounting mismatch, and 3/3 allowed observations. The weekly withdrawal rule remained part of the ordinary workflow.

### 33. [`reentrancy_dao.sol`](../../dataset/reentrancy/reentrancy_dao.sol) — exploratory full V0–V3

`ReentrancyDAO.withdrawAll()` sends the user's credit before setting that credit to zero, despite updating a separate aggregate balance earlier. A callback can observe the still-positive per-user credit. V0 overpaid by 1 ether in the saved scenario; A, B, and V3 recorded zero excess payout and zero accounting mismatch with 3/3 allowed observations. V3 tied the single defenses on this fixture.

### 34. [`reentrancy_simple.sol`](../../dataset/reentrancy/reentrancy_simple.sol) — exploratory full V0–V3

`Reentrance.withdrawBalance()` calls the recipient while `userBalance[msg.sender]` is still positive and only clears it afterwards. A recipient contract can invoke the withdrawal again before the first call finishes. V0 overpaid by 1 ether in the bounded test; A, B, and V3 recorded zero excess payout/mismatch and preserved 3/3 allowed observations. This benchmark is the original source behind the editor-open `cei_guard` variant.

### 35. [`simple_dao.sol`](../../dataset/reentrancy/simple_dao.sol) — new full V0–V3

`SimpleDAO` accepts donations as per-address credit. `withdraw(amount)` performs a low-level ether call before subtracting the caller's credit. In two independent local runs, a one-level callback received 2 ether against 1 ether credit in V0; A, B, and V3 each paid only 1 ether, left attacker credit zero, and preserved the ordinary donation/withdrawal scenario. The combination did not outperform either single defense on this fixture. All four arms still debit credit after a failed send, a separate limitation shown by the rejected-recipient scenario. [New case protocol and evidence](../../next_experiments/all_contracts_v1/simple_dao_v1/PROTOCOL.md).

## Unchecked low-level calls — 3 files

These three exploratory ERC-20 cases compare different meanings of call success. A requires the EVM `CALL` success flag. B independently requires a 32-byte return word equal to true, representing token-level success. V3 requires both. The saved fixtures use synthetic token behaviors that return true, return false, or revert without a return value. This is behavioral evidence for the declared token-call workflow, not a general claim about every low-level call.

### 36. [`0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol`](../../dataset/unchecked_low_level_calls/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol) — exploratory full V0–V3

`TokenBank` uses a low-level `transfer(address,uint256)` call without inspecting its result when sending tokens. The fixture checks both a token that returns false and a token that reverts. V0 handled 0/2 negative scenarios; A handled the revert but not false return (1/2); B and V3 handled both (2/2). V3 matched B, so the combination did not exceed the stronger individual check on these cases.

### 37. [`0xa1fceeff3acc57d257b917e30c4df661401d6431.sol`](../../dataset/unchecked_low_level_calls/0xa1fceeff3acc57d257b917e30c4df661401d6431.sol) — exploratory full V0–V3

`AirDropContract.transfer()` loops over recipients and makes a low-level token transfer call for each without testing success. The saved false-return and revert cases can leave token delivery short while the outer workflow continues. V0 handled 0/2 negative scenarios, A 1/2, and B/V3 2/2. A alone cannot distinguish an EVM-successful token call that reports application failure.

### 38. [`0xe894d54dca59cb53fe9cbc5155093605c7068220.sol`](../../dataset/unchecked_low_level_calls/0xe894d54dca59cb53fe9cbc5155093605c7068220.sol) — exploratory full V0–V3

`airDrop.transfer()` computes a token amount and loops over recipients using an unchecked low-level token call. Under the saved negative scenarios, V0 handled 0/2, A 1/2, and B/V3 2/2; the false-return fixture represented a 500-unit delivery shortfall for V0 and A. V3 matched the stronger application-result check B rather than improving on it.

## What the comparisons support

Among the 23 historical full V0–V3 cases, V3 was better than both single arms in 0, equal to the best in 21, and worse in 2 (the two capacity-limited DoS cases). The new SimpleDAO comparison is also equal to its best single arm on the measured scenario, giving a descriptive **0/24 better, 22/24 equal, 2/24 worse** count across historical and new full comparisons. This combined count does not change the frozen historical tables and is not a statistical estimate. Under the newer strict pair-independence screen, 14 historical full pairings are marked N/A for the current design, nine await audit, and the new SimpleDAO pair is completed; the 0/24 figure must not be read as 24 qualified independent pairs. Thirteen single-repair files and the auction alternatives are excluded from the combination denominator.
