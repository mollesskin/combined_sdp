"""AI-assisted evidence validation. Counts observations, not additive vulnerability scores."""
import pathlib,json,csv,collections,hashlib,argparse
S=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--run1',type=pathlib.Path,default=S/'runs/run1');parser.add_argument('--run2',type=pathlib.Path,default=S/'runs/run2');parser.add_argument('--output',type=pathlib.Path,default=S);args=parser.parse_args();D=args.output;D.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
reg=read(S/'registry.json')['cases'];r1=read(args.run1/'measurements.json');r2=read(args.run2/'measurements.json');checks=[]
def check(name,yes):
 checks.append({'check':name,'passed':bool(yes)})
 if not yes:raise AssertionError(name)
def key(r):return r['file'],r['variant'],r['scenario'],r['step']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
check('16 registered cases',len(reg)==16)
check('2 factorial / 12 single / 2 unresolved',collections.Counter(c['track'] for c in reg)=={'factorial':2,'single':12,'unresolved':2})
for c in reg:
 for v,source in c['variants'].items():check('source hash '+c['file']+' '+v,sha(S/source['path'])==source['sha256'])
 check('unchanged V0 '+c['file'],c['variants']['V0']['sha256']==c['source_sha256'])
 check('author test hash '+c['file'],sha(S/'inputs/author_tests'/pathlib.Path(c['test_path']).name)==c['test_sha256'])
for label,rows,directory in [('run1',r1,args.run1),('run2',r2,args.run2)]:
 check(label+' 266 unique observations',len(rows)==266 and len({key(r) for r in rows})==266)
 check(label+' 14 executed files / 32 variants',len({r['file'] for r in rows})==14 and len({(r['file'],r['variant']) for r in rows})==32)
 check(label+' no infrastructure/setup/compile errors',all(r['setup_status']=='success' and r['compilation_status']=='success' and r['execution_status'] in ['success','reverted','observation'] and isinstance(r['correct'],bool) for r in rows))
 check(label+' raw outputs exist',all(pathlib.Path(r['raw_output']).is_file() for r in rows))
 check(label+' all single fixes pass common oracle',all(r['correct'] for r in rows if r['variant']=='F1'))
 check(label+' all V1/V3 pass common oracle',all(r['correct'] for r in rows if r['variant'] in ['V1','V3']))
 check(label+' B safety preserved',all(r['security_pass'] for r in rows if r['variant']=='V2' and r['kind']!='allowed'))
 inherited=[r for r in rows if r['variant']=='V2' and not r['correct']]
 check(label+' B inherited restriction exactly zero/partial withdrawal',len(inherited)==2 and all(r['file']=='wallet_04_confused_sign.sol' and r['scenario']=='allowed_partial' and r['method']=='withdraw' and r['kind']=='allowed' and r['execution_status']=='reverted' for r in inherited))
 check(label+' protected forbidden success/no-effect accepted',any(r['variant']=='F1' and r['kind']=='forbidden' and r['execution_status']=='success' and r['correct'] for r in rows))
 check(label+' reverted operations atomically observed rollback',all(r['full_observed_rollback'] for r in rows if r['execution_status']=='reverted'))
 check(label+' constructor owner invariant catches V0 and passes fix',all(r['correct']==(r['variant']=='F1') for r in rows if r['method']=='$deployment'))
 check(label+' >2^53 uint input exact string',any(any(isinstance(x,str) and x.isdecimal() and int(x)>2**53 for x in r['inputs']['args']) for r in rows))
 comp=read(directory/'compiler_settings.json');check(label+' identical compiler/settings in every comparison',len({json.dumps([x['solcLongVersion'],x['settings']],sort_keys=True) for x in comp})==1)
 changes={(x['file'],x['variant']) for x in read(directory/'abi_comparisons.json') if not x['equal_V0']}
 expected_changes={(c['file'],'F1') for c in reg if c['file'].startswith('incorrect_constructor') or c['file'] in ['wallet_03_wrong_constructor.sol','parity_wallet_bug_2.sol','simple_suicide.sol']}
 check(label+' only declared constructor ABI metadata/selector changes',changes==expected_changes)
 # Refund repeat must measure genuine excess payment versus independently maintained claim ledger.
 refunds=[r for r in rows if r['file']=='wallet_02_refund_nosub.sol' and r['scenario']=='normal_refund' and r['method']=='refund']
 check(label+' repeat refund independent claim detects baseline extra 6 wei',any(r['variant']=='V0' and r['excess_payout_wei']=='6' for r in refunds))
 check(label+' protected refunds no excess payout',all(r['excess_payout_wei']=='0' for r in refunds if r['variant']=='F1'))
 check(label+' successful ordinary pop tested',all(r['correct'] for r in rows if r['file']=='arbitrary_location_write_simple.sol' and r['effect']=='pop'))
 check(label+' owner-only simple lifecycle preserves successful shutdown',all(r['correct'] for r in rows if r['file']=='simple_suicide.sol' and r['scenario']=='owner'))
# Compare every saved field other than new raw paths. Receipts are deterministic in this pinned local setup.
def stable(r):return {k:v for k,v in r.items() if k!='raw_output'}
check('clean repeat exact observations match',{key(r):stable(r) for r in r1}=={key(r):stable(r) for r in r2})
check('clean repeat raw receipts and setup match',all({k:v for k,v in read(pathlib.Path(r['raw_output'])).items() if k!='row'}=={k:v for k,v in read(pathlib.Path({key(x):x for x in r2}[key(r)]['raw_output'])).items() if k!='row'} for r in r1))
# Read-only preservation audit: no arithmetic file writes or executions.
A=S.parent/'arithmetic_comparison_v1';before=read(S/'arithmetic_before.json');after={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file()};check('arithmetic all files and hashes unchanged',before==after)
lookup={key(r):r for r in r1};comparisons=[]
for r in r1:
 if r['variant']!='V3':continue
 for other in ['V1','V2']:
  o=lookup[(r['file'],other,r['scenario'],r['step'])]
  def relation(x,y):return 'N/A' if x is None or y is None else 'tie' if x==y else 'improvement' if x else 'worsening'
  same=r['before']['state']==o['before']['state'] and r['inputs']==o['inputs'] and r['execution_status']==o['execution_status'] and r['gas_used'] is not None and o['gas_used'] is not None
  comparisons.append({'file':r['file'],'group':r['group'],'scenario':r['scenario'],'step':r['step'],'method':r['method'],'kind':r['kind'],'comparison':'V3_vs_'+other,'overall_relation':relation(r['correct'],o['correct']),'security_relation':relation(r['security_pass'],o['security_pass']),'functionality_relation':relation(r['functionality_pass'],o['functionality_pass']),'functional_regression':r['kind']=='allowed' and r['functionality_pass'] is False and o['functionality_pass'] is True,'execution_status_V3':r['execution_status'],'execution_status_other':o['execution_status'],'gas_comparable':same,'gas_V3':r['gas_used'],'gas_other':o['gas_used'],'gas_delta':str(int(r['gas_used'])-int(o['gas_used'])) if same else None})
files=[]
for c in reg:
 rs=[r for r in r1 if r['file']==c['file']];variants={}
 for v in c['variants']:
  vr=[r for r in rs if r['variant']==v]
  variants[v]=None if not vr else {'scenarios':len({r['scenario'] for r in vr}),'observations':len(vr),'transaction_observations':sum(r['method']!='$deployment' for r in vr),'allowed_total':sum(r['kind']=='allowed' for r in vr),'allowed_pass':sum(r['functionality_pass'] is True for r in vr),'security_total':sum(r['kind']!='allowed' for r in vr),'security_pass':sum(r['security_pass'] is True for r in vr),'infrastructure_errors':sum(r['correct'] is None for r in vr)}
 files.append({'file':c['file'],'group':c['group'],'track':c['track'],'status':'unresolved' if not rs else 'executed_repeated','reason':c['decision_and_scope'] if not rs else None,'variants':variants})
groups=[]
for g in sorted({c['group'] for c in reg}):
 members=[f for f in files if f['group']==g]
 groups.append({'group':g,'files':[m['file'] for m in members],'tracks':sorted({m['track'] for m in members}),'files_executed':sum(m['status']=='executed_repeated' for m in members),'all_protected_variants_pass_security':None if members[0]['track']=='unresolved' else all(v['security_pass']==v['security_total'] for m in members for k,v in m['variants'].items() if k!='V0'),'all_final_fixes_pass_functionality':None if members[0]['track']=='unresolved' else all(v['allowed_pass']==v['allowed_total'] for m in members for k,v in m['variants'].items() if k in ['V1','V3','F1'])})
def write_csv(name,rs):
 with (D/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rs[0].keys());w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rs)
write_csv('comparisons.csv',comparisons);write_csv('file_summary.csv',files);write_csv('group_summary.csv',groups)
comparison_summary={}
for other in ['V1','V2']:
 cs=[r for r in comparisons if r['comparison']=='V3_vs_'+other]
 comparison_summary['V3_vs_'+other]={k:dict(collections.Counter(x[k] for x in cs)) for k in ['overall_relation','security_relation','functionality_relation']}
summary={'files_considered':16,'files_executed':14,'full_factorial_files':2,'single_fix_files':12,'unresolved_files':2,'groups_total':14,'groups_executed':12,'stored_variants':34,'executed_variants':32,'unique_case_scenarios':len({(r['file'],r['scenario']) for r in r1}),'variant_scenario_instances_per_run':len({(r['file'],r['variant'],r['scenario']) for r in r1}),'observations_per_run':len(r1),'transactions_per_run':sum(r['method']!='$deployment' for r in r1),'deployment_observations_per_run':sum(r['method']=='$deployment' for r in r1),'final_repeats':2,'comparisons':comparison_summary,'files':files,'groups':groups,'evidence_checks':checks}
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));(D/'preservation_check.json').write_text(json.dumps({'arithmetic_unchanged':before==after,'files':len(after)},indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['files','groups','evidence_checks']},ensure_ascii=False,indent=2));print(str(len(checks))+' evidence checks passed')
