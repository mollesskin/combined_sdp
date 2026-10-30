#!/usr/bin/env bash
# AI-assisted. Reproduces only DoS, with fresh output paths and unchanged installed dependencies.
set -euo pipefail
stage_dir="$(cd "$(dirname "$0")" && pwd)"
run_root="$stage_dir/runs/reproduction_$(date -u +%Y%m%dT%H%M%SZ)_$$"
mkdir "$run_root"
cd "$stage_dir/project"
node --check measure.js > "$run_root/syntax.log" 2>&1
for run_name in run1 run2; do
 ./node_modules/.bin/hardhat clean > "$run_root/${run_name}_clean.log" 2>&1
 ./node_modules/.bin/hardhat compile > "$run_root/${run_name}_compile.log" 2>&1
 OUTPUT_DIR="$run_root/$run_name" ./node_modules/.bin/hardhat run --no-compile measure.js > "$run_root/${run_name}.log" 2>&1
done
python3 "$stage_dir/validate.py" --run1 "$run_root/run1" --run2 "$run_root/run2" --output "$run_root/analysis" > "$run_root/validation.log" 2>&1
python3 "$stage_dir/export_tables.py" --run "$run_root/run1" --output "$run_root/analysis" > "$run_root/export.log" 2>&1
printf '%s\n' "$run_root"
