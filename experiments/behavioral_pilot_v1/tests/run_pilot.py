#!/usr/bin/env python3
"""Only the fixed UC01 in-process behavioral protocol. No security analyzers/network."""
import argparse,csv,datetime,hashlib,importlib.metadata,json,pathlib,platform,subprocess,sys,traceback
from eth_tester import EthereumTester,PyEVMBackend
from eth.vm.forks.byzantium import ByzantiumVM
from web3 import Web3,EthereumTesterProvider
BASE=pathlib.Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
COMPILER=ROOT/'experiments/reentrancy/toolchain/solc-0.4.19'
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
 return {'to':'0x'+bytes(c.msg.storage_address).hex(),'code_address':'0x'+bytes(c.msg.code_address).hex(),'sender':'0x'+bytes(c.msg.sender).hex(),'input':'0x'+bytes(c.msg.data).hex(),'output':'0x'+bytes(c.output).hex(),'is_error':bool(c.is_error),'error':str(c.error) if c.is_error else None,'gas_used':c.get_gas_used(),'children':[computation(x) for x in c.children]}
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
 def state(self,bank,token):
  opts={'from':self.a[0],**self.cfg['tx']};holder=self.a[1]
  return {'bank_tokens':token.functions.balanceOf(bank.address).call(opts),'holder_tokens':token.functions.balanceOf(holder).call(opts),'entitlement_wei':bank.functions.Holders(holder).call(opts),'bank_ether_wei':self.w.eth.get_balance(bank.address),'allowance_holder_bank':token.functions.allowance(holder,bank.address).call(opts),'token_mode':token.functions.mode().call(opts),'min_deposit_wei':bank.functions.MinDeposit().call(opts)}
def children_to(node,address):
 result=[]
 for c in node.get('children',[]):
  if c['code_address'].lower()==address.lower():result.append(c)
  result+=children_to(c,address)
 return result

def compile_one(out,name,path,contract):
 folder=out/'raw/compile'/name;folder.mkdir(parents=True,exist_ok=True)
 cmd=[str(COMPILER),'--combined-json','abi,bin',str(path)];event={'command':cmd,'cwd':str(folder),'source':str(path),'source_sha256':sha(path),'compiler_sha256':sha(COMPILER),'timeout_seconds':60,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  p=subprocess.run(cmd,cwd=folder,capture_output=True,text=True,timeout=60)
  (folder/'stdout.txt').write_text(p.stdout);(folder/'stderr.txt').write_text(p.stderr);event.update(exit_code=p.returncode,status='compiled' if p.returncode==0 else 'failed')
  if p.returncode:raise RuntimeError('Compilation failure: '+name)
  data=json.loads(p.stdout)['contracts'];c=next(v for k,v in data.items() if k.rsplit(':',1)[-1]==contract);c['abi']=json.loads(c['abi']) if isinstance(c['abi'],str) else c['abi'];return c
 except Exception:
  event['error']=traceback.format_exc();event['status']='failed';raise
 finally:
  event['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(folder/'execution.json',event)

def trial(out,variant,scenario,rep,compiled,fixture,cfg):
 folder=out/'raw/trials'/variant/scenario['id'];folder.mkdir(parents=True,exist_ok=False)
 record={'contract_id':'UC01','variant':variant,'scenario':scenario['id'],'run':rep,'negative':scenario['negative'],'compilation_status':'compiled','deployment_status':'not_started','setup_status':'not_started','execution_status':'not_started','error':None,'raw_evidence_path':str(folder.relative_to(BASE))}
 try:
  c=Chain(folder,cfg);bank=c.deploy('01_deploy_bank',compiled);token=c.deploy('02_deploy_fixture',fixture);record['deployment_status']='deployed'
  record['actors']={'owner':c.a[0],'holder':c.a[1],'bank':bank.address,'token':token.address}
  for name,fn,sender,value in [('03_init',bank.functions.initTokenBank(),0,0),('04_mint',token.functions.mint(bank.address,cfg['initial_bank_tokens']),0,0),('05_deposit',bank.functions.Deposit(),1,cfg['deposit_wei'])]:
   receipt,_=c.tx(name,fn,sender,value)
   if receipt.status!=1:raise RuntimeError('Setup transaction reverted: '+name)
  initial=c.state(bank,token)
  expected={'bank_tokens':cfg['initial_bank_tokens'],'holder_tokens':cfg['initial_holder_tokens'],'entitlement_wei':cfg['deposit_wei'],'bank_ether_wei':cfg['deposit_wei'],'allowance_holder_bank':0,'token_mode':0,'min_deposit_wei':10**18}
  record['setup_checks']={k:initial[k]==v for k,v in expected.items()};record['initial_state']=initial
  if not all(record['setup_checks'].values()):raise RuntimeError('Setup state mismatch')
  record['setup_status']='passed';snapshot=c.t.take_snapshot()
  operation=lambda:bank.functions.WitdrawTokenToHolder(c.a[1],token.address,cfg['amount'])
  before=c.state(bank,token);receipt,raw=c.tx('06_legitimate_probe',operation());after=c.state(bank,token)
  record['legitimate_probe']={'outer_status':receipt.status,'before':before,'after':after,'raw_transaction':'06_legitimate_probe.json'}
  c.t.revert_to_snapshot(snapshot);restored=c.state(bank,token);record['snapshot_restored']=restored==initial
  if not record['snapshot_restored']:raise RuntimeError('Snapshot did not restore initial state')
  receipt,_=c.tx('07_set_scenario_mode',token.functions.setMode(scenario['mode']))
  if receipt.status!=1:raise RuntimeError('Fixture mode transaction failed')
  before=c.state(bank,token)
  if any(before[k]!=initial[k] for k in initial if k!='token_mode') or before['token_mode']!=scenario['mode']:raise RuntimeError('Scenario initial state mismatch')
  receipt,raw=c.tx('08_primary_operation',operation());after=c.state(bank,token)
  calls=children_to(raw['computation'],token.address)
  if len(calls)!=1:raise RuntimeError('Expected exactly one observed token CALL; got '+str(len(calls)))
  call=calls[0]
  record.update(before=before,after=after,outer_status=int(receipt.status),outer_gas_used=int(receipt.gasUsed),low_level_status=not call['is_error'],low_level_return_data=call['output'],low_level_error=call['error'],low_level_observation='actual PyEVM CALL child computation; CALL success follows child is_error; no contract instrumentation',execution_status='completed')
 except Exception:
  record['execution_status']='infrastructure_error';record['error']=traceback.format_exc();save(folder/'infrastructure_error.json',{'traceback':record['error']})
 finally:save(folder/'observation.json',record)
 return record

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=pathlib.Path,required=True);ap.add_argument('--repetition',type=int,choices=[1,2],required=True);args=ap.parse_args()
 verify_lock('protocol.lock.json');verify_lock('execution.lock.json')
 manifest=json.loads((BASE/'source_manifest.json').read_text());assert sha(ROOT/manifest['original_source'])==manifest['original_sha256']
 for v,r in manifest['variants'].items():assert sha(ROOT/r['path'])==r['sha256']
 assert (BASE/'variants/V0/TokenBank.sol').read_bytes()==(ROOT/manifest['original_source']).read_bytes()
 out=args.output.resolve();assert out.is_relative_to(BASE/'runs');out.mkdir(parents=True,exist_ok=False)
 cfg=json.loads((BASE/'scenario_inputs.json').read_text());save(out/'raw/inputs.json',cfg)
 versions={'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['web3','eth-tester','py-evm','eth-abi']},'compiler_sha256':sha(COMPILER),'protocol_lock_sha256':sha(BASE/'protocol.lock.json'),'execution_lock_sha256':sha(BASE/'execution.lock.json')}
 p=subprocess.run([str(COMPILER),'--version'],capture_output=True,text=True,timeout=20);versions['compiler_version_stdout']=p.stdout;versions['compiler_version_stderr']=p.stderr;versions['compiler_version_exit_code']=p.returncode
 if p.returncode or 'Version: 0.4.19+' not in p.stdout:raise RuntimeError('Compiler identity mismatch')
 save(out/'raw/versions.json',versions)
 freeze=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True,timeout=60)
 (out/'raw/requirements.txt').write_text(freeze.stdout);(out/'raw/requirements.stderr.txt').write_text(freeze.stderr)
 save(out/'raw/command.json',{'argv':[sys.executable,*sys.argv],'cwd':str(pathlib.Path.cwd()),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'network':'in-process only','repetition':args.repetition,'pip_freeze_exit_code':freeze.returncode})
 compiled={};compile_errors={}
 for v in cfg['variants']:
  try:compiled[v]=compile_one(out,v,BASE/'variants'/v/'TokenBank.sol','TokenBank')
  except Exception:compile_errors[v]=traceback.format_exc()
 try:fixture=compile_one(out,'fixture',BASE/'fixtures/BehaviorToken.sol','BehaviorToken')
 except Exception:
  save(out/'raw/fatal_error.json',{'stage':'fixture_compilation','error':traceback.format_exc()});raise
 abi_results={v:json.dumps(c['abi'],sort_keys=True)==json.dumps(compiled.get('V0',{}).get('abi'),sort_keys=True) for v,c in compiled.items()};save(out/'raw/abi_comparison.json',{'matches_V0':abi_results,'scope':'full canonical ABI; not behavioral equivalence','compile_errors':compile_errors})
 records=[];blocked=False
 for v in cfg['variants']:
  for s in cfg['scenarios']:
   if v not in compiled or not abi_results.get(v) or blocked:
    reason=compile_errors.get(v) or ('stopped_after_setup_failure' if blocked else 'ABI mismatch')
    folder=out/'raw/trials'/v/s['id'];record={'contract_id':'UC01','variant':v,'scenario':s['id'],'run':args.repetition,'negative':s['negative'],'compilation_status':'failed' if v not in compiled else 'compiled','deployment_status':'not_started','setup_status':'not_started','execution_status':'infrastructure_error','error':reason,'raw_evidence_path':str(folder.relative_to(BASE))};save(folder/'observation.json',record)
   else:
    record=trial(out,v,s,args.repetition,compiled[v],fixture,cfg)
    if record['setup_status']!='passed':blocked=True
   records.append(record)
 save(out/'raw/execution_summary.json',{'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_trials':len(records),'infrastructure_errors':sum(r['execution_status']!='completed' for r in records),'new_analyzer_runs':0,'new_PES_values':0})
 print(str(out))
 if any(r['execution_status']!='completed' for r in records):return 1
 return 0
if __name__=='__main__':sys.exit(main())
