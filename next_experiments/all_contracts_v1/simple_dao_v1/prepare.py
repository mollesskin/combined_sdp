#!/usr/bin/env python3
"""Build exact SimpleDAO treatments and compile all fixtures offline."""

import difflib
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "dataset/reentrancy/simple_dao.sol"
SOLC = ROOT / "experiments/multi_vulnerability/design_v1/toolchain/solc-0.4.2"
EXPECTED_SOURCE_SHA256 = "40ffea56c722280688eba923676992d20be7623dcf724393c1c7ca1ef24e0ae5"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one replacement site, got {source.count(old)}: {old!r}")
    return source.replace(old, new, 1)


def compile_file(path):
    relative_path = path.relative_to(ROOT)
    result = subprocess.run(
        [str(SOLC), "--combined-json", "abi,bin", str(relative_path)],
        cwd=ROOT,
        capture_output=True, text=True, timeout=60, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Compilation failed for {path}: {result.stderr}")
    return result, json.loads(result.stdout)


def main():
    original_bytes = SOURCE.read_bytes()
    if sha256(original_bytes) != EXPECTED_SOURCE_SHA256:
        raise ValueError("Benchmark source hash changed")
    original = original_bytes.decode("utf-8")
    cei = replace_once(
        original,
        "      bool res = msg.sender.call.value(amount)();\n      credit[msg.sender]-=amount;",
        "      credit[msg.sender]-=amount;\n      bool res = msg.sender.call.value(amount)();",
    )
    guard_prefix = (
        "contract SimpleDAO {\n"
        "  bool private entered;\n"
        "  modifier nonReentrant() {\n"
        "    if (entered) throw;\n"
        "    entered = true;\n"
        "    _;\n"
        "    entered = false;\n"
        "  }\n"
    )

    def add_guard(source):
        source = replace_once(source, "contract SimpleDAO {\n", guard_prefix)
        return replace_once(source, "  function withdraw(uint amount) {", "  function withdraw(uint amount) nonReentrant {")

    variants = {"V0": original, "V1": cei, "V2": add_guard(original), "V3": add_guard(cei)}
    out = HERE / "variants"
    out.mkdir(exist_ok=True)
    artifacts = HERE / "artifacts"
    artifacts.mkdir(exist_ok=True)
    report = {"source_path": str(SOURCE.relative_to(ROOT)),
              "source_sha256": EXPECTED_SOURCE_SHA256,
              "solc_path": str(SOLC.relative_to(ROOT)),
              "solc_version": subprocess.check_output([str(SOLC), "--version"], text=True).strip(),
              "variants": {}}
    for name, source in variants.items():
        path = out / f"{name}.sol"
        path.write_bytes(original_bytes if name == "V0" else source.encode("utf-8"))
        diff = "".join(difflib.unified_diff(original.splitlines(True), source.splitlines(True),
                                            fromfile="V0.sol", tofile=f"{name}.sol"))
        (out / f"{name}.patch").write_text(diff)
        result, data = compile_file(path)
        (artifacts / f"{name}.compile.stdout.json").write_text(result.stdout.rstrip() + "\n")
        (artifacts / f"{name}.compile.stderr.txt").write_text(result.stderr)
        if len(data["contracts"]) != 1:
            raise ValueError(f"Unexpected contracts in {name}: {data['contracts'].keys()}")
        contract = next(iter(data["contracts"].values()))
        (artifacts / f"{name}.json").write_text(json.dumps({"abi": json.loads(contract["abi"]),
                                                             "bytecode": "0x" + contract["bin"]}, indent=2) + "\n")
        report["variants"][name] = {"sha256": sha256(path.read_bytes()),
                                     "compile_exit_code": result.returncode,
                                     "bytecode_bytes": len(contract["bin"]) // 2}
    attacker_result, attacker_data = compile_file(HERE / "attacker.sol")
    (artifacts / "attacker.compile.stdout.json").write_text(attacker_result.stdout.rstrip() + "\n")
    (artifacts / "attacker.compile.stderr.txt").write_text(attacker_result.stderr)
    for key, contract in attacker_data["contracts"].items():
        name = key.rsplit(":", 1)[-1]
        (artifacts / f"{name}.json").write_text(json.dumps({"abi": json.loads(contract["abi"]),
                                                              "bytecode": "0x" + contract["bin"]}, indent=2) + "\n")
    report["attacker_sha256"] = sha256((HERE / "attacker.sol").read_bytes())
    (HERE / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"source_sha256": report["source_sha256"],
                      "variant_count": len(variants),
                      "compiled_variants": list(variants),
                      "fixture_contracts": list(attacker_data["contracts"])}))


if __name__ == "__main__":
    main()
