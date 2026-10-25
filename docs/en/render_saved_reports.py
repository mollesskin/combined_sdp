#!/usr/bin/env python3
"""Render English reading copies of locked behavioral reports.

Saved table values and experimental artifacts remain unchanged. The bilingual
line map is translation data, separate from the English-only program logic.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUTS = {
    "behavioral_pilot_v1": "uc01_behavioral.md",
    "behavioral_transferability_v1": "uc02_uc03_behavioral.md",
    "reentrancy_behavioral_v1": "reentrancy_behavioral.md",
}


def main() -> None:
    translations = json.loads((HERE / "report_line_translations.json").read_text())
    output_dir = HERE / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    for stage, output_name in OUTPUTS.items():
        source = ROOT / "experiments" / stage / "generated_results.md"
        lines = [translations[stage].get(line, line) for line in source.read_text().splitlines()]
        translated = "\n".join(lines) + "\n"
        if re.search(r"[\u0400-\u04ff]", translated):
            raise ValueError(f"Untranslated Cyrillic in {stage}")
        (output_dir / output_name).write_text(translated)


if __name__ == "__main__":
    main()
