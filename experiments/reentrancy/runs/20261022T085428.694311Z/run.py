#!/usr/bin/env python3
"""Run the frozen pilot locally; preserve raw evidence and explicit missing results."""
import argparse, collections, csv, datetime, hashlib, json, os, pathlib, platform
import signal, subprocess, sys, time
BASE=pathlib.Path(__file__).resolve().parent
ROOT=BASE.parents[1]
FIELDS=['contract_id','source_contract','variant','security_patterns','solidity_version','compilation_status','tool','vulnerability_detected','vulnerability_count','reentrancy_finding_count','execution_status','error_timeout_status','exit_code','elapsed_seconds','raw_output_directory','source_sha256']

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,data): p.write_text(json.dumps(data,indent=2)+'\n')
def load(p): return json.loads(p.read_text())
def toolenv(venv):
    inherited={k:os.environ[k] for k in ['PATH','TMPDIR','LANG','LC_ALL','SYSTEMROOT'] if k in os.environ}
    return {**inherited,'VIRTUAL_ENV':str(venv),'PATH':str(venv/'bin')+os.pathsep+os.environ.get('PATH',''),'PYTHONHASHSEED':'0','TZ':'UTC','NO_COLOR':'1','MYTHRIL_DIR':str(BASE/'toolchain/mythril-state'),'SOLCX_BINARY_PATH':str(BASE/'toolchain/solcx'),'MPLCONFIGDIR':str(BASE/'toolchain/matplotlib')}

def execute(cmd,folder,timeout,env,event):
    folder.mkdir(parents=True,exist_ok=True)
    rec=dict(command=cmd,cwd=str(folder),started_utc=utc(),timeout_seconds=timeout,environment=env)
    event('command_start',**rec)
    start=time.monotonic(); code=None; status='exited'; error=''
    with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
        try:
            p=subprocess.Popen(cmd,cwd=folder,stdout=out,stderr=err,env=env,start_new_session=True)
            try: code=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL); p.wait(); status='timeout'; error='wall_timeout'
        except OSError as e:
            status='launch_error'; error=str(e); err.write(str(e)+'\n')
    rec.update(ended_utc=utc(),elapsed_seconds=round(time.monotonic()-start,6),exit_code=code,status=status,error=error)
    save(folder/'execution.json',rec); event('command_end',**rec)
    return rec

def treehash(folder):
    h=hashlib.sha256()
    for p in sorted(folder.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            h.update(str(p.relative_to(folder)).encode()); h.update(p.read_bytes())
    return h.hexdigest()

def probe(run,event,manifest):
    observed=dict(platform=platform.platform(),machine=platform.machine(),python=sys.version,tools={},compilers={},inputs={})
    for name,venv,exe in [('slither',BASE/'toolchain/venv','slither'),('mythril',BASE/'toolchain/mythril-venv','myth')]:
        binary=venv/'bin'/exe; python=venv/'bin/python'
        rec=execute([str(binary),'--version' if name=='slither' else 'version'],run/'preflight'/name,90,toolenv(venv),event)
        entry=dict(available=rec['status']=='exited' and rec['exit_code']==0,version=(run/'preflight'/name/'stdout.txt').read_text().strip(),path=str(binary))
        if binary.is_file(): entry['executable_sha256']=sha(binary)
        if python.is_file():
            inventory=execute([str(python),'-m','pip','freeze','--all'],run/'preflight'/(name+'-packages'),30,toolenv(venv),event)
            entry['packages']=(run/'preflight'/(name+'-packages')/'stdout.txt').read_text()
            entry['package_inventory_status']=inventory['status']
            libs=list((venv/'lib').glob('python*/site-packages'))
            entry['site_packages_sha256']=treehash(libs[0]) if libs else None
            entry['python_sha256']=sha(python.resolve())
        observed['tools'][name]=entry
    for version in sorted({r['solc'] for r in manifest['contracts']}):
        binary=BASE/'toolchain'/('solc-'+version)
        registry=BASE/'toolchain/solcx'/('solc-v'+version)
        if binary.is_file():
            if not registry.exists(): registry.symlink_to(pathlib.Path('..')/binary.name)
            if sha(registry)!=sha(binary): raise RuntimeError('Registered compiler hash mismatch: '+version)
        rec=execute([str(binary),'--version'],run/'preflight'/('solc-'+version),30,toolenv(BASE/'toolchain/venv'),event)
        text=(run/'preflight'/('solc-'+version)/'stdout.txt').read_text()
        observed['compilers'][version]=dict(path=str(binary),sha256=sha(binary) if binary.is_file() else None,registered_sha256=sha(registry) if registry.is_file() else None,version=text.strip(),available=rec['status']=='exited' and rec['exit_code']==0 and ('Version: '+version+'+') in text)
    for name in ['settings.json','manifest.json','protocol.md','prepare.py','run.py','setup_compilers.py']:
        observed['inputs'][name]=sha(BASE/name)
    return observed

def parse_slither(folder,rec):
    if rec['status']!='exited': return None,rec['status'],rec['error']
    try: data=load(folder/'report.json')
    except (ValueError,OSError): return None,'invalid_report','missing_or_malformed_json'
    if data.get('success') is not True: return None,'analysis_error',str(data.get('error','tool_report_failure'))
    # Slither may exit nonzero when findings are present; successful JSON is authoritative.
    findings=data.get('results',{}).get('detectors')
    if not isinstance(findings,list): return None,'invalid_report','missing_detectors_list'
    return (len(findings),sum(str(f.get('check','')).startswith('reentrancy-') for f in findings)),'completed',''

def parse_mythril(folder,rec):
    if rec['status']!='exited': return None,rec['status'],rec['error']
    try: data=load(folder/'stdout.txt')
    except (ValueError,OSError): return None,'invalid_report','missing_or_malformed_json'
    if data.get('success') is not True or not isinstance(data.get('issues'),list): return None,'analysis_error',str(data.get('error','tool_report_failure'))
    findings=data['issues']
    return (len(findings),sum(str(f.get('swc-id',''))=='107' for f in findings)),'completed_budget_limited','internal_timeout_not_distinguishable_from_exhaustion'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--lock',action='store_true'); ap.add_argument('--lock-file',type=pathlib.Path,default=BASE/'environment.lock.json'); args=ap.parse_args()
    for name in ['solcx','mythril-state']: (BASE/'toolchain'/name).mkdir(parents=True,exist_ok=True)
    manifest=load(BASE/'manifest.json'); settings=load(BASE/'settings.json')
    run=BASE/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'); run.mkdir(parents=True)
    def event(kind,**details):
        with (run/'events.jsonl').open('a') as f: f.write(json.dumps(dict(timestamp_utc=utc(),event=kind,**details))+'\n')
    event('run_start',command=sys.argv,protocol_version=settings['protocol_version'])
    for name in ['manifest.json','settings.json','protocol.md','prepare.py','run.py','setup_compilers.py','selection.csv']:
        (run/name).write_bytes((BASE/name).read_bytes())
    for row in manifest['contracts']:
        if sha(ROOT/row['source'])!=row['source_sha256']: raise RuntimeError('Dataset drift: '+row['source'])
        for entry in row['variants'].values():
            if sha(BASE/entry['path'])!=entry['sha256']: raise RuntimeError('Variant drift: '+entry['path'])
    observed=probe(run,event,manifest); save(run/'environment.json',observed)
    lock=args.lock_file
    if args.lock:
        with lock.open('x') as f: json.dump(observed,f,indent=2); f.write('\n')
        (BASE/'requirements.lock.txt').write_text(observed['tools']['slither'].get('packages','# Slither environment unavailable\n'))
        (BASE/'requirements-mythril.lock.txt').write_text(observed['tools']['mythril'].get('packages','# Mythril environment unavailable\n'))
        event('environment_locked',path=str(lock)); print(run); return 0
    if not lock.exists() or load(lock)!=observed:
        event('blocked_environment_drift',lock_exists=lock.exists()); save(run/'summary.json',dict(status='blocked_environment_drift')); print(run); return 2
    results=[]; abi={}
    def flush():
        with (run/'results.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(results)
    for row in manifest['contracts']:
        for key in settings['variant_order']:
            entry=row['variants'][key]; folder=run/row['contract_id']/entry['variant']; source=BASE/entry['path']
            compiler=observed['compilers'][row['solc']]; compile_dir=folder/'compile'
            cmd=[compiler['path'],'--combined-json',settings['compiler_output'],str(source)]
            rec=execute(cmd,compile_dir,settings['compile_timeout_seconds'],toolenv(BASE/'toolchain/venv'),event)
            comp='failed'; comp_error='compiler_nonzero_exit'
            if rec['status']!='exited': comp=rec['status']; comp_error=rec['error']
            elif rec['exit_code']==0:
                try:
                    data=load(compile_dir/'stdout.txt'); contracts=data['contracts']
                    if not contracts or any(not c.get('bin') for c in contracts.values()): raise ValueError('missing bytecode')
                    abi[(row['contract_id'],entry['variant'])]=sorted([json.loads(c['abi']) if isinstance(c['abi'],str) else c['abi'] for c in contracts.values()],key=str)
                    comp='success'; comp_error=''
                except (ValueError,KeyError): comp='invalid_compiler_output'; comp_error='missing_bytecode_or_invalid_json'
            save(compile_dir/'status.json',dict(compilation_status=comp,error=comp_error))
            for tool in ['slither','mythril']:
                target=folder/tool; toolinfo=observed['tools'][tool]; counts=None; execution=None
                if comp!='success' or not toolinfo['available']:
                    status='skipped_compilation_'+comp if comp!='success' else 'skipped_tool_unavailable'
                    error=comp_error if comp!='success' else 'tool_version_probe_failed'
                    target.mkdir(parents=True); save(target/'execution.json',dict(status=status,error=error,command=None,recorded_utc=utc()))
                    event('analysis_skipped',contract_id=row['contract_id'],variant=entry['variant'],tool=tool,status=status,error=error)
                else:
                    if tool=='slither':
                        cmd=[toolinfo['path'],str(source),'--solc',compiler['path'],'--json',str(target/'report.json')]
                        timeout=settings['slither_timeout_seconds']; venv=BASE/'toolchain/venv'
                    else:
                        cmd=[toolinfo['path'],'analyze',str(source),'--solv',row['solc'],'--no-onchain-data','--execution-timeout',str(settings['mythril_execution_timeout_seconds']),'--solver-timeout',str(settings['mythril_solver_timeout_ms']),'-t',str(settings['mythril_transaction_count']),'-o','json']
                        timeout=settings['mythril_wall_timeout_seconds']; venv=BASE/'toolchain/mythril-venv'
                    env=toolenv(venv); env['SOLC']=compiler['path']
                    execution=execute(cmd,target,timeout,env,event)
                    counts,status,error=(parse_slither if tool=='slither' else parse_mythril)(target,execution)
                results.append(dict(contract_id=row['contract_id'],source_contract=row['source'],variant=entry['variant'],security_patterns=entry['patterns'],solidity_version=row['solc'],compilation_status=comp,tool=tool,vulnerability_detected='' if counts is None else str(counts[0]>0).lower(),vulnerability_count='' if counts is None else counts[0],reentrancy_finding_count='' if counts is None else counts[1],execution_status=status,error_timeout_status=error,exit_code=execution['exit_code'] if execution else '',elapsed_seconds=execution['elapsed_seconds'] if execution else '',raw_output_directory=target.relative_to(run).as_posix(),source_sha256=entry['sha256']))
                flush()
    abi_checks={row['contract_id']: {v: abi.get((row['contract_id'],'V0'))==abi.get((row['contract_id'],v)) if (row['contract_id'],'V0') in abi and (row['contract_id'],v) in abi else None for v in ['V1','V2','V3']} for row in manifest['contracts']}
    summary=dict(status='finished',rows=len(results),compilation_statuses=dict(collections.Counter(r['compilation_status'] for r in results if r['tool']=='slither')),analysis_statuses=dict(collections.Counter(r['execution_status'] for r in results)),abi_matches_baseline=abi_checks,notes='Counts are detector observations, not exploit-prevention evidence. Empty counts mean unknown.')
    save(run/'summary.json',summary); event('run_end',summary=summary); print(run); return 0
if __name__=='__main__': sys.exit(main())
