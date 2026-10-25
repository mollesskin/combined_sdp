# RE01–RE03: behavioral results from saved outputs

Source contracts: 3; existing source variants: 12; clean process runs: 2; repetitions per contract: 2; scenario trials: 72; withdrawal steps: 120.

The two repetitions check reproducibility; they are not independent contracts. The CEI, mutex, and combined source files were unchanged. UC01–UC03 remain closed exploratory behavioral pilots and were not rerun.

| Contract | Comparison | Result | Ordinary and permitted functionality preserved |
|---|---|---|---|
| RE01 | V3 vs V1 | equal observed protection | True |
| RE01 | V3 vs V2 | equal observed protection | True |
| RE02 | V3 vs V1 | equal observed protection | True |
| RE02 | V3 vs V2 | equal observed protection | True |
| RE03 | V3 vs V1 | equal observed protection | True |
| RE03 | V3 vs V2 | equal observed protection | True |

| Contract | Variant | Payout with one reentry, wei | Excess payout E, wei | Credit mismatch M, wei | Unbacked recorded claims D, wei | Security violations |
|---|---|---:|---:|---:|---:|---|
| RE01 | V0 | 2000000000000000000 | 1000000000000000000 | 115792089237316195423570985008687907853269984665640564039457584007913129639936 | 115792089237316195423570985008687907853269984665640564039457584007913129639936 | ["I1", "I2", "I5"] |
| RE01 | V1 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE01 | V2 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE01 | V3 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE02 | V0 | 2000000000000000000 | 1000000000000000000 | 1000000000000000000 | 1000000000000000000 | ["I1", "I2", "I5"] |
| RE02 | V1 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE02 | V2 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE02 | V3 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE03 | V0 | 2000000000000000000 | 1000000000000000000 | 1000000000000000000 | 1000000000000000000 | ["I1", "I2", "I5"] |
| RE03 | V1 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE03 | V2 | 1000000000000000000 | 0 | 0 | 0 | [] |
| RE03 | V3 | 1000000000000000000 | 0 | 0 | 0 | [] |

The table shows the first run; all compared behavioral fields match in the repetition: {"RE01": true, "RE02": true, "RE03": true}.

| Contract | Variant | Ordinary permitted withdrawals per repetition | Rejection rollback | S1 security properties |
|---|---|---|---|---|
| RE01 | V0 | 3/3 | True | 0/1 |
| RE01 | V1 | 3/3 | True | 1/1 |
| RE01 | V2 | 3/3 | True | 1/1 |
| RE01 | V3 | 3/3 | True | 1/1 |
| RE02 | V0 | 3/3 | True | 0/1 |
| RE02 | V1 | 3/3 | True | 1/1 |
| RE02 | V2 | 3/3 | True | 1/1 |
| RE02 | V3 | 3/3 | True | 1/1 |
| RE03 | V0 | 3/3 | True | 0/1 |
| RE03 | V1 | 3/3 | True | 1/1 |
| RE03 | V2 | 3/3 | True | 1/1 |
| RE03 | V3 | 3/3 | True | 1/1 |

I1 checks excess payout; I2 checks consistency between payout and accounting; I3 checks conservation of financial flow; I5 checks whether assets back remaining recorded claims. I4 checks rollback and I6 checks permitted operations. These checks are not independent vulnerabilities and are not summed into a protection score.

In the RE01 baseline, repeated subtraction wraps the uint256 credit. The huge M/D values reflect actual machine-state corruption, not a plausible monetary valuation; raw credit and measured excess payout are retained separately. In RE02, the aggregate can match actual ETH while differing from the sum of remaining credits; both are recorded. In RE02/RE03, a successful nested call under CEI yields no extra payout and is not rated below mutex rejection when the properties tie.

Evidence validation: PASS; previous files unchanged: 2049; actual traces cross-checked: 120; static-tool runs: 0; new PES values: 0.

Limitations: one previously known bounded reentry attempt, three sources, fixed amounts and gas budget, one local recipient, known prior results, and closed-storage reads through an explicit schema. The study does not prove full functional equivalence, protection against all forms of reentrancy, or real-world prevention probability. Other functions, cross-function reentry, depth/gas boundaries, and live networks were not tested.
