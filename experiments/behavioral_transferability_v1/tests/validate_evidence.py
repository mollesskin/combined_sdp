#!/usr/bin/env python3
"""Read-only old-artifact checks plus trace/metric recomputation validation."""
import argparse,datetime,hashlib,importlib.util,json,pathlib,tempfile
BASE=pathlib.Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('runs',nargs='+',type=pathlib.Path);ap.add_argument('--output',type=pathlib.Path,default=BASE/'validation.json');a=ap.parse_args();issues=[]
 for lockfile in ['protocol.lock.json','execution.lock.json']:
  for f,h in json.loads((BASE/lockfile).read_text())['sha256'].items():
   if sha(BASE/f)!=h:issues.append('lock drift '+f)
 snap=json.loads((BASE/'preservation_snapshot.json').read_text())
 for f,h in snap['sha256'].items():
  if not (ROOT/f).is_file() or sha(ROOT/f)!=h:issues.append('prior file drift '+f)
 old=ROOT/'experiments/behavioral_pilot_v1';uc01=json.loads((old/'artifact.lock.json').read_text())
 for f,h in uc01['sha256'].items():
  if sha(old/f)!=h:issues.append('UC01 artifact drift '+f)
 manifest=json.loads((BASE/'source_manifest.json').read_text());meta={r['path']:r for r in json.loads((ROOT/'vulnerabilities.json').read_text())}
 for cid,m in manifest.items():
  if sha(ROOT/m['source'])!=m['source_sha256'] or (BASE/m['variants']['V0']['path']).read_bytes()!=(ROOT/m['source']).read_bytes():issues.append('baseline drift '+cid)
  if not any(v['category']=='unchecked_low_level_calls' for v in meta[m['source']]['vulnerabilities']):issues.append('metadata mismatch '+cid)
  for v,r in m['variants'].items():
   if sha(BASE/r['path'])!=r['sha256']:issues.append('variant hash drift '+cid+v)
 spec=importlib.util.spec_from_file_location('transfer_summary',BASE/'tests/summarize.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 count=0;traces=0;setups={};recomputed=[];processed=[]
 for run in a.runs:
  run=run.resolve();originals={n:(run/n).read_bytes() for n in ['behavioral_results.csv','invariant_results.csv','summary.json']}
  with tempfile.TemporaryDirectory(prefix='transfer_summary_check_') as tmp:
   p=pathlib.Path(tmp);(p/'raw').symlink_to(run/'raw',target_is_directory=True);module.summarize(p)
   for n,v in originals.items():
    if (p/n).read_bytes()!=v:issues.append('summary recomputation mismatch '+str(run/n))
  recomputed.append(str(run.relative_to(BASE)))
  abi=json.loads((run/'raw/abi_comparison.json').read_text())
  for cid,d in abi.items():
   if len(d['matches_V0'])!=4 or not all(d['matches_V0'].values()) or d['compile_errors']:issues.append('compilation/ABI gate '+cid)
  for p in sorted((run/'raw/trials').glob('*/*/*/observation.json')):
   r=json.loads(p.read_text());count+=1
   if r['execution_status']!='completed':issues.append('incomplete trial '+str(p));continue
   if not r['snapshot_restored'] or not all(r['setup_checks'].values()):issues.append('setup/snapshot mismatch '+str(p))
   key=(r['contract_id'],r['scenario']);initial=r['before']
   if key in setups and setups[key]!=initial:issues.append('unmatched initial state '+str(key))
   setups[key]=initial
   raw=json.loads((p.parent/'07_primary_operation.json').read_text());traces+=1
   if raw['receipt']['status']!=r['outer_status'] or raw['computation']['output']!=r['outer_return_data'] or raw['computation']['is_error']!=(r['outer_status']==0):issues.append('parent receipt/trace mismatch '+str(p))
   def find(c):return [x for child in c['children'] for x in ([child] if child['code_address'].lower()==r['actors']['token'].lower() else [])+find(child)]
   calls=find(raw['computation'])
   if len(calls)!=1 or calls[0]['output']!=r['low_level_return_data'] or (not calls[0]['is_error'])!=r['low_level_status']:issues.append('CALL observation mismatch '+str(p))
   for tx in p.parent.glob('*.json'):
    rec=json.loads(tx.read_text())
    if 'receipt' in rec and (rec['options']['gas']!=12000000 or rec['options']['gasPrice']!=1):issues.append('budget mismatch '+str(tx))
   processed.append(r)
  for cid,m in manifest.items():
   v=json.loads((run/'raw/versions.json').read_text())['compilers'][cid]
   for variant in ['V0','V1','V2','V3','fixture']:
    e=json.loads((run/'raw/compile'/(cid+'_'+variant)/'execution.json').read_text())
    if e['status']!='compiled' or e['compiler_sha256']!=v['sha256'] or ('Version: '+m['compiler']+'+') not in v['stdout']:issues.append('compiler mismatch '+cid+variant)
 # Recompute pairwise classifications without writing the delivered comparison.
 for cid in manifest:
  allrows=[];allinv=[];summaries=[]
  for run in a.runs:
   with tempfile.TemporaryDirectory(prefix='transfer_pair_check_') as tmp:
    p=pathlib.Path(tmp);(p/'raw').symlink_to(run.resolve()/'raw',target_is_directory=True);rs,inv,s=module.summarize(p)
    allrows.extend(r for r in rs if r['contract_id']==cid);allinv.extend(r for r in inv if r['contract_id']==cid);summaries.append(s[cid])
  actual=module.compare(allrows,allinv,summaries);saved=json.loads((BASE/'comparison/comparison.json').read_text())[cid]
  if actual!=saved:issues.append('comparison recomputation mismatch '+cid)
 result={'validated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if not issues else 'FAIL','issues':issues,'prior_files_preserved':len(snap['sha256']),'UC01_frozen_files_verified':len(uc01['sha256']),'source_contracts':2,'variant_sources':8,'clean_process_launches':len(a.runs),'repetitions_per_contract':len(a.runs),'primary_trials':count,'primary_traces_crosschecked':traces,'byte_identical_metric_recomputation':recomputed,'matched_initial_states':True if not issues else None,'new_PES_values':0,'new_analyzer_runs':0,'limits':'No general equivalence proof; contract-specific allowance adaptations and absent-ledger N/A keep results stratified, not pooled with UC01.'}
 if a.output.exists():raise RuntimeError('Preserve existing validation report; choose a fresh --output')
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if issues:raise SystemExit(1)
if __name__=='__main__':main()
