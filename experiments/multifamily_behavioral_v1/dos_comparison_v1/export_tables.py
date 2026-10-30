"""Readable, derived tables from raw DoS measurements. No new execution or scores."""
import pathlib,json,csv,argparse
S=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,default=S);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
run=a.run or S/json.loads((S/'evaluation_paths.json').read_text())['run1'];ops=json.loads((run/'operations.json').read_text());rows=json.loads((run/'measurements.json').read_text())
def write(n,data):
 cols=list(dict.fromkeys(k for x in data for k in x))
 with (a.output/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in x.items()} for x in data)
arrays=[];auction=[]
for o in ops:
 if 'cleanup_transactions'in o:
  arrays.append({k:o.get(k) for k in ['file','variant','scenario','requested_work','accepted_work','rejected_work','completed_work','capacity_rejected','completion_requested','completion_accepted','full_requested_task_complete','accepted_part_complete','load_transactions','cleanup_transactions','transactions_to_complete','load_gas_used','cleanup_gas_used','total_workflow_gas_used','cleanup_stop_reason']}|{'post_completion_refill_passed':o['post_completion_refill']['correct'] if o.get('post_completion_refill') else None})
 if o['file']=='auction.sol':
  rs=[r for r in rows if all(r[k]==o[k] for k in ['file','variant','scenario'])];paid=0;completion=None
  for i,r in enumerate(rs):
   if r['phase'] in ['higher_bid','refund_recovery']:paid+=int(r.get('paid_old_bidder_wei') or 0)
   if r['actual']['bid']=='20' and paid==10 and all(x=='0' for x in r['actual']['claims'].values()):completion=i+1;break
  auction.append({k:o.get(k) for k in ['file','variant','scenario','higher_bid_accepted','refund_entitlement_after_outbid_wei','refund_paid_before_claim_wei','refund_owed_after_outbid_wei','eventual_refund_paid_wei','baseline_uncompleted_live_bid_wei','claim_failure_rollback','recovery_correct','repeat_claim_no_extra_payout','full_requested_task_complete','workflow_transactions','total_workflow_gas_used']}|{'transactions_until_first_completion_in_trace':completion,'gas_until_first_completion_in_trace':str(sum(int(r['gas_used']) for r in rs[:completion])) if completion else None,'bid_and_claim_phase_transactions':sum(r['phase'] in ['first_bid','higher_bid','refund_recovery'] for r in rs),'gas_bid_and_claim_phases':str(sum(int(r['gas_used']) for r in rs if r['phase'] in ['first_bid','higher_bid','refund_recovery'])),'verification_phase_gas':str(sum(int(r['gas_used']) for r in rs if r['phase'] not in ['first_bid','higher_bid','refund_recovery']))})
write('array_results.csv',arrays);write('auction_results.csv',auction)
write('group_summary.csv',[{'group':c['group'],'files':[c['file']],'track':c['track'],'completed_comparison':True,'independence_claim':False} for c in json.loads((S/'registry.json').read_text())['cases']])
