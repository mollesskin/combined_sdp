# Transferability to UC02 and UC03: results from saved CSV files

Source contracts: 2; source variants: 8; separate clean runs: 2; repetitions per contract: 2; primary trials: 48; separate ordinary probes: 48.

Repetitions check reproducibility; they do not increase the number of independent contracts. UC01 was neither rerun nor pooled with these results.

| Contract | Comparison | Classification | Ordinary functionality preserved |
|---|---|---|---|
| UC02 | V3 vs V1 | additional observed protection | True |
| UC02 | V3 vs V2 | equal observed protection | True |
| UC03 | V3 vs V1 | additional observed protection | True |
| UC03 | V3 vs V2 | equal observed protection | True |

A+B is not claimed to outperform BOTH individual components when either comparison is a tie.

| Contract | Variant | Scenario | Outer status | Delivered | D, token units | D/a | Allowance consumed | Violations |
|---|---|---|---|---:|---:|---|---:|---|
| UC02 | V0 | S1 | success | 5 | 0 | 0 | 5 | [] |
| UC02 | V0 | S2 | success | 0 | 5 | 1 | 0 | ["I1", "I4"] |
| UC02 | V0 | S3 | success | 0 | 5 | 1 | 0 | ["I1", "I4"] |
| UC02 | V1 | S1 | success | 5 | 0 | 0 | 5 | [] |
| UC02 | V1 | S2 | success | 0 | 5 | 1 | 0 | ["I1", "I4"] |
| UC02 | V1 | S3 | revert | 0 | 0 | 0 | 0 | [] |
| UC02 | V2 | S1 | success | 5 | 0 | 0 | 5 | [] |
| UC02 | V2 | S2 | revert | 0 | 0 | 0 | 0 | [] |
| UC02 | V2 | S3 | revert | 0 | 0 | 0 | 0 | [] |
| UC02 | V3 | S1 | success | 5 | 0 | 0 | 5 | [] |
| UC02 | V3 | S2 | revert | 0 | 0 | 0 | 0 | [] |
| UC02 | V3 | S3 | revert | 0 | 0 | 0 | 0 | [] |
| UC03 | V0 | S1 | success | 500 | 0 | 0 | 500 | [] |
| UC03 | V0 | S2 | success | 0 | 500 | 1 | 0 | ["I1", "I4"] |
| UC03 | V0 | S3 | success | 0 | 500 | 1 | 0 | ["I1", "I4"] |
| UC03 | V1 | S1 | success | 500 | 0 | 0 | 500 | [] |
| UC03 | V1 | S2 | success | 0 | 500 | 1 | 0 | ["I1", "I4"] |
| UC03 | V1 | S3 | revert | 0 | 0 | 0 | 0 | [] |
| UC03 | V2 | S1 | success | 500 | 0 | 0 | 500 | [] |
| UC03 | V2 | S2 | revert | 0 | 0 | 0 | 0 | [] |
| UC03 | V2 | S3 | revert | 0 | 0 | 0 | 0 | [] |
| UC03 | V3 | S1 | success | 500 | 0 | 0 | 500 | [] |
| UC03 | V3 | S2 | revert | 0 | 0 | 0 | 0 | [] |
| UC03 | V3 | S3 | revert | 0 | 0 | 0 | 0 | [] |

The table shows one complete run; all compared behavioral fields match in the clean repetition: {"UC02": true, "UC03": true}.

| Contract | Variant | Negative scenarios handled correctly per repetition | Ordinary probes | S1 | Applicable invariant violations per repetition |
|---|---|---|---|---|---:|
| UC02 | V0 | 0/2 (expected 2; excluded 0) | 3/3 | True | 4 |
| UC02 | V1 | 1/2 (expected 2; excluded 0) | 3/3 | True | 2 |
| UC02 | V2 | 2/2 (expected 2; excluded 0) | 3/3 | True | 0 |
| UC02 | V3 | 2/2 (expected 2; excluded 0) | 3/3 | True | 0 |
| UC03 | V0 | 0/2 (expected 2; excluded 0) | 3/3 | True | 4 |
| UC03 | V1 | 1/2 (expected 2; excluded 0) | 3/3 | True | 2 |
| UC03 | V2 | 2/2 (expected 2; excluded 0) | 3/3 | True | 0 |
| UC03 | V3 | 2/2 (expected 2; excluded 0) | 3/3 | True | 0 |

I1 means acknowledged success without the required delivery/accounting; I4 means failure to reject atomically. I2 and the erased Holders credit measure do not apply here and are not set to zero. D does not establish financial loss. Measures are neither added into a scale nor converted into PES.

Evidence validation: PASS; prior files verified unchanged: 1550; frozen UC01 files additionally checked: 291; primary traces cross-checked: 48.

Limitations: one recipient per batch, honest synthetic tokens, only S1–S3, bounded amounts without arithmetic overflow, and no tests of other defects or functions. Different compiler pins, operation sizes, and accounting applicability require separate presentation of the contracts; they cannot be pooled with UC01 as identical repetitions.
