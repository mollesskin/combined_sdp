#!/usr/bin/env python3
"""Derive state/financial properties from saved local observations, separate from PES."""
import argparse,csv,json,pathlib,hashlib
from fractions import Fraction
BASE=pathlib.Path(__file__).resolve().parents[1]
SECURITY=['I1','I2','I3','I5']
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def csvsave(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def evaluate(s):
 a,b=s['before'],s['after'];w=s['authorized_amount_wei'];p=b['receiver_ether_wei']-a['receiver_ether_wei'];c0,c1=a['actor_credit_wei'],b['actor_credit_wei'];o0,o1=a['other_credit_wei'],b['other_credit_wei'];g0,g1=a['aggregate_wei'],b['aggregate_wei']
 debit=c0-c1;conserve=a['bank_ether_wei']-b['bank_ether_wei']==p and b['bank_ether_wei']+b['receiver_ether_wei']==a['bank_ether_wei']+a['receiver_ether_wei'];aggregate_ok=g1 is None or (g1==g0-p and g1==c1+o1)
 frame=['bank_ether_wei','receiver_ether_wei','actor_credit_wei','other_credit_wei','aggregate_wei','last_withdraw_time']
 rollback=s['outer_status']==0 and all(a[k]==b[k] for k in frame) and b['guard_entered'] in [None,0]
 permitted=s['outer_status']==1 and p==w and c1==c0-w and o1==o0 and (g1 is None or g1==g0-w) and (b['last_withdraw_time'] is None or b['last_withdraw_time']==s['block_timestamp']) and b['guard_entered'] in [None,0] and conserve
 values={'I1':0<=p<=w,'I2':debit==p and 0<=c1<=c0 and o1==o0 and aggregate_ok,'I3':conserve,'I4':rollback,'I5':b['bank_ether_wei']>=c1+o1 and (g1 is None or (g1==c1+o1 and b['bank_ether_wei']>=g1)),'I6':permitted}
 applicable={k:(s['intended_rejection'] or s['outer_status']==0) if k=='I4' else not s['intended_rejection'] if k=='I6' else True for k in values}
 metrics={'payout_wei':p,'authorized_amount_wei':w,'excess_payout_wei':max(0,p-w),'normalized_excess_payout':str(Fraction(max(0,p-w),w)),'credit_mismatch_wei':abs(debit-p),'credit_increased_or_wrap':c1>c0,'claim_shortfall_wei':max(0,c1+o1-b['bank_ether_wei']),'aggregate_minus_claims_wei':g1-(c1+o1) if g1 is not None else None}
 return values,applicable,metrics
STEPS={'O1':['06_first_withdraw','08_second_withdraw'],'F1':['06_rejected_withdraw','08_recovery_withdraw'],'S1':['06_bounded_reentry']}
def summarize(folder):
 cfg=json.loads((folder/'raw/inputs.json').read_text());abi=json.loads((folder/'raw/abi_comparison.json').read_text());rows=[];inv=[]
 for p in sorted((folder/'raw/trials').glob('*/*/*/observation.json')):
  r=json.loads(p.read_text());step_index={s['step']:s for s in r['steps']}
  for name in STEPS[r['scenario']]:
   s=step_index.get(name);valid=r['execution_status']=='completed' and s is not None;reject=name=='06_rejected_withdraw';app={k:reject if k=='I4' else not reject if k=='I6' else True for k in cfg['invariants']};values={};metrics={k:None for k in ['payout_wei','authorized_amount_wei','excess_payout_wei','normalized_excess_payout','credit_mismatch_wei','credit_increased_or_wrap','claim_shortfall_wei','aggregate_minus_claims_wei']}
   if valid:values,app,metrics=evaluate(s)
   row={k:r[k] for k in ['contract_id','variant','scenario','run','compilation_status','deployment_status','setup_status','execution_status']};row.update(step=name,test_kind='security' if r['scenario']=='S1' else 'rollback' if reject else 'ordinary_functionality',abi_matches_V0=abi[r['contract_id']]['matches_V0'].get(r['variant']),outer_status=s.get('outer_status') if s else None,outer_error=s.get('outer_error') if s else None,outer_gas_used=s.get('outer_gas_used') if s else None)
   for key in ['bank_ether_wei','receiver_ether_wei','actor_credit_wei','other_credit_wei','aggregate_wei','last_withdraw_time','guard_entered','callbacks','public_getter_matches_storage']:
    for phase in ['before','after']:row[key+'_'+phase]=s.get(phase,{}).get(key) if s else None
   row.update(metrics);row.update(nested_attempts=s.get('nested_attempts') if s else None,applicable_invariants=sum(app.values()),violated_invariant_ids=[k for k in values if app[k] and not values[k]] if valid else None,security_violated_ids=[k for k in SECURITY if not values[k]] if valid else None,security_properties_satisfied=all(values[k] for k in SECURITY) if valid else None,permitted_operation_satisfied=values.get('I6') if valid and app['I6'] else None,rollback_satisfied=values.get('I4') if valid and app['I4'] else None,error=r['error'],raw_evidence_path=r['raw_evidence_path'],observation_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   rows.append(row)
   for k,label in cfg['invariants'].items():inv.append({'contract_id':r['contract_id'],'variant':r['variant'],'scenario':r['scenario'],'run':r['run'],'step':name,'invariant_id':k,'name':label,'applicable':app[k],'satisfied':values.get(k) if valid and app[k] else None,'status':'not_applicable' if not app[k] else 'passed' if valid and values[k] else 'violated' if valid else 'inconclusive','raw_evidence_path':r['raw_evidence_path']})
 csvsave(folder/'behavioral_results.csv',rows);csvsave(folder/'invariant_results.csv',inv)
 summary={}
 for case in cfg['cases']:
  cid=case['id'];summary[cid]={}
  for v in cfg['variants']:
   rr=[r for r in rows if r['contract_id']==cid and r['variant']==v];normal=[r for r in rr if r['scenario']!='S1' and r['test_kind']=='ordinary_functionality'];rollback=[r for r in rr if r['test_kind']=='rollback'];sec=[r for r in rr if r['scenario']=='S1'];good=lambda r:r['execution_status']=='completed';s=sec[0]
   summary[cid][v]={'withdrawal_steps_expected':5,'withdrawal_steps_completed':sum(good(r) for r in rr),'ordinary_allowed_operations_passed':sum(r['permitted_operation_satisfied'] is True for r in normal),'ordinary_allowed_operations_expected':3,'rejection_rollback_passed':all(r['rollback_satisfied'] is True for r in rollback),'ordinary_functionality_preserved':len(normal)==3 and all(good(r) and r['permitted_operation_satisfied'] is True and r['security_properties_satisfied'] is True for r in normal) and len(rollback)==1 and all(good(r) and r['rollback_satisfied'] is True for r in rollback),'security_scenarios_expected':1,'security_scenarios_completed':sum(good(r) for r in sec),'security_scenarios_satisfied':sum(r['security_properties_satisfied'] is True for r in sec),'security_scenario_violated_ids':s['security_violated_ids'],'security_outer_permitted_operation':s['permitted_operation_satisfied'],'excess_payout_wei':s['excess_payout_wei'],'credit_mismatch_wei':s['credit_mismatch_wei'],'claim_shortfall_wei':s['claim_shortfall_wei'],'credit_increased_or_wrap':s['credit_increased_or_wrap'],'infrastructure_errors':sum(not good(r) for r in rr)}
 save(folder/'summary.json',summary);return rows,inv,summary

def comparison(rows,inv,summaries,cid):
 out=[];indexes={(r['run'],r['variant'],r['scenario'],r['step']):r for r in rows if r['contract_id']==cid};keys=sorted({(r['run'],r['scenario'],r['step']) for r in rows if r['contract_id']==cid})
 for comp in ['V1','V2']:
  better=False;worse=False;missing=False;evidence=[]
  for rep,sc,step in keys:
   a=indexes.get((rep,'V3',sc,step));b=indexes.get((rep,comp,sc,step))
   if not a or not b or a['execution_status']!='completed' or b['execution_status']!='completed':missing=True;continue
   av={r['invariant_id']:r['satisfied'] for r in inv if r['contract_id']==cid and r['run']==rep and r['variant']=='V3' and r['scenario']==sc and r['step']==step and r['invariant_id'] in SECURITY}
   bv={r['invariant_id']:r['satisfied'] for r in inv if r['contract_id']==cid and r['run']==rep and r['variant']==comp and r['scenario']==sc and r['step']==step and r['invariant_id'] in SECURITY}
   improved=[k for k in SECURITY if av[k] and not bv[k]];regressed=[k for k in SECURITY if not av[k] and bv[k]];better|=bool(improved);worse|=bool(regressed)
   for metric in ['excess_payout_wei','credit_mismatch_wei','claim_shortfall_wei']:
    better|=a[metric]<b[metric];worse|=a[metric]>b[metric]
   evidence.append({'run':rep,'scenario':sc,'step':step,'improved_properties':improved,'regressed_properties':regressed,'V3_consequences':{k:a[k] for k in ['excess_payout_wei','credit_mismatch_wei','claim_shortfall_wei']},'comparator_consequences':{k:b[k] for k in ['excess_payout_wei','credit_mismatch_wei','claim_shortfall_wei']}})
  normal3=all(s[cid]['V3']['ordinary_functionality_preserved'] and s[cid]['V3']['security_outer_permitted_operation'] is True for s in summaries);normalc=all(s[cid][comp]['ordinary_functionality_preserved'] and s[cid][comp]['security_outer_permitted_operation'] is True for s in summaries)
  label='insufficient evidence' if missing else 'trade-off' if (better and worse) or (better and not normal3 and normalc) else 'functional regression' if normalc and not normal3 else 'insufficient evidence' if not normal3 or not normalc else 'additional observed protection' if better else 'worse/security regression' if worse else 'equal observed protection'
  out.append({'contract_id':cid,'comparison':'V3 vs '+comp,'classification':label,'ordinary_and_permitted_functionality_preserved':normal3 and normalc,'matched_evidence':evidence})
 return {'comparisons':out,'additional_benefit_over_both':all(c['classification']=='additional observed protection' for c in out)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('runs',nargs='+',type=pathlib.Path);ap.add_argument('--comparison-output',type=pathlib.Path,required=True);a=ap.parse_args();allrows=[];allinv=[];summaries=[];per_run=[]
 for run in a.runs:
  rr,ii,ss=summarize(run.resolve());allrows+=rr;allinv+=ii;summaries.append(ss);per_run.append(rr)
 a.comparison_output.mkdir(parents=True,exist_ok=True);cc={cid:comparison(allrows,allinv,summaries,cid) for cid in ['RE01','RE02','RE03']};save(a.comparison_output/'comparison.json',cc)
 csvsave(a.comparison_output/'comparison.csv',[{k:v for k,v in c.items() if k!='matched_evidence'} for cid in cc for c in cc[cid]['comparisons']])
 stable=lambda rs,cid:[{k:v for k,v in r.items() if k not in ['run','raw_evidence_path','observation_sha256']} for r in rs if r['contract_id']==cid]
 repro={cid:len(per_run)>1 and all(stable(per_run[0],cid)==stable(r,cid) for r in per_run[1:]) for cid in cc}
 save(a.comparison_output/'reproducibility.json',{'source_contracts':3,'variant_sources':12,'clean_process_launches':len(a.runs),'repetitions_per_contract':len(a.runs),'withdrawal_steps':len(allrows),'behavioral_metrics_identical':repro,'note':'Repeated deterministic trials are not independent source contracts; no PES.'})
 print(json.dumps({'comparisons':[{k:v for k,v in c.items() if k!='matched_evidence'} for cid in cc for c in cc[cid]['comparisons']],'reproducibility':repro},indent=2))
if __name__=='__main__':main()
