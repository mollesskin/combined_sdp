#!/usr/bin/env python3
"""Validate frozen artifacts, raw execution evidence and repeatable derivation without EVM runs."""
import argparse,datetime,hashlib,importlib.util,json,pathlib,tempfile
BASE=pathlib.Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('runs',nargs='+',type=pathlib.Path);ap.add_argument('--output',type=pathlib.Path,default=BASE/'validation.json');a=ap.parse_args();issues=[]
 for name in ['protocol.lock.json','execution.lock.json']:
  for f,h in json.loads((BASE/name).read_text())['sha256'].items():
   if sha(BASE/f)!=h:issues.append('lock drift '+f)
 snap=json.loads((BASE/'preservation_snapshot.json').read_text())
 for f,h in snap['sha256'].items():
  if not (ROOT/f).is_file() or sha(ROOT/f)!=h:issues.append('prior drift '+f)
 branches={}
 for name in ['behavioral_pilot_v1','behavioral_transferability_v1']:
  old=ROOT/'experiments'/name;lock=json.loads((old/'artifact.lock.json').read_text());branches[name]=len(lock['sha256'])
  for f,h in lock['sha256'].items():
   if sha(old/f)!=h:issues.append('closed branch drift '+name+'/'+f)
 cfg=json.loads((BASE/'scenario_inputs.json').read_text())
 for case in cfg['cases']:
  for v,s in case['sources'].items():
   if sha(ROOT/s['path'])!=s['sha256']:issues.append('original source drift '+case['id']+v)
  if (ROOT/case['sources']['V0']['path']).read_bytes()!=(ROOT/'dataset/reentrancy'/case['filename']).read_bytes():issues.append('benchmark mismatch '+case['id'])
 provenance=json.loads((BASE/'fixture_provenance.json').read_text());old=(ROOT/provenance['original_fixture']).read_text();extracted=old[old.index('contract LocalRecipient'):];new=(BASE/'fixtures/LocalRecipient.sol').read_text();assert new[new.index('contract LocalRecipient'):]==extracted
 spec=importlib.util.spec_from_file_location('re_summary',BASE/'tests/summarize.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 allrows=[];allinv=[];summaries=[];trials=steps=traces=0;initials={};recomputed=[]
 for run in a.runs:
  run=run.resolve();original={n:(run/n).read_bytes() for n in ['behavioral_results.csv','invariant_results.csv','summary.json']}
  with tempfile.TemporaryDirectory(prefix='re_state_check_') as tmp:
   work=pathlib.Path(tmp);(work/'raw').symlink_to(run/'raw',target_is_directory=True);rs,inv,summary=module.summarize(work);allrows+=rs;allinv+=inv;summaries.append(summary)
   for n,raw in original.items():
    if (work/n).read_bytes()!=raw:issues.append('derived mismatch '+str(run/n))
  recomputed.append(str(run.relative_to(BASE)))
  versions=json.loads((run/'raw/versions.json').read_text())
  for case in cfg['cases']:
   baseabi=None;compiler=versions['compilers'][case['compiler']]
   for v,s in case['sources'].items():
    folder=run/'raw/compile'/(case['id']+'_'+v);e=json.loads((folder/'execution.json').read_text())
    if e['status']!='compiled' or e['compiler_sha256']!=compiler['sha256'] or e['source_sha256']!=s['sha256']:issues.append('compiler/source provenance mismatch')
    data=json.loads((folder/'stdout.txt').read_text())['contracts'];c=next(value for name,value in data.items() if name.rsplit(':',1)[-1]==case['contract']);abi=json.loads(c['abi']) if isinstance(c['abi'],str) else c['abi']
    if baseabi is None:baseabi=abi
    elif sorted(json.dumps(x,sort_keys=True) for x in abi)!=sorted(json.dumps(x,sort_keys=True) for x in baseabi):issues.append('ABI mismatch '+case['id']+v)
  for p in sorted((run/'raw/trials').glob('*/*/*/observation.json')):
   r=json.loads(p.read_text());trials+=1
   if r['execution_status']!='completed':issues.append('infrastructure failure '+str(p));continue
   if not all(r['setup_checks'].values()):issues.append('setup failed '+str(p))
   initial={k:r['initial_state'][k] for k in ['bank_ether_wei','receiver_ether_wei','actor_credit_wei','other_credit_wei','aggregate_wei','last_withdraw_time','callbacks']};key=(r['contract_id'],r['scenario'])
   if key in initials and initials[key]!=initial:issues.append('unequal initial conditions '+str(key))
   initials[key]=initial
   if len(r['steps'])!=len(module.STEPS[r['scenario']]):issues.append('step count mismatch')
   for s in r['steps']:
    steps+=1;raw=json.loads((p.parent/s['raw_transaction']).read_text());traces+=1
    if raw['receipt']['status']!=s['outer_status'] or raw['computation']['is_error']!=(s['outer_status']==0):issues.append('receipt/computation mismatch')
    def find(c):return [x for child in c['children'] for x in ([child] if child['code_address'].lower()==r['actors']['bank'].lower() else [])+find(child)]
    calls=find(raw['computation'])
    # Only withdraw calls can target bank during these receiver.withdraw transactions.
    if calls!=s['bank_withdrawal_calls']:issues.append('CALL trace mismatch')
    for phase in ['before','after']:
     st=s[phase]
     for label,field in [('actor_credit','actor_credit_wei'),('other_credit','other_credit_wei'),('aggregate','aggregate_wei'),('last_withdraw','last_withdraw_time'),('guard','guard_entered')]:
      if field in st and st[field] is not None and int(st['storage_words'][label]['word'],16)!=st[field]:issues.append('raw storage mismatch')
     if st['public_getter_matches_storage'] is False:issues.append('getter mismatch')
   for tx in p.parent.glob('*.json'):
    record=json.loads(tx.read_text())
    if 'receipt' in record and (record['options']['gas']!=12000000 or record['options']['gasPrice']!=1):issues.append('budget drift')
 saved=json.loads((BASE/'comparison/comparison.json').read_text())
 for cid in saved:
  if module.comparison(allrows,allinv,summaries,cid)!=saved[cid]:issues.append('pairwise recomputation mismatch '+cid)
 result={'validated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if not issues else 'FAIL','issues':issues,'previous_files_preserved':len(snap['sha256']),'closed_UC_branch_files_verified':branches,'source_contracts':3,'existing_variant_sources':12,'modified_benchmark_or_treatment_sources':0,'clean_process_launches':len(a.runs),'scenario_trials':trials,'withdrawal_steps':steps,'actual_traces_crosschecked':traces,'byte_identical_metric_recomputation':recomputed,'static_tool_runs':0,'PES_values':0,'scope':'Defined local scenarios only; no full equivalence proof or general prevention-probability claim.'}
 if a.output.exists():raise RuntimeError('Preserve existing validation report; choose a fresh --output')
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if issues:raise SystemExit(1)
if __name__=='__main__':main()
