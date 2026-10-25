# Results generated from saved CSV files

One UC01 source contract was tested in two repetitions with fresh local state. Repetitions are not independent contracts.

| Variant | Scenario | Outer transaction status | CALL succeeded | Tokens delivered | Shortfall D, token units | Credit erased on shortfall E, wei | Violations |
|---|---|---|---|---:|---:|---:|---|
| V0 | S1 | success | True | 5 | 0 | 0 | [] |
| V0 | S2 | success | True | 0 | 5 | 2000000000000000000 | ["I1", "I2", "I4"] |
| V0 | S3 | success | False | 0 | 5 | 2000000000000000000 | ["I1", "I2", "I4"] |
| V1 | S1 | success | True | 5 | 0 | 0 | [] |
| V1 | S2 | success | True | 0 | 5 | 2000000000000000000 | ["I1", "I2", "I4"] |
| V1 | S3 | revert | False | 0 | 0 | 0 | [] |
| V2 | S1 | success | True | 5 | 0 | 0 | [] |
| V2 | S2 | revert | True | 0 | 0 | 0 | [] |
| V2 | S3 | revert | False | 0 | 0 | 0 | [] |
| V3 | S1 | success | True | 5 | 0 | 0 | [] |
| V3 | S2 | revert | True | 0 | 0 | 0 | [] |
| V3 | S3 | revert | False | 0 | 0 | 0 | [] |

| Variant | Negative scenarios handled correctly per repetition | Ordinary-operation probes | Invariant violations in primary trials |
|---|---|---|---:|
| V0 | 0/2 | 3/3; S1=True | 6 |
| V1 | 1/2 | 3/3; S1=True | 3 |
| V2 | 2/2 | 3/3; S1=True | 0 |
| V3 | 2/2 | 3/3; S1=True | 0 |

Comparisons under the previously fixed rules:
- V3 vs V1: additional observed protection
- V3 vs V2: equal observed protection

Additional benefit of the combination over BOTH individual components: False.
Behavioral metrics match across the clean repetitions: True.

I1/I2/I4 record an acknowledged transaction without the promised delivery, erased Holders credit without delivery, and failure to reject atomically. These are correlated checks, not three independent vulnerabilities. D/5 is normalized shortfall; E is measured separately without adding token units to wei. A correctly handled revert has D=0 and E=0. This operation does not transfer the bank's ETH. The observations do not establish safety beyond the three scenarios and are not converted into PES.
