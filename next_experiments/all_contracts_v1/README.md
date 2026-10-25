# All-contract expansion: qualification stage

This new stage inventories all 143 original Solidity files in SmartBugs Curated. It is deliberately outside the historical `experiments/` tree so the frozen `final_evidence_v1` preservation audit remains valid. No previous source, protocol, result, or hash is changed.

Current state: all **143** unchanged V0 files compile with their pinned local compiler; **23** full comparisons are historical; **one new source** (`simple_dao.sol`) has a complete local V0–V3 behavioral comparison, making **24** completed full comparisons in total. Historical full comparisons are not automatically accepted as independent pairs under this stricter rule. `pair_qualification.csv` gives one status and reason per source: **32 N/A** for the current strict pair design, **9 historical pair audits pending**, **101 source-specific reviews pending**, and **1 newly completed pair**. These categories describe qualification work, not 143 protection tests. N/A is revisable if a genuinely independent, comparable second defense is designed.

The comparison unit is an original benchmark file, not a generated variant or repeated run. For each case that qualifies, the intended arms are V0 (byte-identical original), V1 (A only), V2 (B only), and V3 (A+B). A and B must be independently implemented and measurable; neither may secretly include the other, and all four arms must preserve a declared ordinary workflow. For a claim that the combination is *better* than either component, the protocol must also expose distinct failure conditions or another measured benefit. The same local scenario inputs and compiler pin must be used within a case. V3 is compared with V1 and V2 separately. Compilation or a missing warning is not a protection outcome.

The existing 23 full comparisons are referenced rather than rerun or counted twice. They still need a pair-independence audit before entering any new strict two-pattern denominator: some historical arithmetic checks intentionally overlap. The remaining 120 files require source-specific review before assigning A/B. Existing single-fix and alternative-workflow cases are not relabelled as full comparisons. If two valid treatments cannot be defined for a case, its status must remain `not_applicable` or `unqualified`, with the reason recorded. No placeholder V2/V3 source or fabricated result should be generated.

`build_inventory.py` cross-checks all source paths against `versions.csv` and `vulnerabilities.json`, records source hashes and annotated lines, links previous evaluation types from the redacted `prior_case_registry_public.csv`, and checks availability of pinned local compilers. Its outputs are `inventory.csv` and `inventory_summary.json`. The public prior-case registry contains only case identity, source hash, evaluation type, and pattern names; original historical run files are not part of this publication subset.

Run from any directory:

```bash
python3 next_experiments/all_contracts_v1/build_inventory.py
```

`qualify_baselines.py` performs the next gate: offline compilation of unchanged sources with their pinned local compilers. It writes per-source stdout/stderr and commands under `compile_raw/`, status rows in `baseline_compilation.csv`, and `baseline_compilation_summary.json`. Compiler binaries and raw compile files are kept locally, outside Git; the CSV is the published status record. On macOS, `download_pinned_compilers.py` restores every version from the official Solidity archive and verifies each published SHA-256. `solc 0.4.21` was fetched and verified for this run; `toolchain/solc-0.4.21.provenance.json` records its source and digest. No substitute compiler version was used. Run the baseline check after building the inventory and restoring compilers:

```bash
python3 next_experiments/all_contracts_v1/qualify_baselines.py
```

Then record conservative pair statuses:

```bash
python3 next_experiments/all_contracts_v1/screen_pairs.py
```

The new `simple_dao_v1/` case has its own frozen [protocol](simple_dao_v1/PROTOCOL.md), exact variant diffs, compiler outputs, two behavioral run records, and [case summary](simple_dao_v1/summary.json). Reproduce its local run with:

```bash
python3 next_experiments/all_contracts_v1/simple_dao_v1/prepare.py
cd next_experiments/all_contracts_v1/simple_dao_v1/project
SIMPLE_DAO_RUN_ID=r1 ./node_modules/.bin/hardhat run --no-compile scripts/run.js
SIMPLE_DAO_RUN_ID=r2 ./node_modules/.bin/hardhat run --no-compile scripts/run.js
cd -
python3 next_experiments/all_contracts_v1/simple_dao_v1/summarize.py
python3 next_experiments/all_contracts_v1/build_inventory.py
python3 next_experiments/all_contracts_v1/screen_pairs.py
```

The local project uses an existing Hardhat dependency tree through a `node_modules` link that is not committed. In a fresh checkout, run `npm install` inside `simple_dao_v1/project/` before the Hardhat commands. The local scenario shows V3 blocks the measured repeated withdrawal, but does **not** outperform either single pattern on that scenario. All four variants still debit credit on a failed ether send, which is a separate limitation.

Baseline compilation does not establish two-pattern comparability. Treatment generation and behavioral experiments require a case-level policy, local fixture, ordinary workflow and negative scenarios, a frozen oracle, exact V0-relative diffs, and a compiler/ABI check. Static detector scores remain separate from behavioral measurements.
