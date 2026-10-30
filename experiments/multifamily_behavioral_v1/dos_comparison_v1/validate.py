"""AI-assisted validation of stored DoS evidence; no previous-stage execution, no PES."""
import pathlib,json,csv,hashlib,collections,argparse
S=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--run1',type=pathlib.Path);parser.add_argument('--run2',type=pathlib.Path);parser.add_argument('--output',type=pathlib.Path,default=S)
a=parser.parse_args()
if a.run1 is None or a.run2 is None:
 paths=json.loads((S/'evaluation_paths.json').read_text());a.run1=S/paths['run1'];a.run2=S/paths['run2']
D=a.output;D.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=read(S/'registry.json')['cases'];checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:
  (D/'validation_checks.json').write_text(json.dumps(checks,indent=2));raise AssertionError(name)
def key(r):return r['file'],r['variant'],r['scenario'],r['step']
def opkey(o):return o['file'],o['variant'],o['scenario']
check('four source files / two factorial / one single / one alternatives',len(reg)==4 and collections.Counter(c['track'] for c in reg)=={'factorial':2,'single':1,'alternatives':1})
for c in reg:
 for v,m in c['variants'].items():check('source hash '+c['file']+' '+v,sha(S/m['path'])==m['sha256'])
 check('V0 identical to reviewed source '+c['file'],c['variants']['V0']['sha256']==c['source_sha256'])
 check('author test preserved '+c['file'],sha(S/'inputs'/pathlib.Path(c['review_proposal']['test_path']).name)==c['test_sha256'])
runs=[]
for label,p in [('run1',a.run1),('run2',a.run2)]:
 rows=read(p/'measurements.json');ops=read(p/'operations.json');history=read(p/'status_history.json');runs.append((rows,ops,history))
 check(label+' complete 13 variants / 338 measured tx / 34 operations',len(rows)==338 and len(ops)==34 and len({(r['file'],r['variant']) for r in rows})==13)
 check(label+' unique tx observations',len({key(r) for r in rows})==len(rows))
 check(label+' final runner v2 / no missing or infrastructure statuses',all(r['instrument_version']=='v2-nested-transaction-hash' and r['execution_status'] in ['success','reverted'] and r['compilation_status']=='success' and r['setup_status']=='success' for r in rows))
 check(label+' gas limit12m all measured calls',all(r['inputs']['gas_limit']=='12000000' and r['gas_used'] is not None and int(r['gas_used'])<=12000000 for r in rows))
 check(label+' raw evidence and receipt status/gas agree',all(pathlib.Path(r['raw_output']).is_file() and read(pathlib.Path(r['raw_output']))['receipt']['status']==(1 if r['execution_status']=='success' else 0) and read(pathlib.Path(r['raw_output']))['receipt']['gasUsed']==r['gas_used'] for r in rows))
 check(label+' mined reverts observed atomic rollback',all(r['full_observed_rollback'] for r in rows if r['execution_status']=='reverted'))
 nested=[r for r in rows if r['error'] and r['error'].get('transactionHash') and r['error'].get('top_level_transactionHash') is None]
 check(label+' four OOG nested-hash receipts recovered',len(nested)==4 and all(r['execution_status']=='reverted' and r['gas_used']=='12000000' and r['full_observed_rollback'] for r in nested))
 compiler=read(p/'compiler_settings.json')
 check(label+' 13 variants same compiler/settings',len(compiler)==13 and len({json.dumps([x['solcLongVersion'],x['settings']],sort_keys=True) for x in compiler})==1 and {x['solcVersion'] for x in compiler}=={'0.4.25'})
 for o in ops:
  rs=[r for r in rows if (r['file'],r['variant'],r['scenario'])==opkey(o)]
  if o['track'] in ['factorial','single']:
   loads=[r for r in rs if r['phase']=='load'];cleanup=[r for r in rs if r['phase']=='cleanup']
   check(label+' requested denominator '+str(opkey(o)),int(o['requested_work'])==len(loads)*350 and int(o['accepted_work'])+int(o['rejected_work'])==int(o['requested_work']) and int(o['completed_work'])+int(o['final_state']['length'])==int(o['accepted_work']))
   check(label+' bounded operation budget '+str(opkey(o)),len(cleanup)<=20 and sum(int(r['gas_used']) for r in cleanup)<=240000000 and int(o['total_workflow_gas_used'])==sum(int(r['gas_used']) for r in loads+cleanup) and int(o['total_workflow_gas_used'])<=int(o['total_workflow_gas_budget']))
   check(label+' successful cleanup progress '+str(opkey(o)),all(0<int(r['before']['length'])-int(r['actual']['length'])<=int(r['before']['length']) for r in cleanup if r['execution_status']=='success'))
   check(label+' full vs accepted completion not conflated '+str(opkey(o)),o['full_requested_task_complete']==(o['accepted_part_complete'] is True and o['accepted_work']==o['requested_work']))
   if o['accepted_part_complete']:
    check(label+' final state and another cycle '+str(opkey(o)),o['final_state']['length']=='0' and o['final_state']['logical']=='0' and not o['final_state']['clearing'] and o['post_completion_refill']['correct'])
   if o['variant'] in ['V2','V3'] and o['scenario']=='load_5950':
    check(label+' cap reject4200 explicitly retained '+str(opkey(o)),o['requested_work']=='5950' and o['accepted_work']=='1750' and o['capacity_rejected']=='4200' and not o['full_requested_task_complete'] and o['completion_requested']=={'numerator':'1750','denominator':'5950'})
  if o['track']=='alternatives':
   check(label+' auction budget and backing '+str(opkey(o)),o['workflow_transactions']<=8 and int(o['total_workflow_gas_used'])<=96000000 and o['live_bid_backed'])
   check(label+' every auction step balances bid plus registered claims '+str(opkey(o)),all(int(r['actual']['contract_wei'])==int(r['actual']['bid'])+sum(map(int,r['actual']['claims'].values())) for r in rs))
   if o['higher_bid_accepted']:
    check(label+' former refund paid/preserved '+str(opkey(o)),int(o['refund_paid_before_claim_wei'])+int(o['refund_owed_after_outbid_wei'])==10 and o['eventual_refund_paid_wei']=='10' and o['final_state']['contract_wei']=='20' and all(v=='0' for v in o['final_state']['claims'].values()))
   if o['scenario']=='refusing_bidder' and o['variant']!='V0':
    check(label+' refusing claim rollback/recovery/repeat '+str(opkey(o)),o['full_requested_task_complete'] and o['claim_failure_rollback'] and o['recovery_correct'] and o['repeat_claim_no_extra_payout'])
  if o['track']=='scope_limit':check(label+' oversize fails without claiming success '+str(opkey(o)),o['requested_work']=='5000' and o['accepted_work']=='0' and o['rejected_work']=='5000' and o['execution_status']=='reverted' and o['full_observed_rollback'] and not o['full_requested_task_complete'])
  if o['track']=='functional_check':check(label+' logical clear/reuse preserved '+str(opkey(o)),o['full_requested_task_complete'] and o['records_check']['correct'])
 # Independently inspect exact stored values, rather than trusting the runner's booleans.
 record_files=list(p.glob('*.records.json'))
 check(label+' record evidence present',len(record_files)>0)
 for f in record_files:
  x=read(f);matching=[o for o in ops if f.name.startswith('.'.join(opkey(o))+'.')];check(label+' records map to one operation '+f.name,len(matching)==1)
  o=matching[0];values=list(map(int,x['values']));check(label+' record count '+f.name,len(values)==int(x['length']))
  if o['file']=='dos_number.sol':basevalue=1
  else:
   sender=next((r['inputs']['sender'] for r in rows if r['file']==o['file'] and r['variant']==o['variant'] and r['scenario']==o['scenario']),None)
   if sender is None:sender=next(h['receipt']['from'] for h in history if h.get('variant')==o['variant'] and h.get('receipt'))
   basevalue=int(sender,16)
  if '.reuse.records.' in f.name:expected=[9 if i<350 else 1 for i in range(len(values))]
  elif '.refill.records.' in f.name:expected=[9 if o['file']=='dos_number.sol' else basevalue]*len(values)
  elif '.after_cleanup.records.' in f.name:expected=[basevalue if i<int(o['final_state']['length']) else 0 for i in range(len(values))]
  else:expected=[basevalue]*len(values)
  check(label+' exact record integrity '+f.name,values==expected and x['incorrect_indices']==[])
 for v in ['V0','F1']:
  hs=[x for x in history if x['variant']==v and x.get('after_mined_blocks')];last={x['hash']:x for x in hs};probes=[x for x in history if x['variant']==v and x['scenario']=='block_budget_admission_probe'];o=next(o for o in ops if o['variant']==v and o['scenario']=='mining_status')
  check(label+' transient pending then included '+v,any(x['after_mined_blocks']==1 and x['execution_status']=='pending' and x['receipt'] is None for x in hs) and len(last)==4 and all(x['execution_status']=='success' for x in last.values()) and o['full_requested_task_complete'] and o['final_pending']==0)
  check(label+' probe rejected before inclusion '+v,len(probes)==1 and probes[0]['execution_status']=='rejected_before_inclusion' and probes[0]['hash'] is None)
 # ABI changes declared; no claim of equivalence.
 changed={(x['file'],x['variant']) for x in read(p/'abi_comparisons.json') if not x['equal_V0']}
 check(label+' ABI changes only stated new workflow functions/getters',changed=={('auction.sol','PULL'),('auction.sol','FALLBACK'),('dos_address.sol','V1'),('dos_address.sol','V3'),('dos_number.sol','V1'),('dos_number.sol','V3'),('dos_simple.sol','F1')})
# Preserve and report differences; a repeat difference is evidence, not something to overwrite.
def canonical(x):
 if isinstance(x,dict):return {k:canonical(v) for k,v in x.items() if k not in ['raw_output','raw_outputs','status_history_raw']}
 if isinstance(x,list):return [canonical(v) for v in x]
 return x
def differences(xs,ys,k):
 x={k(v):canonical(v) for v in xs};y={k(v):canonical(v) for v in ys};return [{'key':i,'run1':x.get(i),'run2':y.get(i)} for i in sorted(x.keys()|y.keys()) if x.get(i)!=y.get(i)]
rowdiff=differences(runs[0][0],runs[1][0],key);opdiff=differences(runs[0][1],runs[1][1],opkey)
status_equal=canonical(runs[0][2])==canonical(runs[1][2])
repeat={'primary_observations_identical_except_output_paths':not rowdiff,'operation_outcomes_identical_except_output_paths':not opdiff,'raw_status_history_identical':status_equal,'observation_differences':rowdiff,'operation_differences':opdiff,'status_history_run1':str(a.run1/'status_history.json'),'status_history_run2':str(a.run2/'status_history.json')}
(D/'repeat_comparison.json').write_text(json.dumps(repeat,ensure_ascii=False,indent=2))
# No tools/scripts in earlier stages executed; only compare their saved bytes.
preservation={}
for name,old in read(S/'previous_stages_before.json').items():
 root=S.parent/name;new={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()};preservation[name]={'unchanged':old==new,'files':len(new)};check(name+' read-only preservation',old==new)
(D/'preservation_check.json').write_text(json.dumps(preservation,indent=2))
rows,ops,history=runs[0];lookup={opkey(o):o for o in ops};comparisons=[]
for o in ops:
 if o['variant']!='V3':continue
 for other in ['V1','V2']:
  b=lookup[(o['file'],other,o['scenario'])];x=o['full_requested_task_complete'];y=b['full_requested_task_complete'];relation='N/A' if x is None or y is None else 'tie' if x==y else 'improvement' if x else 'worsening'
  comparable=o.get('accepted_work')==b.get('accepted_work') and o.get('completed_work')==b.get('completed_work') and x==y and o.get('total_workflow_gas_used') is not None and b.get('total_workflow_gas_used') is not None
  comparisons.append({'file':o['file'],'scenario':o['scenario'],'comparison':'V3_vs_'+other,'full_requested_completion_relation':relation,'requested_work':o['requested_work'],'accepted_V3':o.get('accepted_work'),'accepted_other':b.get('accepted_work'),'completed_V3':o.get('completed_work'),'completed_other':b.get('completed_work'),'rejected_V3':o.get('rejected_work'),'rejected_other':b.get('rejected_work'),'accepted_part_complete_V3':o.get('accepted_part_complete'),'accepted_part_complete_other':b.get('accepted_part_complete'),'cleanup_tx_V3':o.get('cleanup_transactions'),'cleanup_tx_other':b.get('cleanup_transactions'),'gas_total_V3':o.get('total_workflow_gas_used'),'gas_total_other':b.get('total_workflow_gas_used'),'gas_comparable_same_work_and_outcome':comparable,'gas_delta_if_comparable':str(int(o['total_workflow_gas_used'])-int(b['total_workflow_gas_used'])) if comparable else None})
status_summary=[]
for v in ['V0','F1']:
 hs=[h for h in history if h['variant']==v and h.get('after_mined_blocks')];last={h['hash']:h for h in hs};status_summary.append({'file':'dos_simple.sol','variant':v,'requested_work':'1400','included_work':'1400','transaction_count':len(last),'first_block_pending':sum(h['execution_status']=='pending' and h['after_mined_blocks']==1 for h in hs),'final_success_count':sum(h['execution_status']=='success' for h in last.values()),'final_pending_count':sum(h['execution_status']=='pending' for h in last.values()),'total_gas_used':str(sum(int(h['gas_used']) for h in last.values())),'admission_probe':'rejected_before_inclusion'})
def csvwrite(name,rs):
 cols=list(dict.fromkeys(k for r in rs for k in r))
 with (D/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rs)
csvwrite('combination_comparisons.csv',comparisons);csvwrite('mining_status_summary.csv',status_summary)
file_summary=[{'file':c['file'],'group':c['group'],'track':c['track'],'variants':list(c['variants']),'operations_per_run':sum(o['file']==c['file'] for o in ops),'observations_per_run':sum(r['file']==c['file'] for r in rows),'comparison_status':'executed_twice','blocker':None} for c in reg];csvwrite('file_summary.csv',file_summary)
summary={'original_files_evaluated':4,'full_factorial_files':2,'single_fix_files':1,'alternative_workflow_files':1,'source_variants':13,'groups_by_existing_review':4,'groups_independence_claimed':False,'scenario_definitions':len({(o['file'],o['scenario']) for o in ops}),'variant_scenario_instances_per_run':len(ops),'measured_transaction_observations_per_run':len(rows),'diagnostic_submitted_txs_per_run':8,'diagnostic_admission_probes_per_run':2,'primary_repeats':2,'measured_statuses':dict(collections.Counter(r['execution_status'] for r in rows)),'repeat':{k:v for k,v in repeat.items() if not k.endswith('_differences')},'V3_vs_V1':dict(collections.Counter(x['full_requested_completion_relation'] for x in comparisons if x['comparison']=='V3_vs_V1')),'V3_vs_V2':dict(collections.Counter(x['full_requested_completion_relation'] for x in comparisons if x['comparison']=='V3_vs_V2')),'comparison_note':'Relations are observations across scenarios, not counts of independent vulnerabilities; no security/gas composite score.','unresolved_cases':[],'file_summary':file_summary,'evidence_checks_passed':len(checks)}
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));(D/'validation_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
