# Historical experiment publication scope

The `experiments/` directory contains the original historical protocols, source variants, run records, consolidation tables, and validation artifacts. These files were committed without rewriting their content or timestamps in the working tree. The local `experiments/final_evidence_v1/validate_consolidation.py` check passed all 324 checks before publication.

The repository's `.gitignore` excludes downloaded Solidity compilers, Python virtual environments, `node_modules`, caches, and editor state. Those local dependencies were present during the original validation but are not part of the GitHub commit. Therefore a fresh GitHub checkout is **not** a byte-for-byte copy of the original full workstation environment, and the preservation validator may fail until the missing dependencies are restored. The published raw measurement and report files remain available for inspection.

Many historical logs record absolute filesystem paths from the original workstation. They are provenance strings and are not portable commands. Use the relative paths in the repository to locate the same files; do not assume that an absolute path in a saved log exists on another machine.

The follow-up stage under `next_experiments/all_contracts_v1/` remains separate from the frozen historical artifacts. Its `compile_raw/` files and compiler binaries are local generated inputs/outputs; its public CSV and JSON summaries state what was measured. The [T3 overview](T3_original_study.md) and [tested-contract catalog](tested_contracts_catalog.md) describe the scope and results without replacing the raw records.
