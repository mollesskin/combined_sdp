import csv,json,hashlib,subprocess,io,zipfile,collections,datetime,pathlib,openpyxl
O=pathlib.Path(__file__).parent
ROOT=O.parent
repo=ROOT/'combined_sdp'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
commit=git('rev-parse','origin/main').decode().strip()
def write(name,rows,fields=None):
 rows=list(rows)
 with open(O/name,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def val(v):return v.isoformat(sep=' ') if isinstance(v,datetime.datetime) else (v.isoformat() if isinstance(v,datetime.date) else v)
w=openpyxl.load_workbook(ROOT/'upload/Контактная информация (Ответы) (3).xlsx',data_only=True)
a=list(w.active.values);headers=list(a[0]);headers[1]='respondent_id';rows=[]
for i,row in enumerate(a[1:],1):
 d=dict(zip(headers,map(val,row)));d['respondent_id']=f'P{i}';rows.append(d)
write('survey_raw_anonymised.csv',rows)
processed=[]
for d in rows:
 t=d.copy();t['role_group']=str(d[headers[3]]).strip().lower().replace(' ','_');t['effectiveness_rating_numeric']=int(d[headers[10]]);processed.append(t)
write('survey_processed.csv',processed)
write('survey_cleaning_log.csv',[
 {'date':'2026-10-31','operation':'Replace direct identifiers','rule':'Replace Name with P1–P3 in original worksheet row order; no public name-to-code key','records_affected':3},
 {'date':'2026-10-31','operation':'Serialize dates','rule':'Excel date/datetime values exported in ISO format; submission timestamp and self-entered date remain separate; no timezone inferred','records_affected':3},
 {'date':'2026-10-31','operation':'Add analysis fields','rule':'Preserve original responses; add role_group and integer effectiveness_rating_numeric','records_affected':3},
 {'date':'2026-10-31','operation':'Retain ambiguous experience and pattern answers','rule':'Do not infer experience units or silently split the combined pattern answer','records_affected':0},
 {'date':'2026-10-31','operation':'Missing values and duplicates','rule':'No imputation or deletion; counts in survey_quality.csv','records_affected':0}])
write('survey_quality.csv',[{'variable':k,'valid':sum(d[k] is not None and str(d[k]).strip()!='' for d in rows),'missing':sum(d[k] is None or str(d[k]).strip()=='' for d in rows)} for k in headers])
sources=list(csv.DictReader(open(ROOT/'appendix_output/Appendix_A_source_index.csv',encoding='utf-8-sig')))
obs=list(csv.DictReader(open(ROOT/'appendix_output/Appendix_A_all_observations.csv',encoding='utf-8-sig')))
zpath='experiments/multifamily_behavioral_v1/dos_comparison_v1/runs.zip'; z=zipfile.ZipFile(io.BytesIO(git('show',commit+':'+zpath)))
for s in sources:
 path=s['public_url'].split('/blob/')[1].split('/',1)[1] if s['public_url'] else s['source_path'].replace('exp/','experiments/',1);member=''
 if s['family']=='denial_of_service':
  suffix=path.split('/dos_comparison_v1/')[1];matches=[n for n in z.namelist() if n.endswith(suffix)];assert len(matches)==1,(suffix,matches);member=matches[0];b=z.read(member);path=zpath
 else:b=git('show',commit+':'+path)
 s['archive_member']=member;s['verified_commit']=commit;s['hash_matches']=str(hashlib.sha256(b).hexdigest()==s['sha256']).lower();assert s['hash_matches']=='true',s['source_id']
 s['public_url']='https://github.com/mollesskin/combined_sdp/blob/'+commit+'/'+path;s['publication_status']='SHA-256 verified archive member' if member else 'SHA-256 verified public file'
 s['indexed_records']=sum(r['source_id']==s['source_id'] for r in obs);assert s['indexed_records']==int(s['source_rows'])
write('Appendix_A_source_index_verified.csv',sources)
lookup={s['source_id']:s for s in sources}
for r in obs:r['public_url']=lookup[r['source_id']]['public_url'];r['archive_member']=lookup[r['source_id']]['archive_member']
write('Appendix_A_all_observations_verified.csv',obs)
# Explicit boolean failures are counted only where the relevant instrument reports true/false.
def boolean(x):
 t=str(x).lower();return True if t=='true' else False if t=='false' else None
checks={'access_control':['security_pass','functionality_pass'],'arithmetic':['correct','allowed_operation_passed'],'unchecked_calls':['negative_security_requirements_satisfied','legitimate_probe_passed'],'reentrancy':['security_properties_satisfied','permitted_operation_satisfied'],'denial_of_service':['full_requested_task_complete']}
summary=collections.defaultdict(lambda:[0,0]);failures=[];statuses=collections.Counter()
for r in obs:
 d=json.loads(r['original_fields_json']);sid=r['source_id'];src=lookup[sid]
 for k in ['compilation_status','deployment_status','setup_status','execution_status','error_timeout_status']:
  if k in d:statuses[(sid,r['classification'],k,str(d[k]))]+=1
 if r['classification']!='primary behavioral':continue
 keys=checks.get(r['family'],[])
 if sid in ['S35','S36']:
  if d['scenario']=='nested':d['excess_payout_absent']=int(d['attackerReceived'])<=10**18;keys=['excess_payout_absent']
  elif d['scenario']=='rejectedCallback':d['failed_send_credit_retained']=int(d['recipientCreditAfter'])==10**18;keys=['failed_send_credit_retained']
  else:keys=[]
 for k in keys:
  v=boolean(d.get(k))
  if v is None:continue
  key=(sid,r['family'],r['run_id'],r['variant'],k);summary[key][0]+=1
  if not v:
   summary[key][1]+=1;failures.append({**{a:r[a] for a in ['source_id','source_record','family','run_id','contract','variant','scenario','step']},'failed_check':k,'public_url':r['public_url'],'archive_member':r['archive_member']})
write('technical_failure_summary.csv',[dict(zip(['source_id','family','run_id','variant','check'],key),applicable_observations=v[0],failed_observations=v[1],passed_observations=v[0]-v[1]) for key,v in summary.items()])
write('technical_failure_records.csv',failures)
write('technical_status_counts.csv',[dict(source_id=k[0],classification=k[1],field=k[2],recorded_value=k[3],count=v) for k,v in statuses.items()])
# Inventory of candidate run result files, excluding redundant raw transactions and derived summaries.
paths=git('ls-tree','-r','--name-only',commit).decode().splitlines();selected={s['public_url'].split('/blob/')[1].split('/',1)[1] for s in sources}
candidates=[p for p in paths if '/runs/' in p and p.endswith(('/measurements.csv','/behavioral_results.csv','/invariant_results.csv','/results.csv','/compilation.csv','/operations.csv','/status_history.csv'))]
write('run_inventory_comparison.csv',[{'repository_path':p,'included_in_source_index':p in selected} for p in candidates])
notes=f'''EVIDENCE AUDIT — 31 October 2026
Repository snapshot: {commit}

Survey: 3 responses, 14 original columns. Name replaced by respondent_id in worksheet order. The processed copy preserves all source answers and adds two analysis columns. No answers were imputed, removed or silently recoded. Exact dates and free-text answers remain; these files are de-identified rather than a guarantee against re-identification. Do not publish a name-to-code key. The numeric scale is 1–5; this export does not establish its original verbal labels.

Run register: all {len(sources)} indexed source files were matched by SHA-256 to the repository snapshot, including 9 files inside the public DoS runs.zip archive. All {len(obs)} indexed observation rows reconcile with their source counts. These are heterogeneous records, NOT {len(obs)} independent trials. The archive_member column identifies the exact file inside an archive. Publication-pending wording for these DoS sources is outdated.

The run_inventory_comparison.csv additionally lists candidate run-level result files found in the snapshot. A false inclusion flag must be resolved before claiming that the appendix covers every experiment ever executed. This audit confirms the indexed evidence, not unrecorded runs or every claim in the latest Word report.

Failure definitions: technical_failure_summary.csv counts explicit false values among explicit true/false values, separately for each instrument field, run and variant. technical_failure_records.csv identifies each corresponding source record. A false result can describe an insecure baseline, a functionality failure or a workload shortfall; it is not automatically an instrumentation error. Different checks may overlap on the same observation. Do not sum these counts as independent failures or contracts. For arithmetic, correct covers both allowed and adversarial observations; allowed_operation_passed is a separate, potentially overlapping field. For DoS, full_requested_task_complete measures requested-work completion and does not alone distinguish protective rejection from execution failure.

SimpleDAO uses explicit derived rules: nested payout must not exceed the 1 ETH entitlement; the rejected-payment scenario must preserve 1 ETH recipient credit. The underlying original numeric fields remain in the observation register. Other scenarios are not assigned invented pass/fail values.

technical_status_counts.csv reports recorded execution/compilation/setup statuses for all indexed sources, including development and static-tool runs. A reverted transaction is NOT automatically an error: intended rejection can be a successful security outcome. Missing status fields are unavailable, not zero errors. Invariant-detail rows and status-history rows are retained as supporting observations, not added again to scenario-level failure counts.

Reproduction: build_evidence.py reads the supplied Excel, existing Appendix A CSVs and the locally fetched repository snapshot. Source paths are relative to the task workspace. No new experiment was executed.

Publication: these newly generated files have not been committed or pushed to GitHub. Suggested repository folder: docs/en/evidence_update/. Table 2 should link survey_processed.csv and survey_cleaning_log.csv after upload. Appendix A should use the verified source index and observation register; Table 6 should link the failure summary, individual records and status counts. Do not mark exhaustive experiment coverage complete while inventory exclusions remain unexplained.
'''
(O/'README.txt').write_text(notes)
print('sources',len(sources),'observations',len(obs),'failure entries',len(failures),'candidate exclusions',[p for p in candidates if p not in selected])
print('fail totals',collections.Counter(x['failed_check'] for x in failures))
