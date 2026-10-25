# Commands executed / reproduction

All commands are local. Working directory for Hardhat commands:
`experiments/multifamily_behavioral_v1/access_control_comparison_v1/project`.

Initial source generation from repository root:

```bash
python3 /tmp/ac_build.py
# Generator subsequently saved/corrected as build_variants.py; final source regeneration:
python3 experiments/multifamily_behavioral_v1/access_control_comparison_v1/build_variants.py
node --check experiments/multifamily_behavioral_v1/access_control_comparison_v1/project/measure.js
```

Compilation and preliminary instrument execution, from project:

```bash
./node_modules/.bin/hardhat compile > ../compile.log 2>&1
OUTPUT_DIR=../runs/initial_01 ./node_modules/.bin/hardhat run --no-compile measure.js > ../initial_01.log 2>&1
```

Final two runs after the documented oracle type correction, from project:

```bash
OUTPUT_DIR=../runs/run1 ./node_modules/.bin/hardhat run --no-compile measure.js > ../run1.log 2>&1
./node_modules/.bin/hardhat clean > ../run2_clean.log 2>&1
./node_modules/.bin/hardhat compile > ../run2_compile.log 2>&1
OUTPUT_DIR=../runs/run2 ./node_modules/.bin/hardhat run --no-compile measure.js > ../run2.log 2>&1
```

Validation and fresh-path reproduction script test, from repository root:

```bash
python3 experiments/multifamily_behavioral_v1/access_control_comparison_v1/analyze.py > experiments/multifamily_behavioral_v1/access_control_comparison_v1/validation.log 2>&1
bash experiments/multifamily_behavioral_v1/access_control_comparison_v1/reproduce.sh > experiments/multifamily_behavioral_v1/access_control_comparison_v1/reproduction_check.log 2>&1
```

For a new reproduction use `reproduce.sh` directly; it creates fresh paths and stops on command failure. The fixed historical commands refuse to overwrite existing output directories. Environment recorded with `node --version`, `npm --version`, `hardhat --version`, `npm ls --depth=0 --json`, `python3 --version`. No installs, dependency upgrades, public-network execution or arithmetic reruns were performed.
