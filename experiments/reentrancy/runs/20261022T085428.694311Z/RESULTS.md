# Observed pilot results

Source run: `20261022T085428.694311Z`. Generated from raw-backed results.csv; no imputation.

| Tool | ID | V0 reentrancy | V1 CEI | V2 mutex | V3 CEI+mutex |
|---|---|---:|---:|---:|---:|
| slither | R01 | 1 | 0 | 1 | 0 |
| slither | R02 | 1 | 0 | 1 | 0 |
| slither | R03 | 1 | 0 | 1 | 0 |
| mythril | R01 | unknown (analysis_error) | unknown (analysis_error) | unknown (analysis_error) | unknown (analysis_error) |
| mythril | R02 | 2 | 1 | 4 | 3 |
| mythril | R03 | 2 | 1 | 4 | 3 |

## Paired descriptive comparisons

| Tool | Comparison | Completed pairs / 3 | Fewer findings | Same | More |
|---|---|---:|---:|---:|---:|
| slither | V0 → V1 | 3 / 3 | 3 | 0 | 0 |
| slither | V0 → V2 | 3 / 3 | 0 | 3 | 0 |
| slither | V0 → V3 | 3 / 3 | 3 | 0 | 0 |
| slither | V1 → V3 | 3 / 3 | 0 | 3 | 0 |
| slither | V2 → V3 | 3 / 3 | 3 | 0 | 0 |
| mythril | V0 → V1 | 2 / 3 | 2 | 0 | 0 |
| mythril | V0 → V2 | 2 / 3 | 0 | 0 | 2 |
| mythril | V0 → V3 | 2 / 3 | 0 | 0 | 2 |
| mythril | V1 → V3 | 2 / 3 | 0 | 0 | 2 |
| mythril | V2 → V3 | 2 / 3 | 2 | 0 | 0 |

Compilation outcomes (one per variant): `{"success": 12}`.

All missing analyses remain in the CSV. Successful static reports describe detector observations only. These results do not establish exploit prevention, behavioral equivalence, or broad combination superiority. Mythril reports, when valid, are budget-limited. See raw stderr/JSON for failure details.
