#!/usr/bin/env python3
"""Verify source integrity and recompute reported counts directly from raw JSON."""
import csv,difflib,hashlib,json,pathlib,sys
BASE=pathlib.Path(__file__).resolve().parent
ROOT=BASE.parents[1]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    m=json.loads((BASE/'manifest.json').read_text()); assert len(m['contracts'])==3
    annotated={r['path'] for r in json.loads((ROOT/'vulnerabilities.json').read_text()) if any(v['category']=='reentrancy' for v in r['vulnerabilities'])}
    candidates={p.relative_to(ROOT).as_posix() for p in (ROOT/'dataset/reentrancy').glob('*.sol')}
    assert annotated==candidates=={r['path'] for r in m['inventory']}
    assert len(candidates)==31
    for r in m['contracts']:
        source=ROOT/r['source']; baseline=BASE/r['variants']['baseline']['path']
        assert source.read_bytes()==baseline.read_bytes()
        for name,e in r['variants'].items():
            p=BASE/e['path']; assert sha(p)==e['sha256']
            if name!='baseline':
                expected=''.join(difflib.unified_diff(baseline.read_text().splitlines(True),p.read_text().splitlines(True),fromfile='baseline/'+r['name'],tofile=name+'/'+r['name']))
                assert (BASE/'patches'/name/(r['name']+'.patch')).read_text()==expected
    print('Source integrity: 3 byte-identical baselines, 12 hashes, 9 exact diffs.')
    if len(sys.argv)>1:
        run=pathlib.Path(sys.argv[1]).resolve(); rows=list(csv.DictReader((run/'results.csv').open()))
        assert len(rows)==24
        assert len({(r['contract_id'],r['variant'],r['tool']) for r in rows})==24
        for r in rows:
            folder=run/r['raw_output_directory']
            assert (folder/'execution.json').is_file()
            if r['execution_status'].startswith('completed'):
                path=folder/('report.json' if r['tool']=='slither' else 'stdout.txt'); data=json.loads(path.read_text()); assert data['success'] is True
                findings=data['results']['detectors'] if r['tool']=='slither' else data['issues']
                assert int(r['vulnerability_count'])==len(findings)
                count=sum(str(f.get('check','')).startswith('reentrancy-') if r['tool']=='slither' else str(f.get('swc-id',''))=='107' for f in findings)
                assert int(r['reentrancy_finding_count'])==count
                assert r['vulnerability_detected']==str(bool(findings)).lower()
            else:
                assert r['vulnerability_count']==r['reentrancy_finding_count']==r['vulnerability_detected']==''
        for contract in m['contracts']:
            abis={}
            for variant in ['V0','V1','V2','V3']:
                folder=run/contract['contract_id']/variant/'compile'
                status=json.loads((folder/'status.json').read_text())['compilation_status']
                if status=='success':
                    execution=json.loads((folder/'execution.json').read_text()); assert execution['exit_code']==0
                    data=json.loads((folder/'stdout.txt').read_text())['contracts']
                    assert data and all(c['bin'] for c in data.values())
                    abis[variant]=sorted([json.loads(c['abi']) if isinstance(c['abi'],str) else c['abi'] for c in data.values()],key=str)
            if 'V0' in abis: assert all(abi==abis['V0'] for abi in abis.values())
        if (run/'artifacts.sha256').exists():
            for line in (run/'artifacts.sha256').read_text().splitlines():
                expected,name=line.split('  ',1); assert sha(run/name)==expected
        print('Result integrity: all 24 rows accounted for; counts match raw reports; missing results remain blank.')
        print('Compilation/ABI evidence verified; artifact checksums verified when present.')
if __name__=='__main__': main()
