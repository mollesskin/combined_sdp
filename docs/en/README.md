# English experiment reports

These are English reading copies of the current result reports. They do not replace the locked source reports, scripts, protocols, registries, or raw evidence under `experiments/`. The saved experimental findings and numbers are unchanged.

The [tested contract catalog](tested_contracts_catalog.md) gives a source-specific description, applied pattern variants, and measured result for all 38 original files with completed behavioral comparisons, including the new SimpleDAO case.

| Study | English report | Original report |
|---|---|---|
| UC01 token-call behavior | [UC01](reports/uc01_behavioral.md) | `experiments/behavioral_pilot_v1/generated_results.md` |
| UC02 and UC03 token-call behavior | [UC02–UC03](reports/uc02_uc03_behavioral.md) | `experiments/behavioral_transferability_v1/generated_results.md` |
| Reentrancy behavior | [Reentrancy](reports/reentrancy_behavioral.md) | `experiments/reentrancy_behavioral_v1/generated_results.md` |
| Arithmetic comparison | [Arithmetic](reports/arithmetic_comparison.md) | `experiments/multifamily_behavioral_v1/arithmetic_comparison_v1/README_RU.md` |
| Access-control comparison | [Access control](reports/access_control_comparison.md) | `experiments/multifamily_behavioral_v1/access_control_comparison_v1/README_RU.md` |
| Denial-of-service comparison | [DoS](reports/dos_comparison.md) | `experiments/multifamily_behavioral_v1/dos_comparison_v1/README_RU.md` |

`render_saved_reports.py` is an English-only report-rendering script for the three behavioral reports. It copies saved table values and translates display text. Run it from any working directory:

```bash
python3 docs/en/render_saved_reports.py
```

The original `tests/report.py` files and `generated_results.md` reports are covered by historical artifact hashes. Editing them in place would break the saved validation chain, so the English script and reports live outside `experiments/`. Historical Russian protocols, run snapshots, source-review documents, and registry entries remain archival evidence rather than current English reports.
