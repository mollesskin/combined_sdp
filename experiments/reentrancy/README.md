# Reentrancy security-pattern pilot

Research question: “How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?”

This reproducible **static-analysis pilot** measures detector observations for three source contracts and four treatments. It does not itself measure exploit prevention. All work uses local Solidity files; no chain interaction is part of the experiment.

## Source and fixed selection

Source: [SmartBugs Curated](https://github.com/smartbugs/smartbugs-curated), commit `230e649123477eff332742a59a1c7cc6dc286cab`. `dataset_structure.json` records 143 Solidity files in ten directories; `dataset/reentrancy/` contains 31. The manifest includes original source attribution and vulnerability annotations from `vulnerabilities.json`. Files retain original licenses; see the repository LICENSE and source headers.

The earlier chat stated the pilot criteria before initial variant generation; the v1 protocol file was saved after that generation. This timing deviation is disclosed in deviations.json. The expanded protocol v2 saved explicit criteria before this extension changed preparation metadata and before any compilation/security analysis. Existing Solidity variants were retained unchanged. Protocol v3 corrects explicit Mythril compiler pinning; its change is saved before the final batch. The fixed sample was inherited unchanged from that pilot. No sample member was selected, replaced or discarded because of analyzer results.

Inclusion: annotated reentrancy, standalone without imports/inheritance, at most 60 physical lines, Solidity 0.4.x, payable funding, ETH withdrawal that updates accounting after interaction, reverting send-failure path, and a locally reviewable transformation. The final restriction is the previously frozen three-file whitelist. This is a purposive sample with no population representativeness claim. `selection.csv` lists all 31 candidates and inclusion/exclusion reasons. Compilation failure does not remove a case.

| ID | Source | Exact solc |
|---|---|---|
| R01 | etherstore.sol | 0.4.10 |
| R02 | reentrancy_dao.sol | 0.4.19 |
| R03 | reentrancy_simple.sol | 0.4.15 |

Achieved dataset size: **3 baselines, 12 total Solidity files**, with nine experimental variants and exact diffs. See run summaries for achieved compilation/analysis coverage.

## Treatments

| Variant | Directory | Patterns |
|---|---|---|
| V0 | contracts/baseline | Original, byte-for-byte |
| V1 | contracts/cei | Checks-Effects-Interactions |
| V2 | contracts/guard | Private mutex and nonReentrant modifier |
| V3 | contracts/cei_guard | CEI + mutex |

See CHANGELOG.md and patches/ for every source change. Guard is legacy-compatible custom Solidity, not an OpenZeppelin import. Function signatures and funding logic are retained. Gas usage, private storage, callback-visible accounting and nested withdrawals intentionally differ. ABI comparison checks interfaces only; dynamic regression and exploit tests have not been performed. Original vulnerability-line comments apply to baselines and are not new variant labels.

## Directory structure

```text
experiments/reentrancy/
├── README.md, protocol.md, CHANGELOG.md
├── prepare.py, run.py, verify.py, summarize.py, setup_compilers.py
├── manifest.json, selection.csv, dataset_structure.json, settings.json
├── environment.lock.json, deviations.json, latest-run.json
├── requirements.lock.txt, requirements-mythril.lock.txt
├── contracts/{baseline,cei,guard,cei_guard}/*.sol
├── patches/{cei,guard,cei_guard}/*.patch
├── toolchain/                     # ignored: virtualenvs, compilers, local caches
├── setup/                         # raw installation, probe and download evidence
└── runs/<UTC-run-ID>/
    ├── environment.json, manifest.json, settings.json
    ├── protocol.md, selection.csv, prepare.py, run.py, setup_compilers.py
    ├── events.jsonl, results.csv, summary.json
    ├── compilation_results.csv, compilation_failures.csv, analysis_failures.csv
    ├── RESULTS.md, metrics.json, artifacts.sha256
    ├── preflight/                 # raw version/package probes
    └── R01|R02|R03/V0|V1|V2|V3/
        ├── compile/{stdout.txt,stderr.txt,execution.json,status.json}
        ├── slither/{stdout.txt,stderr.txt,execution.json,report.json}
        └── mythril/{stdout.txt,stderr.txt,execution.json}
```

Actual launch failures retain empty stdout and the OS error in stderr. Skipped analyses have execution.json with a reason and no command; they are not represented as executions. `report.json` exists only if Slither created it. Original v1 preflight-only runs remain in runs/ and do not contain experimental results.

## Conditions and provenance

`settings.json` is authoritative. Same native compiler within each source's four variants, taken from versions.csv; no pragma normalization and no optimization. Compilation: `solc-VERSION --combined-json abi,bin SOURCE`, 60-second wall limit. Slither runs its full default detector set with that exact compiler, 180-second wall limit. Mythril, when its preflight succeeds, uses explicit `--solv VERSION` and hash-checked local compiler registrations (also recorded as `SOLC`), offline `--no-onchain-data`, 3 transactions, 120-second execution budget, 10000 ms solver timeout, 180-second wall limit. No detector tuning based on sample findings.

Runs are sequential on the same host, using `PYTHONHASHSEED=0`, `TZ=UTC` and isolated virtualenvs. CPU/memory are not capped; elapsed time is descriptive and not a cross-host performance benchmark. Slither and Mythril do not share dependencies. Cache locations are scoped inside toolchain. Only dependency/compiler setup requires network access. Mythril offline mode disables on-chain data loading.

Environment locking records actual platform, interpreter and package versions, compiler and launcher hashes, package-tree hashes, and input hashes. A changed environment or input blocks analysis. Raw probes and every process command, relevant environment, cwd, UTC start/end, timeout, duration and exit code are saved. This is a local environment lock, not a portable container image; a new host/path requires a separate lock, retained alongside the published original. Re-created package binary builds can differ even with pinned versions; the lock exposes that difference.

## Exact reproduction commands

From repository root, after obtaining this experiment directory:

```sh
python3 experiments/reentrancy/prepare.py
python3 experiments/reentrancy/verify.py
python3.13 -m venv experiments/reentrancy/toolchain/venv
experiments/reentrancy/toolchain/venv/bin/python -m pip install -r experiments/reentrancy/requirements.lock.txt
experiments/reentrancy/toolchain/venv/bin/python experiments/reentrancy/setup_compilers.py
python3.12 -m venv experiments/reentrancy/toolchain/mythril-venv
experiments/reentrancy/toolchain/mythril-venv/bin/python -m pip install -r experiments/reentrancy/requirements-mythril.lock.txt
```

Compiler setup downloads the official platform archive, verifies its upstream SHA-256, and records each attempt. Native x86 macOS compiler execution requires host support; Linux uses the official linux-amd64 archive. Other platforms are not validated. On this host Python binaries are `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` and `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`.

To repeat in the original, unchanged local environment:

```sh
python3 experiments/reentrancy/run.py
```

To reproduce on a different checkout/host, retain the published lock and create a separate observed lock (exclusive creation; do not overwrite locks):

```sh
python3 experiments/reentrancy/run.py --lock --lock-file experiments/reentrancy/reproduction.lock.json
python3 experiments/reentrancy/run.py --lock-file experiments/reentrancy/reproduction.lock.json
```

Compare the new lock's versions/settings/compiler identities against environment.lock.json and disclose platform/build deviations. The lock command performs preflight only; the second command performs the experiment. If Mythril cannot start, every Mythril row is explicitly skipped while Slither proceeds. Every invocation creates a new UTC directory and preserves prior evidence. For a produced run, substitute its printed directory:

```sh
python3 experiments/reentrancy/summarize.py experiments/reentrancy/runs/UTC-RUN-ID
python3 experiments/reentrancy/verify.py experiments/reentrancy/runs/UTC-RUN-ID
```

## Results and metrics

`results.csv` has 24 rows: 3 sources × 4 variants × 2 tools. Columns include IDs, source, V0–V3, patterns, compiler version, compilation status, tool, detection boolean, total findings, reentrancy findings, execution/error/timeout statuses, exit code, duration, raw-output directory and source hash. Compiler results are independently recorded once per variant. Blank detection/count cells mean unknown, failed or skipped; zero is reserved for an actual valid report with no corresponding findings.

For Slither, vulnerability_count counts all results.detectors entries, including informational/optimization notices. It is a historical column name required by the requested schema, not a count of confirmed exploitable defects. Reentrancy count includes detector IDs starting `reentrancy-`. A nonzero Slither exit may indicate findings, so JSON success and structure determine usable reports. For Mythril, issues entries are findings and SWC-107 is reentrancy; all valid reports are budget-limited. Internal budget exhaustion may yield partial reports; no completeness claim is made.

Use paired source/tool comparisons V0→V1, V0→V2, V0→V3 and V1/V2→V3, only when both reports completed successfully. Report numerator and denominator and all missing cases. The sample is too small and narrow for general effectiveness claims. Static warnings disappearing cannot establish safety or the superiority of combinations; behavioral exploit tests would be needed to answer prevention directly.

Primary tool references: [Slither usage](https://github.com/crytic/slither/wiki/Usage) and [Mythril CLI](https://github.com/ConsenSysDiligence/mythril/blob/develop/mythril/interfaces/cli.py). Exact installed CLI help/source and actual commands take precedence over changing online documentation.

The completed v2 batch is retained as diagnostic evidence. Use the v3 batch identified in `latest-run.json` for the final results; batches are repeated observations of the same sample and must not be pooled as extra contracts. `RESULTS.md`, `metrics.json`, and `artifacts.sha256` are derived from each completed run by summarize.py. Static-analysis counts can vary with bounded solver search and host scheduling even with the same configured budgets. See protocol.md for the compiler-pinning deviation.

`compilation_results.csv` has one row per Solidity file; `compilation_failures.csv` contains failed cases only (header-only when none fail). `analysis_failures.csv` retains failed or skipped tool rows. Setup history is indexed in setup/history.json; timestamps that were not captured during early setup are explicitly left unspecified.

No explicit EVM target flag is set: each locked compiler uses its own default for every variant of that source. The final report bundle also preserves Mythril config.ini; `--no-onchain-data` is passed in every Mythril analysis regardless of its default dynamic-loading setting. Function-signature caches are local and may be populated during sequential runs.

## Final executed coverage

Final batch: [`20261022T085428.694311Z`](runs/20261022T085428.694311Z/RESULTS.md). Standalone compilation: 12/12 successful; all nine ABI comparisons matched. Slither 0.11.6: 12/12 completed. Mythril 0.24.8: 8/12 valid budget-limited reports and 4/12 analysis errors from py-solc-x rejecting solc 0.4.10. No selected case was removed. See [results.csv](runs/20261022T085428.694311Z/results.csv) and [observed paired results](runs/20261022T085428.694311Z/RESULTS.md).

Protocol.md is a chronological record: v1 environment-status statements are historical; v3 and settings.json govern the final batch. Deviations and the diagnostic v2 batch remain available.
