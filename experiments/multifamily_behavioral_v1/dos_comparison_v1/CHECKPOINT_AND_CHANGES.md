# Checkpoint recovery and instrument history

The resumed task inspected the existing files rather than recreating the project. At recovery, the protocol, case registry and measure.js matched frozen_before_first_run/hashes.json. Compilation had completed (14 Solidity files); no DoS execution directories or validated outcomes existed. Prepared source variants were not described as executed results. No older vulnerability stage was run.

The saved design was retained: 2 factorial cases (address/number), single-fix simple (its capacity restriction already existed), and alternative refund workflows for auction. The existing loads 1750/5950, cap1750, chunk350, 12m per tx, 20 cleanup steps, aggregate budgets and Shanghai/block30m settings were not retuned.

First execution: `runs/evaluation_1_20261023T052839Z`, instrument v1. It completed the planned calls, but labelled four mined out-of-gas errors infrastructure_error because Hardhat returned transactionHash under error.data.transactionHash. Receipt gas was unavailable to that runner. All its raw outputs, log, original instrument and protocol remain saved. It is development/instrument evidence, not one of the two validated primary runs. A new run was necessary because the in-process networks had already reset between scenarios and ended; the old nested hashes alone could not retrieve receipts from those ended ephemeral networks.

Instrument v2 adds nested-hash recovery before querying actual receipt status. It does not classify OOG from text alone. Unknown oversize completion is null rather than false. No contract source, workload, requirement or comparison budget changed. Versions are under instrument_versions and protocol_versions. The four calls were then confirmed as mined reverts, each using12m gas with observed rollback.

Validated primary runs:

- `runs/evaluation_v2_1_20261023T053001Z` — unchanged compiled variants, corrected instrument.
- `runs/evaluation_v2_2_20261023T053111Z` — new process, clean/recompile, all scenarios reset, new output directory.

Each has338 measured transactions,34 variant-scenario operation records, plus8 submitted mining-diagnostic transactions and2 intentionally rejected admission probes. No evaluation output directory was overwritten. The primary observations, outcomes and raw status histories matched. See repeat_comparison.json for the explicit comparison and paths; future differences are retained, not overwritten or forced to match.

The saved reproduce.sh uses these already executed local commands with fresh directories. bash syntax and JS syntax were checked. It was not run for an unnecessary third/fourth primary evaluation after the completed clean pair.

This stage is AI-assisted engineering/research implementation, not an assignment submission or independent formal audit.
