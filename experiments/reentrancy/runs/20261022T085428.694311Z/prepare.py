#!/usr/bin/env python3
"""Build a frozen, manually reviewed pilot; never modify dataset/."""
import csv, difflib, hashlib, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()

def generate():
    versions = {r['file']: r['compiled version'] for r in csv.DictReader((ROOT/'versions.csv').open())}
    annotations = {r['path']: r for r in json.loads((ROOT/'vulnerabilities.json').read_text())}
    # Exact reviewed transformations; fail on upstream source drift.
    edits = {
        'etherstore.sol': ('        require(msg.sender.call.value(_weiToWithdraw)());\n        balances[msg.sender] -= _weiToWithdraw;\n        lastWithdrawTime[msg.sender] = now;', '        balances[msg.sender] -= _weiToWithdraw;\n        lastWithdrawTime[msg.sender] = now;\n        require(msg.sender.call.value(_weiToWithdraw)());', 'function withdrawFunds (uint256 _weiToWithdraw) public'),
        'reentrancy_dao.sol': ('            bool callResult = msg.sender.call.value(oCredit)();\n            require (callResult);\n            credit[msg.sender] = 0;', '            credit[msg.sender] = 0;\n            bool callResult = msg.sender.call.value(oCredit)();\n            require (callResult);', 'function withdrawAll() public'),
        'reentrancy_simple.sol': ('         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){\n             throw;\n         }\n         userBalance[msg.sender] = 0;', '         uint amount = userBalance[msg.sender];\n         userBalance[msg.sender] = 0;\n         if( ! (msg.sender.call.value(amount)() ) ){\n             throw;\n         }', 'function withdrawBalance()'),
    }
    exclusions = {
        'etherbank.sol': 'No explicit payable funding function (legacy implicit payable not normalized).',
        'modifier_reentrancy.sol': 'Token/modifier callback scenario; no payable ETH funding/withdrawal path.',
        'reentrance.sol': 'External call failure is ignored instead of reverting.',
        'reentrancy_bonus.sol': 'Bonus/cross-function scenario; no payable funding path.',
        'reentrancy_cross_function.sol': 'No payable funding path; cross-function scenario.',
        'reentrancy_insecure.sol': 'Solidity 0.5.x and no payable funding path.',
        'simple_dao.sol': 'External call failure is ignored instead of reverting.',
    }
    inventory = []
    for p in sorted((ROOT/'dataset/reentrancy').glob('*.sol')):
        source = p.read_bytes(); rel = p.relative_to(ROOT).as_posix()
        inventory.append(dict(path=rel, lines=len(source.splitlines()), sha256=sha(source), selected=p.name in edits,
                              reason='Included: meets criteria and frozen v1 whitelist.' if p.name in edits else
                              ('Excluded: exceeds 60 physical lines.' if len(source.splitlines())>60 else exclusions[p.name])))
    manifest = dict(schema=2, dataset_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    selection='protocol.md', inventory=inventory, contracts=[])
    for name, (old,new,signature) in sorted(edits.items()):
        p = ROOT/'dataset/reentrancy'/name; raw=p.read_bytes(); text=raw.decode()
        assert text.count(old)==1 and text.count(signature)==1
        assert len(raw.splitlines())<=60 and 'import ' not in text
        cei=text.replace(old,new)
        def guard(s):
            pos=s.index('{',s.index('contract '))+1
            s=s[:pos]+ '\n    // Experiment guard: Solidity 0.4-compatible, shared contract lock.\n    bool private experimentEntered;\n    modifier nonReentrant() {\n        require(!experimentEntered);\n        experimentEntered = true;\n        _;\n        experimentEntered = false;\n    }\n' + s[pos:]
            return s.replace(signature,signature+' nonReentrant')
        rel=p.relative_to(ROOT).as_posix()
        assert any(v['category']=='reentrancy' for v in annotations[rel]['vulnerabilities'])
        record=dict(contract_id=f'R{len(manifest["contracts"])+1:02d}', name=name, source=rel, source_sha256=sha(raw), solc=versions[rel], annotation=annotations[rel], variants={})
        for variant, data in [('baseline',raw),('cei',cei.encode()),('guard',guard(text).encode()),('cei_guard',guard(cei).encode())]:
            dest=OUT/'contracts'/variant/name; dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and dest.read_bytes()!=data: raise RuntimeError(f'Refusing to overwrite changed file: {dest}')
            dest.write_bytes(data)
            index=['baseline','cei','guard','cei_guard'].index(variant)
            record['variants'][variant]=dict(variant=f'V{index}', patterns=['none','CEI','mutex','CEI+mutex'][index],path=dest.relative_to(OUT).as_posix(),sha256=sha(data))
            if variant!='baseline':
                patch=OUT/'patches'/variant/(name+'.patch'); patch.parent.mkdir(parents=True,exist_ok=True)
                patch.write_text(''.join(difflib.unified_diff(text.splitlines(True),data.decode().splitlines(True),fromfile='baseline/'+name,tofile=variant+'/'+name)))
        manifest['contracts'].append(record)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    counts={p.name:len(list(p.glob('*.sol'))) for p in sorted((ROOT/'dataset').iterdir()) if p.is_dir()}
    (OUT/'dataset_structure.json').write_text(json.dumps(counts,indent=2)+'\n')
    with (OUT/'selection.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(inventory[0])); writer.writeheader(); writer.writerows(inventory)
if __name__=='__main__': generate()
