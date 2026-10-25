"""AI-assisted independent evidence checks and descriptive summaries. No PES."""
import pathlib,json,csv,hashlib,collections,sys,argparse
P=pathlib.Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
parser=argparse.ArgumentParser();parser.add_argument('--run1',type=pathlib.Path,default=P/'runs/run1');parser.add_argument('--run2',type=pathlib.Path,default=P/'runs/run2');parser.add_argument('--output',type=pathlib.Path,default=P)
args=parser.parse_args();D=args.output;D.mkdir(parents=True,exist_ok=True)
reg=read(P/'registry.json')['cases'];r1=read(args.run1/'measurements.json');r2=read(args.run2/'measurements.json')
checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
def key(r):return (r['file'],r['variant'],r['scenario'],r['step'])
check('13 registered files, 52 variants',len(reg)==13 and len({(r['file'],r['variant']) for r in r1})==52)
for c in reg:
 for v,m in c['variants'].items():check('source hash '+c['file']+' '+v,hashlib.sha256((P/m['path']).read_bytes()).hexdigest()==m['sha256'])
 check('V0 identical to reviewed baseline '+c['file'],c['variants']['V0']['sha256']==c['source_sha256'])
for label,rows in [('run1',r1),('run2',r2)]:
 check(label+' complete unique rows',len(rows)==244 and len({key(r) for r in rows})==len(rows))
 check(label+' infrastructure absent',all(r['compilation_status']=='success' and r['setup_status']=='success' and r['execution_status'] in ['success','reverted'] for r in rows))
 check(label+' raw evidence exists',all(pathlib.Path(r['raw_output']).is_file() for r in rows))
 check(label+' allowed state exact',all(r['correct'] and r['execution_status']=='success' and not r['field_discrepancies'] for r in rows if r['kind']=='allowed'))
 check(label+' protected unsafe reverts rollback',all(r['correct'] and r['execution_status']=='reverted' and r['full_observed_rollback'] for r in rows if r['kind']=='unsafe' and r['variant']!='V0'))
 check(label+' baseline unsafe observed',all(not r['correct'] and r['execution_status']=='success' and r['wraparound'] for r in rows if r['kind']=='unsafe' and r['variant']=='V0'))
 check(label+' ABI same (interface check only)',all(x['equal_V0'] for x in read((args.run1 if label=='run1' else args.run2)/'abi_comparisons.json')))
 compiler=read((args.run1 if label=='run1' else args.run2)/'compiler_settings.json')
 check(label+' fixed compiler settings all variants',len({json.dumps([x['solcLongVersion'],x['settings']],sort_keys=True) for x in compiler})==1)
 check(label+' exact >2^53 value persisted',any(any(abs(int(t['mathematical_result']))>2**53 for t in r['arithmetic_trace']) for r in rows))
# Ignore output path only; tx hashes/errors, gas, state and inputs must reproduce exactly.
def stable(r):return {k:v for k,v in r.items() if k!='raw_output'}
check('two clean runs exact match except raw path',{key(r):stable(r) for r in r1}=={key(r):stable(r) for r in r2})
lookup={key(r):r for r in r1}
comparisons=[]
for r in r1:
 if r['variant']!='V3':continue
 for other in ['V1','V2']:
  x=lookup[(r['file'],other,r['scenario'],r['step'])]
  relation='tie' if r['correct']==x['correct'] else 'improvement' if r['correct'] else 'worsening'
  comparable=r['execution_status']==x['execution_status'] and r['inputs']==x['inputs'] and r['before']==x['before']
  comparisons.append(dict(file=r['file'],group=r['group'],scenario=r['scenario'],step=r['step'],kind=r['kind'],comparison='V3_vs_'+other,relation=relation,functional_regression=r['kind']=='allowed' and not r['correct'],execution_status=r['execution_status'],gas_comparable=comparable,gas_V3=r['gas_used'],gas_other=x['gas_used'],gas_delta=str(int(r['gas_used'])-int(x['gas_used'])) if comparable else None))
files=[]
for c in reg:
 row={'file':c['file'],'group':c['group'],'status':'complete','missing_reason':None}
 for v in ['V0','V1','V2','V3']:
  rs=[r for r in r1 if r['file']==c['file'] and r['variant']==v]
  row[v]={'allowed_pass':sum(r['correct'] for r in rs if r['kind']=='allowed'),'allowed_total':sum(r['kind']=='allowed' for r in rs),'unsafe_safe_rejection':sum(r['correct'] for r in rs if r['kind']=='unsafe'),'unsafe_total':sum(r['kind']=='unsafe' for r in rs),'ordinary_rejection_pass':sum(r['correct'] for r in rs if r['kind']=='reject')}
 files.append(row)
groups=[]
for group in sorted({c['group'] for c in reg}):
 members=[f for f in files if f['group']==group]
 groups.append({'group':group,'files':[f['file'] for f in members],'all_members_complete':all(f['status']=='complete' for f in members),'V0_any_unsafe_failure':any(f['V0']['unsafe_safe_rejection']<f['V0']['unsafe_total'] for f in members),'protected_all_members_unsafe_rejected':all(f[v]['unsafe_safe_rejection']==f[v]['unsafe_total'] for f in members for v in ['V1','V2','V3']),'protected_all_allowed_pass':all(f[v]['allowed_pass']==f[v]['allowed_total'] for f in members for v in ['V1','V2','V3'])})
def write_csv(name,rows):
 with (D/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
write_csv('comparisons.csv',comparisons);write_csv('file_summary.csv',files);write_csv('group_summary.csv',groups)
summary={'files':len(files),'full_four_variant_comparisons':len(files),'groups':len(groups),'rows_per_run':len(r1),'repeats':2,'V3_vs_V1':dict(collections.Counter(r['relation'] for r in comparisons if r['comparison']=='V3_vs_V1')),'V3_vs_V2':dict(collections.Counter(r['relation'] for r in comparisons if r['comparison']=='V3_vs_V2')),'files_detail':files,'groups_detail':groups,'checks':checks}
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['files_detail','groups_detail','checks']},indent=2));print(f'{len(checks)} evidence checks passed')
