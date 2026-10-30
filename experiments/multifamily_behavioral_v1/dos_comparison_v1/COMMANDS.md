# Exact execution commands

Initial preparation from repository root (before checkpoint interruption):

```bash
python3 /tmp/dos_build.py
cp /tmp/dos_build.py experiments/multifamily_behavioral_v1/dos_comparison_v1/build_variants.py
node --check experiments/multifamily_behavioral_v1/dos_comparison_v1/project/measure.js
```

Initial compilation, cwd `experiments/multifamily_behavioral_v1/dos_comparison_v1/project`:

```bash
./node_modules/.bin/hardhat compile > ../compile.log 2>&1
```

After checkpoint recovery, from that same project directory:

```bash
OUTPUT_DIR=../runs/evaluation_1_20261023T052839Z ./node_modules/.bin/hardhat run --no-compile measure.js > ../evaluation_1.log 2>&1
# v1 instrument evidence retained; nested OOG hash correction was versioned before these primary runs:
OUTPUT_DIR=../runs/evaluation_v2_1_20261023T053001Z ./node_modules/.bin/hardhat run --no-compile measure.js > ../evaluation_v2_1.log 2>&1
./node_modules/.bin/hardhat clean > ../repeat_clean.log 2>&1
./node_modules/.bin/hardhat compile > ../repeat_compile.log 2>&1
OUTPUT_DIR=../runs/evaluation_v2_2_20261023T053111Z ./node_modules/.bin/hardhat run --no-compile measure.js > ../evaluation_v2_2.log 2>&1
```

Validation, cwd repository root:

```bash
python3 experiments/multifamily_behavioral_v1/dos_comparison_v1/validate.py > experiments/multifamily_behavioral_v1/dos_comparison_v1/validation.log 2>&1
bash -n experiments/multifamily_behavioral_v1/dos_comparison_v1/reproduce.sh
node --check experiments/multifamily_behavioral_v1/dos_comparison_v1/project/measure.js
```

Environment: node --version, npm --version, local hardhat --version, npm ls --depth=0 --json, python3 --version. Outputs saved in versions.txt/dependencies.json.

For a future repeat use `bash experiments/multifamily_behavioral_v1/dos_comparison_v1/reproduce.sh` from any cwd. The script creates new timestamped paths, clean-compiles twice in the DoS project and validates only those new outputs. Historical fixed-path commands above refuse to overwrite existing measurement directories. Existing installed dependencies are reused; no installs/updates or external-network execution.
