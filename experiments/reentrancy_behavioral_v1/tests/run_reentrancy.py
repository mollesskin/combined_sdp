#!/usr/bin/env python3
"""Only the fixed three existing reentrancy sources, in-process behavioral protocol. No security analyzers/network."""
import argparse,csv,datetime,hashlib,importlib.metadata,json,pathlib,platform,subprocess,sys,traceback
from eth_tester import EthereumTester,PyEVMBackend
from eth.vm.forks.byzantium import ByzantiumVM
from web3 import Web3,EthereumTesterProvider
BASE=pathlib.Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(x):
 if isinstance(x,(bytes,bytearray,memoryview)):return '0x'+bytes(x).hex()
 if isinstance(x,dict) or hasattr(x,'items'):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [clean(v) for v in x]
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 return str(x)
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),indent=2,sort_keys=True)+'\n')
def verify_lock(name):
 lock=json.loads((BASE/name).read_text())
 for f,h in lock['sha256'].items():
  if sha(BASE/f)!=h:raise RuntimeError('Frozen file drift: '+f)
def computation(c):
 return {'to':'0x'+bytes(c.msg.storage_address).hex(),'code_address':'0x'+bytes(c.msg.code_address).hex(),'sender':'0x'+bytes(c.msg.sender).hex(),'input':'0x'+bytes(c.msg.data).hex(),'output':'0x'+bytes(c.output).hex(),'is_error':bool(c.is_error),'error':str(c.error) if c.is_error else None,'gas_used':c.get_gas_used(),'value':int(c.msg.value),'children':[computation(x) for x in c.children]}
class Chain:
 def __init__(self,out,cfg):
  self.out=out;self.cfg=cfg;self.backend=PyEVMBackend(genesis_parameters=cfg['genesis'],vm_configuration=((0,ByzantiumVM),))
  self.t=EthereumTester(backend=self.backend);self.w=Web3(EthereumTesterProvider(self.t));self.a=self.w.eth.accounts;self.last=None
  original=self.backend.chain.apply_transaction
  def capture(tx):
   result=original(tx);self.last=computation(result[2]);return result
  self.backend.chain.apply_transaction=capture
 def tx(self,name,fn,sender=0,value=0):
  self.last=None;opts={'from':self.a[sender],'value':value,**self.cfg['tx']}
  try:
   h=fn.transact(opts);receipt=self.w.eth.wait_for_transaction_receipt(h)
   raw={'name':name,'options':opts,'transaction':clean(self.w.eth.get_transaction(h)),'receipt':clean(receipt),'computation':self.last,'block_timestamp':self.w.eth.get_block(receipt.blockNumber).timestamp}
   save(self.out/(name+'.json'),raw)
   if self.last is None:raise RuntimeError('Missing actual PyEVM computation')
   return receipt,raw
  except Exception:
   save(self.out/(name+'.error.json'),{'traceback':traceback.format_exc(),'options':opts,'captured_computation':self.last});raise
 def deploy(self,name,compiled):
  c=self.w.eth.contract(abi=compiled['abi'],bytecode=compiled['bin']);receipt,raw=self.tx(name,c.constructor())
  if receipt.status!=1:raise RuntimeError('Deployment reverted: '+name)
  return self.w.eth.contract(address=receipt.contractAddress,abi=compiled['abi'])
 def state(self,bank,receiver,case,variant):
  shift=int(variant in ['V2','V3']);opts={'from':self.a[0],**self.cfg['tx']};raw={}
  def word(slot,label):
   v=self.w.eth.get_storage_at(bank.address,slot);raw[label]={'slot':hex(slot),'word':'0x'+bytes(v).hex()};return int.from_bytes(v,'big')
  def credit(address,slot,label):
   key=int.from_bytes(Web3.keccak(bytes.fromhex(address[2:]).rjust(32,b'\0')+slot.to_bytes(32,'big')),'big');return word(key,label)
  slot=case['credit_slot_base']+shift
  actor=credit(receiver.address,slot,'actor_credit');other=credit(self.a[1],slot,'other_credit')
  agg=word(case['aggregate_slot_base']+shift,'aggregate') if case['aggregate_slot_base'] is not None else None
  timestamp=credit(receiver.address,case['time_slot_base']+shift,'last_withdraw') if case['time_slot_base'] is not None else None
  lock=word(0,'guard') if shift else None;getter_match=None
  if case['id']=='RE01':getter_match=(bank.functions.balances(receiver.address).call(opts)==actor and bank.functions.balances(self.a[1]).call(opts)==other and bank.functions.lastWithdrawTime(receiver.address).call(opts)==timestamp and bank.functions.withdrawalLimit().call(opts)==self.cfg['unit_wei'])
  elif case['id']=='RE03':getter_match=(bank.functions.getBalance(receiver.address).call(opts)==actor and bank.functions.getBalance(self.a[1]).call(opts)==other)
  return {'bank_ether_wei':self.w.eth.get_balance(bank.address),'receiver_ether_wei':self.w.eth.get_balance(receiver.address),'actor_credit_wei':actor,'other_credit_wei':other,'aggregate_wei':agg,'last_withdraw_time':timestamp,'guard_entered':lock,'callbacks':receiver.functions.callbacks().call(opts),'public_getter_matches_storage':getter_match,'storage_words':raw}
def children_to(node,address):
 result=[]
 for c in node.get('children',[]):
  if c['code_address'].lower()==address.lower():result.append(c)
  result+=children_to(c,address)
 return result

def compile_one(out,name,path,contract,compiler):
 folder=out/'raw/compile'/name;folder.mkdir(parents=True,exist_ok=True)
 cmd=[str(compiler),'--combined-json','abi,bin',str(path)];event={'command':cmd,'cwd':str(folder),'source':str(path),'source_sha256':sha(path),'compiler_sha256':sha(compiler),'timeout_seconds':60,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  p=subprocess.run(cmd,cwd=folder,capture_output=True,text=True,timeout=60)
  (folder/'stdout.txt').write_text(p.stdout);(folder/'stderr.txt').write_text(p.stderr);event.update(exit_code=p.returncode,status='compiled' if p.returncode==0 else 'failed')
  if p.returncode:raise RuntimeError('Compilation failure: '+name)
  data=json.loads(p.stdout)['contracts'];c=next(v for k,v in data.items() if k.rsplit(':',1)[-1]==contract);c['abi']=json.loads(c['abi']) if isinstance(c['abi'],str) else c['abi'];return c
 except Exception:
  event['error']=traceback.format_exc();event['status']='failed';raise
 finally:
  event['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(folder/'execution.json',event)

def trial(out,case,variant,scenario,rep,compiled,fixture,cfg):
 folder=out/'raw/trials'/case['id']/variant/scenario;folder.mkdir(parents=True,exist_ok=False)
 record={'contract_id':case['id'],'variant':variant,'scenario':scenario,'run':rep,'compilation_status':'compiled','deployment_status':'not_started','setup_status':'not_started','execution_status':'not_started','error':None,'steps':[],'raw_evidence_path':str(folder.relative_to(BASE))}
 try:
  c=Chain(folder,cfg);bank=c.deploy('01_deploy_bank',compiled);receiver=c.deploy('02_deploy_receiver',fixture);record['deployment_status']='deployed';U=cfg['unit_wei']
  record['actors']={'controller':c.a[0],'other_depositor':c.a[1],'bank':bank.address,'receiver':receiver.address}
  def state():return c.state(bank,receiver,case,variant)
  def require_tx(name,fn,sender=0,value=0):
   receipt,raw=c.tx(name,fn,sender,value)
   if receipt.status!=1:raise RuntimeError('Setup/allowed intermediate transaction failed: '+name)
   return receipt,raw
  require_tx('03_configure_receiver',receiver.functions.configure(bank.address,Web3.keccak(text=case['withdraw_selector'])[:4],U,scenario=='F1',scenario=='S1'))
  require_tx('04_other_deposit',getattr(bank.functions,case['deposit_function'])(),sender=1,value=2*U)
  actor_initial=2*U if scenario=='O1' and case['id']=='RE01' else U
  require_tx('05_actor_deposit',receiver.functions.fund(Web3.keccak(text=case['deposit_selector'])[:4]),value=actor_initial)
  initial=state();record['initial_state']=initial
  checks={'bank_funding':initial['bank_ether_wei']==2*U+actor_initial,'receiver_funding':initial['receiver_ether_wei']==0,'actor_credit':initial['actor_credit_wei']==actor_initial,'other_credit':initial['other_credit_wei']==2*U,'getter_match':initial['public_getter_matches_storage'] is not False,'aggregate':initial['aggregate_wei'] is None or initial['aggregate_wei']==2*U+actor_initial,'guard_clear':initial['guard_entered'] in [None,0],'timestamp':initial['last_withdraw_time'] in [None,0]}
  record['setup_checks']=checks
  if not all(checks.values()):raise RuntimeError('Storage/funding/setup checks failed')
  record['setup_status']='passed'
  def withdraw(label,intended_rejection=False):
   before=state();receipt,raw=c.tx(label,receiver.functions.withdraw());after=state();calls=children_to(raw['computation'],bank.address)
   selected=[x for x in calls if x['input'].startswith('0x'+Web3.keccak(text=case['withdraw_selector'])[:4].hex())]
   if not selected:raise RuntimeError('No actual bank withdrawal computation')
   if scenario=='S1' and len(selected)!=2:raise RuntimeError('Bounded one-retry fixture did not produce exactly two bank attempts')
   observation={'step':label,'intended_rejection':intended_rejection,'before':before,'after':after,'outer_status':int(receipt.status),'outer_error':raw['computation']['error'],'outer_gas_used':int(receipt.gasUsed),'block_timestamp':raw['block_timestamp'],'authorized_amount_wei':U,'bank_withdrawal_calls':selected,'nested_attempts':[{'status':not x['is_error'],'value':x['value'],'output':x['output'],'error':x['error']} for x in selected[1:]],'raw_transaction':label+'.json'}
   record['steps'].append(observation)
   if before['public_getter_matches_storage'] is False or after['public_getter_matches_storage'] is False:raise RuntimeError('Storage/getter observation mismatch')
  if scenario=='O1':
   withdraw('06_first_withdraw')
   if case['id']=='RE01':
    t=c.w.eth.get_block('latest').timestamp+604801;c.t.time_travel(t);save(folder/'07_time_advance.json',{'requested_timestamp':t,'actual_latest_timestamp':c.w.eth.get_block('latest').timestamp})
   else:
    require_tx('07_actor_redeposit',receiver.functions.fund(Web3.keccak(text=case['deposit_selector'])[:4]),value=U)
    s=state()
    if s['actor_credit_wei']!=U:raise RuntimeError('Redeposit did not restore legitimate credit')
   withdraw('08_second_withdraw')
  elif scenario=='F1':
   withdraw('06_rejected_withdraw',True)
   require_tx('07_allow_receiver',receiver.functions.configure(bank.address,Web3.keccak(text=case['withdraw_selector'])[:4],U,False,False))
   withdraw('08_recovery_withdraw')
  else:withdraw('06_bounded_reentry')
  record['execution_status']='completed'
 except Exception:
  record['execution_status']='infrastructure_error';record['error']=traceback.format_exc();save(folder/'infrastructure_error.json',{'traceback':record['error']})
 finally:save(folder/'observation.json',record)
 return record

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=pathlib.Path,required=True);ap.add_argument('--repetition',type=int,choices=[1,2],required=True);a=ap.parse_args()
 verify_lock('protocol.lock.json');verify_lock('execution.lock.json');cfg=json.loads((BASE/'scenario_inputs.json').read_text())
 for case in cfg['cases']:
  for v,s in case['sources'].items():assert sha(ROOT/s['path'])==s['sha256']
  assert (ROOT/case['sources']['V0']['path']).read_bytes()==(ROOT/'dataset/reentrancy'/case['filename']).read_bytes()
 out=a.output.resolve();assert out.is_relative_to(BASE/'runs');out.mkdir(parents=True,exist_ok=False);save(out/'raw/inputs.json',cfg)
 save(out/'raw/command.json',{'argv':[sys.executable,*sys.argv],'cwd':str(pathlib.Path.cwd()),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repetition':a.repetition,'network':'in-process only; no static tools/PES'})
 versions={'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['web3','eth-tester','py-evm','eth-abi']},'protocol_lock_sha256':sha(BASE/'protocol.lock.json'),'execution_lock_sha256':sha(BASE/'execution.lock.json'),'compilers':{}}
 freeze=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True,timeout=60);(out/'raw/requirements.txt').write_text(freeze.stdout);(out/'raw/requirements.stderr.txt').write_text(freeze.stderr)
 def compiler(version):
  old=ROOT/'experiments/reentrancy/toolchain'/('solc-'+version);p=old if old.is_file() else ROOT/'experiments/multi_vulnerability/design_v1/toolchain'/('solc-'+version)
  probe=subprocess.run([str(p),'--version'],capture_output=True,text=True,timeout=20);versions['compilers'][version]={'path':str(p),'sha256':sha(p),'stdout':probe.stdout,'stderr':probe.stderr,'exit_code':probe.returncode};save(out/'raw/versions.json',versions)
  if probe.returncode or 'Version: '+version+'+' not in probe.stdout:raise RuntimeError('Compiler identity mismatch')
  return p
 try:fixture=compile_one(out,'fixture',BASE/'fixtures/LocalRecipient.sol','LocalRecipient',compiler(cfg['fixture_compiler']))
 except Exception:save(out/'raw/fatal_error.json',{'stage':'fixture_compile','error':traceback.format_exc()});raise
 records=[];abi_all={}
 for case in cfg['cases']:
  compiled={};errors={};cid=case['id']
  try:binary=compiler(case['compiler'])
  except Exception:binary=None;errors['compiler']=traceback.format_exc()
  if binary:
   for v,s in case['sources'].items():
    try:compiled[v]=compile_one(out,cid+'_'+v,ROOT/s['path'],case['contract'],binary)
    except Exception:errors[v]=traceback.format_exc()
  abi={v:json.dumps(x['abi'],sort_keys=True)==json.dumps(compiled.get('V0',{}).get('abi'),sort_keys=True) for v,x in compiled.items()};abi_all[cid]={'matches_V0':abi,'compile_errors':errors};blocked=False
  for v in cfg['variants']:
   for scenario in cfg['scenarios']:
    if v not in compiled or not abi.get(v) or blocked:
     folder=out/'raw/trials'/cid/v/scenario;record={'contract_id':cid,'variant':v,'scenario':scenario,'run':a.repetition,'compilation_status':'failed' if v not in compiled else 'compiled','deployment_status':'not_started','setup_status':'not_started','execution_status':'infrastructure_error','error':errors.get(v) or errors.get('compiler') or ('blocked_after_setup_failure' if blocked else 'ABI mismatch'),'steps':[],'raw_evidence_path':str(folder.relative_to(BASE))};save(folder/'observation.json',record)
    else:
     record=trial(out,case,v,scenario,a.repetition,compiled[v],fixture,cfg)
     if record['setup_status']!='passed':blocked=True
    records.append(record)
 save(out/'raw/abi_comparison.json',abi_all);save(out/'raw/execution_summary.json',{'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_contracts':3,'variant_sources':12,'scenario_trials':len(records),'observed_withdrawal_steps':sum(len(r['steps']) for r in records),'infrastructure_errors':sum(r['execution_status']!='completed' for r in records),'static_tool_runs':0,'PES_values':0})
 print(str(out));return int(any(r['execution_status']!='completed' for r in records))
if __name__=='__main__':sys.exit(main())
