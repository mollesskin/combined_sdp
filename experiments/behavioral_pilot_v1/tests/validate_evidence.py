#!/usr/bin/env python3
"""Validate locks, prior preservation, raw traces and byte-identical metric recomputation."""
import argparse,csv,datetime,hashlib,importlib.util,json,pathlib,tempfile
BASE=pathlib.Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('runs',type=pathlib.Path,nargs='+');args=ap.parse_args();issues=[]
 for name in ['protocol.lock.json','execution.lock.json']:
  lock=json.loads((BASE/name).read_text())
  for f,h in lock['sha256'].items():
   if sha(BASE/f)!=h:issues.append('lock drift: '+f)
 snap=json.loads((BASE/'preservation_snapshot.json').read_text())
 for f,h in snap['sha256'].items():
  if not (ROOT/f).is_file() or sha(ROOT/f)!=h:issues.append('prior drift: '+f)
 manifest=json.loads((BASE/'source_manifest.json').read_text());assert (BASE/'variants/V0/TokenBank.sol').read_bytes()==(ROOT/manifest['original_source']).read_bytes()
 spec=importlib.util.spec_from_file_location('pilot_summarize',BASE/'tests/summarize.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 trial_count=0;trace_count=0;recomputed=[]
 for run in args.runs:
  run=run.resolve();csvs={name:(run/name).read_bytes() for name in ['behavioral_results.csv','invariant_results.csv','summary.json']}
  # Recompute only in a temporary directory; preserve every original output.
  with tempfile.TemporaryDirectory(prefix='uc01_metric_check_') as tmp:
   work=pathlib.Path(tmp);(work/'raw').symlink_to(run/'raw',target_is_directory=True);module.summarize(work)
   for name,original in csvs.items():
    if (work/name).read_bytes()!=original:issues.append('derived metric drift: '+str(run/name))
  recomputed.append(str(run.relative_to(BASE)))
  for p in (run/'raw/trials').glob('*/*/observation.json'):
   r=json.loads(p.read_text());trial_count+=1
   if r['execution_status']!='completed':issues.append('incomplete: '+str(p));continue
   raw=json.loads((p.parent/'08_primary_operation.json').read_text());trace_count+=1
   if raw['receipt']['status']!=r['outer_status']:issues.append('receipt mismatch: '+str(p))
   if raw['computation']['is_error']!=(r['outer_status']==0):issues.append('outer computation mismatch')
   def find(c):return [x for child in c['children'] for x in ([child] if child['code_address'].lower()==r['actors']['token'].lower() else [])+find(child)]
   calls=find(raw['computation'])
   if len(calls)!=1 or calls[0]['output']!=r['low_level_return_data'] or (not calls[0]['is_error'])!=r['low_level_status']:issues.append('child trace mismatch')
   for tx in p.parent.glob('*.json'):
    v=json.loads(tx.read_text())
    if 'receipt' in v and (v['options']['gas']!=12000000 or v['options']['gasPrice']!=1):issues.append('budget drift: '+str(tx))
 result={'validated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if not issues else 'FAIL','issues':issues,'prior_files_preserved':len(snap['sha256']),'trial_observations':trial_count,'primary_traces_crosschecked':trace_count,'byte_identical_recomputation':recomputed,'new_analyzer_runs':0,'new_PES_computations':0,'limits':'Defined pilot observations only; source/ABI comparison and tests are not proof of full functional equivalence.'}
 p=BASE/'validation.json'
 if p.exists():raise RuntimeError('Validation report already exists; preserve it')
 p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if issues:raise SystemExit(1)
if __name__=='__main__':main()
