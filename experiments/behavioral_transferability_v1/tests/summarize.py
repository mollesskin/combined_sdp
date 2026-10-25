#!/usr/bin/env python3
"""Derive stratified UC02/UC03 metrics from saved traces/states only; no PES."""
import argparse,csv,hashlib,json,pathlib
from fractions import Fraction
BASE=pathlib.Path(__file__).resolve().parents[1]
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def writecsv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def evaluate(before,after,status,output,negative,a):
 f0,f1=before['source_tokens'],after['source_tokens'];r0,r1=before['recipient_tokens'],after['recipient_tokens'];c0,c1=before['airdrop_tokens'],after['airdrop_tokens'];l0,l1=before['allowance'],after['allowance'];q0,q1=before['airdrop_ether_wei'],after['airdrop_ether_wei'];d=r1-r0
 true_data=output=='0x'+(1).to_bytes(32,'big').hex();delivery=d==a and f0-f1==a and c1==c0 and l0-l1==a
 conservation=f1+r1+c1==f0+r0+c0
 values={'I1':status!=1 or (true_data and delivery),'I2':None,'I3':conservation,'I4':status==0 and f1==f0 and r1==r0 and c1==c0 and l1==l0,'I5':q1==q0,'I6':status==1 and true_data and delivery and conservation and q1==q0}
 applicable={k:False if k=='I2' else negative if k=='I4' else not negative if k=='I6' else True for k in values}
 return values,applicable

def summarize(folder):
 cfg=json.loads((folder/'raw/inputs.json').read_text());abi=json.loads((folder/'raw/abi_comparison.json').read_text());rows=[];invariants=[]
 for p in sorted((folder/'raw/trials').glob('*/*/*/observation.json')):
  r=json.loads(p.read_text());valid=r['execution_status']=='completed';a=r['amount'];values={};app={k:False if k=='I2' else r['negative'] if k=='I4' else not r['negative'] if k=='I6' else True for k in cfg['invariants']};probe=None
  row={k:r.get(k) for k in ['contract_id','variant','scenario','run','compilation_status','deployment_status','setup_status','execution_status']}
  row.update(abi_matches_V0=abi[r['contract_id']]['matches_V0'].get(r['variant']),outer_transaction_status=r.get('outer_status'),outer_return_data=r.get('outer_return_data'),outer_gas_used=r.get('outer_gas_used'),low_level_call_status=r.get('low_level_status'),low_level_return_data=r.get('low_level_return_data'),low_level_error=r.get('low_level_error'),intended_amount=a)
  for key in ['source_tokens','recipient_tokens','airdrop_tokens','allowance','airdrop_ether_wei','token_mode']:
   for phase in ['before','after']:row[key+'_'+phase]=r.get(phase,{}).get(key)
  if valid:
   values,app=evaluate(r['before'],r['after'],r['outer_status'],r['outer_return_data'],r['negative'],a)
   lp=r['legitimate_probe'];pv,_=evaluate(lp['before'],lp['after'],lp['outer_status'],lp['outer_return_data'],False,a);probe=pv['I6']
   d=r['after']['recipient_tokens']-r['before']['recipient_tokens'];D=max(0,a-d) if r['outer_status']==1 else 0;spent=r['before']['allowance']-r['after']['allowance'];violations=[k for k in values if app[k] and not values[k]]
  else:d=D=spent=None;violations=None
  row.update(delivered_delta=d,acknowledged_shortfall_token_units=D,shortfall_normalization_denominator=a,normalized_shortfall=str(Fraction(D,a)) if D is not None else None,allowance_consumed=spent,consumed_unfulfilled_entitlement_wei=None,entitlement_metric_status='not_applicable_no_internal_ledger',invariants_applicable=sum(app.values()),invariant_violation_count=len(violations) if violations is not None else None,violated_invariant_ids=violations,legitimate_probe_passed=probe,negative_scenario=r['negative'],negative_security_requirements_satisfied=all(values[k] for k in cfg['negative_requirements']) if valid and r['negative'] else None,error=r.get('error'),raw_evidence_path=r['raw_evidence_path'],observation_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  rows.append(row)
  for k,name in cfg['invariants'].items():
   invariants.append({'contract_id':r['contract_id'],'variant':r['variant'],'scenario':r['scenario'],'run':r['run'],'phase':'primary','invariant_id':k,'name':name,'applicable':app[k],'satisfied':values.get(k) if valid and app[k] else None,'status':'not_applicable' if not app[k] else 'passed' if valid and values[k] else 'violated' if valid else 'inconclusive','raw_evidence_path':r['raw_evidence_path']})
  invariants.append({'contract_id':r['contract_id'],'variant':r['variant'],'scenario':r['scenario'],'run':r['run'],'phase':'legitimate_probe','invariant_id':'I6','name':'legitimate_operation','applicable':True,'satisfied':probe,'status':'passed' if probe is True else 'violated' if probe is False else 'inconclusive','raw_evidence_path':r['raw_evidence_path']})
 writecsv(folder/'behavioral_results.csv',rows);writecsv(folder/'invariant_results.csv',invariants)
 summary={}
 for c in cfg['cases']:
  summary[c['id']]={}
  for v in cfg['variants']:
   vr=[r for r in rows if r['contract_id']==c['id'] and r['variant']==v];negative=[r for r in vr if r['negative_scenario']];complete=[r for r in negative if r['execution_status']=='completed'];num=sum(r['negative_security_requirements_satisfied'] is True for r in complete)
   summary[c['id']][v]={'negative_scenarios_satisfied':num,'negative_scenarios_completed':len(complete),'negative_scenarios_expected':2,'negative_scenarios_excluded_infrastructure':len(negative)-len(complete),'negative_scenario_proportion':str(Fraction(num,len(complete))) if complete else None,'legitimate_probes_passed':sum(r['legitimate_probe_passed'] is True for r in vr),'legitimate_probes_expected':3,'S1_legitimate_passed':next((r['invariant_violation_count']==0 and r['execution_status']=='completed' for r in vr if r['scenario']=='S1'),False),'all_legitimate_functionality_preserved':len(vr)==3 and all(r['legitimate_probe_passed'] is True for r in vr) and all(r['invariant_violation_count']==0 for r in vr if r['scenario']=='S1'),'primary_invariant_violations':sum(r['invariant_violation_count'] or 0 for r in vr),'infrastructure_errors':sum(r['execution_status']!='completed' for r in vr)}
 save(folder/'summary.json',summary);return rows,invariants,summary

def compare(allrows,allinv,summaries):
 comparisons=[]
 for comparator in ['V1','V2']:
  worse=False;better=False;missing=False;funcbad=False;funcgain=False
  for rs in summaries:
   if not rs['V3']['all_legitimate_functionality_preserved'] or not rs[comparator]['all_legitimate_functionality_preserved']:
    funcbad|=not rs['V3']['all_legitimate_functionality_preserved'] and rs[comparator]['all_legitimate_functionality_preserved'];funcgain|=rs['V3']['all_legitimate_functionality_preserved'] and not rs[comparator]['all_legitimate_functionality_preserved']
  indexes={(r['run'],r['variant'],r['scenario']):r for r in allrows}
  evidence=[]
  for rep in sorted({r['run'] for r in allrows}):
   for sid in ['S1','S2','S3']:
    a=indexes.get((rep,'V3',sid));b=indexes.get((rep,comparator,sid))
    if not a or not b or a['execution_status']!='completed' or b['execution_status']!='completed':missing=True;continue
    av={r['invariant_id']:r['satisfied'] for r in allinv if r['run']==rep and r['variant']=='V3' and r['scenario']==sid and r['phase']=='primary' and r['applicable']}
    bv={r['invariant_id']:r['satisfied'] for r in allinv if r['run']==rep and r['variant']==comparator and r['scenario']==sid and r['phase']=='primary' and r['applicable']}
    better_ids=[k for k in av if av[k] and not bv[k]];worse_ids=[k for k in av if not av[k] and bv[k]]
    better|=bool(better_ids);worse|=bool(worse_ids)
    for metric in ['acknowledged_shortfall_token_units']:
     better|=a[metric]<b[metric];worse|=a[metric]>b[metric]
    evidence.append({'run':rep,'scenario':sid,'improved_invariant_ids':better_ids,'regressed_invariant_ids':worse_ids,'V3_shortfall':a['acknowledged_shortfall_token_units'],'comparator_shortfall':b['acknowledged_shortfall_token_units'],'entitlement_metric':'not_applicable'})
  both_normal=all(s['V3']['all_legitimate_functionality_preserved'] and s[comparator]['all_legitimate_functionality_preserved'] for s in summaries)
  label='inconclusive evidence' if missing else 'trade-off' if (funcbad and better) or (better and worse) else 'functional regression' if funcbad else 'inconclusive evidence' if not both_normal else 'additional observed protection' if better and not worse else 'security regression' if worse and not better else 'equal observed protection'
  comparisons.append({'comparison':'V3 vs '+comparator,'classification':label,'all_legitimate_functionality_preserved':both_normal,'matched_evidence':evidence})
 return {'comparisons':comparisons,'additional_benefit_over_both':all(c['classification']=='additional observed protection' for c in comparisons),'scope':'one synthetic-fixture operational case; deterministic repetitions not independent contracts; no PES'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('runs',nargs='+',type=pathlib.Path);ap.add_argument('--comparison-output',type=pathlib.Path,required=True);args=ap.parse_args();allrows=[];allinv=[];summaries=[];reps=[]
 for folder in args.runs:
  rs,inv,s=summarize(folder.resolve());allrows+=rs;allinv+=inv;summaries.append(s);reps.append(rs)
 args.comparison_output.mkdir(parents=True,exist_ok=True);comparisons={};tab=[];repro={}
 for cid in ['UC02','UC03']:
  comparisons[cid]=compare([r for r in allrows if r['contract_id']==cid],[r for r in allinv if r['contract_id']==cid],[s[cid] for s in summaries])
  for c in comparisons[cid]['comparisons']:tab.append({'contract_id':cid,'comparison':c['comparison'],'classification':c['classification'],'all_legitimate_functionality_preserved':c['all_legitimate_functionality_preserved'],'additional_benefit_over_both':comparisons[cid]['additional_benefit_over_both']})
  stable=lambda rows:[{k:v for k,v in r.items() if k not in ['run','raw_evidence_path','observation_sha256']} for r in rows if r['contract_id']==cid]
  repro[cid]=len(reps)>1 and all(stable(reps[0])==stable(r) for r in reps[1:])
 save(args.comparison_output/'comparison.json',comparisons);writecsv(args.comparison_output/'comparison.csv',tab)
 save(args.comparison_output/'reproducibility.json',{'clean_process_launches':len(reps),'source_contracts':2,'variant_sources':8,'repetitions_per_source':len(reps),'primary_trials':len(allrows),'legitimate_probes':len(allrows),'behavioral_metrics_identical':repro,'not_independent_contracts':'Deterministic repetitions are reproducibility checks; UC01 not pooled.'})
 print(json.dumps({'comparisons':tab,'reproducibility':repro},indent=2))
if __name__=='__main__':main()
