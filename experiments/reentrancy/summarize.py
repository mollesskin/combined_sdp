#!/usr/bin/env python3
"""Derive descriptive metrics solely from an existing completed CSV run."""
import collections,csv,datetime,hashlib,json,pathlib,sys
BASE=pathlib.Path(__file__).resolve().parent

def main():
    run=pathlib.Path(sys.argv[1]).resolve(); rows=list(csv.DictReader((run/'results.csv').open()))
    if len(rows)!=24 or not (run/'summary.json').exists(): raise RuntimeError('Incomplete run')
    for name in ['deviations.json','CHANGELOG.md','README.md','verify.py','summarize.py']:
        if (BASE/name).exists(): (run/name).write_bytes((BASE/name).read_bytes())
    config=BASE/'toolchain/mythril-state/config.ini'
    if config.exists(): (run/'mythril-config.ini').write_bytes(config.read_bytes())
    completed=lambda r: r['execution_status'].startswith('completed')
    with (run/'analysis_failures.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(r for r in rows if not completed(r))
    compilations=[]
    for r in rows:
        if r['tool']!='slither': continue
        folder=run/r['contract_id']/r['variant']/'compile'
        execution=json.loads((folder/'execution.json').read_text())
        status=json.loads((folder/'status.json').read_text())
        compilations.append(dict(contract_id=r['contract_id'],source_contract=r['source_contract'],variant=r['variant'],solidity_version=r['solidity_version'],compilation_status=r['compilation_status'],exit_code=execution['exit_code'],elapsed_seconds=execution['elapsed_seconds'],error=status['error'],raw_output_directory=folder.relative_to(run).as_posix()))
    for name,records in [('compilation_results.csv',compilations),('compilation_failures.csv',[r for r in compilations if r['compilation_status']!='success'])]:
        with (run/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(compilations[0])); writer.writeheader(); writer.writerows(records)
    pairs=[]
    for tool in ['slither','mythril']:
        keyed={(r['contract_id'],r['variant']):r for r in rows if r['tool']==tool}
        for before,after in [('V0','V1'),('V0','V2'),('V0','V3'),('V1','V3'),('V2','V3')]:
            eligible=[(keyed[(c,before)],keyed[(c,after)]) for c in ['R01','R02','R03'] if completed(keyed[(c,before)]) and completed(keyed[(c,after)])]
            pairs.append(dict(tool=tool,before=before,after=after,paired_completed=len(eligible),fewer_reentrancy_findings=sum(int(b['reentrancy_finding_count'])<int(a['reentrancy_finding_count']) for a,b in eligible),same_reentrancy_findings=sum(int(b['reentrancy_finding_count'])==int(a['reentrancy_finding_count']) for a,b in eligible),more_reentrancy_findings=sum(int(b['reentrancy_finding_count'])>int(a['reentrancy_finding_count']) for a,b in eligible)))
    (run/'metrics.json').write_text(json.dumps(pairs,indent=2)+'\n')
    lines=['# Observed pilot results','',f'Source run: `{run.name}`. Generated from raw-backed results.csv; no imputation.','', '| Tool | ID | V0 reentrancy | V1 CEI | V2 mutex | V3 CEI+mutex |','|---|---|---:|---:|---:|---:|']
    for tool in ['slither','mythril']:
        for c in ['R01','R02','R03']:
            rr={r['variant']:r for r in rows if r['tool']==tool and r['contract_id']==c}
            values=[rr[v]['reentrancy_finding_count'] if completed(rr[v]) else 'unknown ('+rr[v]['execution_status']+')' for v in ['V0','V1','V2','V3']]
            lines.append('| '+' | '.join([tool,c]+values)+' |')
    lines+=['','## Paired descriptive comparisons','','| Tool | Comparison | Completed pairs / 3 | Fewer findings | Same | More |','|---|---|---:|---:|---:|---:|']
    for p in pairs: lines.append(f"| {p['tool']} | {p['before']} → {p['after']} | {p['paired_completed']} / 3 | {p['fewer_reentrancy_findings']} | {p['same_reentrancy_findings']} | {p['more_reentrancy_findings']} |")
    comp=collections.Counter(r['compilation_status'] for r in rows if r['tool']=='slither')
    lines+=['', 'Compilation outcomes (one per variant): `'+json.dumps(dict(comp))+'`.', '', 'All missing analyses remain in the CSV. Successful static reports describe detector observations only. These results do not establish exploit prevention, behavioral equivalence, or broad combination superiority. Mythril reports, when valid, are budget-limited. See raw stderr/JSON for failure details.','']
    (run/'RESULTS.md').write_text('\n'.join(lines))
    (run/'derivation.json').write_text(json.dumps(dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=sys.argv,python=sys.version,results_csv_sha256=hashlib.sha256((run/'results.csv').read_bytes()).hexdigest(),summary_script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    with (run/'artifacts.sha256').open('w') as f:
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.name!='artifacts.sha256': f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(run).as_posix()+'\n')
    (BASE/'latest-run.json').write_text(json.dumps(dict(run=run.relative_to(BASE).as_posix(),results_csv=(run/'results.csv').relative_to(BASE).as_posix(),report=(run/'RESULTS.md').relative_to(BASE).as_posix()),indent=2)+'\n')
    print(run/'RESULTS.md')
if __name__=='__main__': main()
