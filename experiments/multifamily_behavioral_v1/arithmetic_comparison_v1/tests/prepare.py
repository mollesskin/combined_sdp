#!/usr/bin/env python3
"""Deterministic source transformations and scenario registry; no EVM execution."""
from pathlib import Path
import json,hashlib,difflib,shutil,datetime
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[2]
STAND=ROOT/'experiments/multifamily_behavioral_v1/stand_reproduction/20261023T024815Z_oJrMgr/project'
helper='''\n// AI-assisted experimental helper; not a verbatim external SafeMath library.\nlibrary ArithmeticChecks {\n    function add(uint256 a, uint256 b) internal pure returns (uint256) {\n        uint256 c = a + b; require(c >= a); return c;\n    }\n    function sub(uint256 a, uint256 b) internal pure returns (uint256) {\n        uint256 c = a - b; require(c <= a); return c;\n    }\n    function mul(uint256 a, uint256 b) internal pure returns (uint256) {\n        uint256 c = a * b; require(a == 0 || c / a == b); return c;\n    }\n}\n'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply(s,old,new,n=1):
 assert s.count(old)==n,(old,s.count(old));return s.replace(old,new)
def transform(s,file,A,B):
 def op(old,lhs,operator,rhs):
  nonlocal s
  symbol={'add':'+','sub':'-','mul':'*'}[operator]
  guard={'add':f'{rhs} <= uint256(-1) - {lhs}','sub':f'{rhs} <= {lhs}','mul':f'{lhs} == 0 || {rhs} <= uint256(-1) / {lhs}'}[operator]
  expr=f'ArithmeticChecks.{operator}({lhs}, {rhs})' if A else f'{lhs} {symbol} {rhs}'
  new=(f'require({guard});\n        ' if B else '')+f'{lhs} = {expr};'
  s=apply(s,old,new)
 if file=='BECToken.sol':
  expr='SafeMath.mul(uint256(cnt), _value)' if A else 'uint256(cnt) * _value'
  s=apply(s,'uint256 amount = uint256(cnt) * _value;',('require(_value == 0 || uint256(cnt) <= uint256(-1) / _value);\n    ' if B else '')+'uint256 amount = '+expr+';');return s
 if file=='integer_overflow_1.sol':op('sellerBalance += value;','sellerBalance','add','value')
 elif file=='overflow_simple_add.sol':op('balance += deposit;','balance','add','deposit')
 elif file in ['integer_overflow_add.sol','integer_overflow_mul.sol','integer_overflow_minimal.sol','integer_overflow_multitx_multifunc_feasible.sol','integer_overflow_multitx_onefunc_feasible.sol']:
  typ='add' if file=='integer_overflow_add.sol' else 'mul' if file=='integer_overflow_mul.sol' else 'sub';sy={'add':'+','mul':'*','sub':'-'}[typ];op(f'count {sy}= input;','count',typ,'input')
 elif file=='integer_overflow_mapping_sym_1.sol':op('map[k] -= v;','map[k]','sub','v')
 elif file=='overflow_single_tx.sol':
  for typ,sy in [('add','+'),('mul','*'),('sub','-')]:op(f'count {sy}= input;','count',typ,'input')
 elif file=='timelock.sol':op('lockTime[msg.sender] += _secondsToIncrease;','lockTime[msg.sender]','add','_secondsToIncrease')
 elif file=='token.sol':
  s=apply(s,'require(balances[msg.sender] - _value >= 0);',('require(_value <= balances[msg.sender]);\n     ' if B else '')+('require(ArithmeticChecks.sub(balances[msg.sender], _value) >= 0);' if A else 'require(balances[msg.sender] - _value >= 0);'))
  op('balances[msg.sender] -= _value;','balances[msg.sender]','sub','_value');op('balances[_to] += _value;','balances[_to]','add','_value')
 elif file=='tokensalechallenge.sol':
  if B:
   s=apply(s,'require(msg.value == numTokens * PRICE_PER_TOKEN);','require(numTokens == 0 || PRICE_PER_TOKEN <= uint256(-1) / numTokens);\n        require(msg.value == numTokens * PRICE_PER_TOKEN);')
   s=apply(s,'msg.sender.transfer(numTokens * PRICE_PER_TOKEN);','require(numTokens == 0 || PRICE_PER_TOKEN <= uint256(-1) / numTokens);\n        msg.sender.transfer(numTokens * PRICE_PER_TOKEN);')
  if A:s=apply(s,'numTokens * PRICE_PER_TOKEN','ArithmeticChecks.mul(numTokens, PRICE_PER_TOKEN)',2)
  op('balanceOf[msg.sender] += numTokens;','balanceOf[msg.sender]','add','numTokens')
  # B debit already enforced by retained original require(balanceOf[msg.sender] >= numTokens).
  s=apply(s,'balanceOf[msg.sender] -= numTokens;','balanceOf[msg.sender] = ArithmeticChecks.sub(balanceOf[msg.sender], numTokens);' if A else 'balanceOf[msg.sender] -= numTokens;')
 else:raise ValueError(file)
 return s+(helper if A else '')
def sc(id,kind='valid',**kw):return {'id':id,'kind':kind,**kw}
def scenarios(file):
 if file=='BECToken.sol':return [sc('normal_two',recipients=['alice','bob'],value='1'),sc('duplicate_recipient',recipients=['alice','alice'],value='1'),sc('self_and_other',recipients=['owner','alice'],value='1'),sc('unsafe_published_mul','unsafe',recipients=['alice','zero'],value='POW255'),sc('existing_zero_rejection','existing_rejection',recipients=['alice'],value='0')]
 if file=='integer_overflow_1.sol':return [sc('zero',input='0'),sc('normal',input='1'),sc('max_valid',input='MAX'),sc('unsafe_second_add','unsafe',setup=['addMAX'],input='1')]
 if file in ['integer_overflow_add.sol','overflow_simple_add.sol']:return [sc('zero',input='0'),sc('normal',input='1'),sc('max_valid',input='MAX_MINUS1'),sc('unsafe_wrap','unsafe',input='MAX')]
 if file=='integer_overflow_mapping_sym_1.sol':return [sc('zero_key0',key='0',input='0'),sc('zero_keyMAX',key='MAX',input='0'),sc('unsafe_one','unsafe',key='0',input='1'),sc('unsafe_max','unsafe',key='0',input='MAX')]
 if file=='integer_overflow_mul.sol':return [sc('zero',input='0'),sc('normal',input='2'),sc('largest_valid',input='HALF'),sc('unsafe_wrap','unsafe',input='POW255')]
 if file in ['integer_overflow_minimal.sol','integer_overflow_multitx_multifunc_feasible.sol','integer_overflow_multitx_onefunc_feasible.sol']:
  ss=[sc('zero',input='0'),sc('depletion',input='1'),sc('unsafe_underflow','unsafe',input='2')]
  if 'multitx' in file:ss.insert(0,sc('uninitialized_path',input='2',early=True))
  return ss
 if file=='overflow_single_tx.sol':return [sc('normal_add',op='overflowaddtostate',math='add',input='1'),sc('unsafe_add','unsafe',op='overflowaddtostate',math='add',input='MAX'),sc('normal_mul',op='overflowmultostate',math='mul',input='2'),sc('unsafe_mul_sequence','unsafe',op='overflowmultostate',math='mul',setup=['mulPOW255'],input='2'),sc('depletion',op='underflowtostate',math='sub',input='1'),sc('unsafe_sub','unsafe',op='underflowtostate',math='sub',input='2')]
 if file=='timelock.sol':return [sc('zero',input='0'),sc('normal_matured',input='1',followup='matured_withdraw'),sc('unsafe_exact_wrap','unsafe',input='LOCK_WRAP',followup='immediate_withdraw'),sc('unsafe_max','unsafe',input='MAX')]
 if file=='token.sol':return [sc('normal',value='1',to='alice'),sc('zero',value='0',to='alice'),sc('self',value='1',to='owner'),sc('self_max',supply='MAX',value='MAX',to='owner'),sc('unsafe_owner','unsafe',value='2',to='alice'),sc('unsafe_outsider','unsafe',sender='alice',value='1',to='bob'),sc('unsafe_self','unsafe',value='2',to='owner')]
 if file=='tokensalechallenge.sol':return [sc('zero_buy',op='buy',input='0',value='0'),sc('normal_buy',op='buy',input='1',value='ETHER'),sc('normal_roundtrip',op='sell',input='1',setup=['buy1']),sc('zero_sell',op='sell',input='0'),sc('over_entitlement_sell','existing_rejection',op='sell',input='1'),sc('unsafe_published_buy','unsafe',op='buy',input='POW238',value='0',followup='sell1')]
 raise ValueError(file)
def main():
 rows=json.loads((BASE/'registry/cases.json').read_text());out=[]
 for r in rows:
  s=Path(r['baseline_source']).read_text();r['scenarios']=scenarios(r['file']);r['variants']={}
  for v,A,B in [('V0',False,False),('V1',True,False),('V2',False,True),('V3',True,True)]:
   p=BASE/'project/contracts/conditions'/v/r['file'];p.parent.mkdir(parents=True,exist_ok=True)
   if v=='V0':p.write_bytes(Path(r['baseline_source']).read_bytes())
   else:p.write_text(transform(s,r['file'],A,B))
   r['variants'][v]={'source':str(p.relative_to(BASE/'project')),'sha256':sha(p)}
   copy=BASE/'variants'/r['id']/v/r['file'];copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy)
   if v!='V0':(BASE/'diffs'/(r['id']+'_'+v+'.patch')).write_text(''.join(difflib.unified_diff(s.splitlines(True),p.read_text().splitlines(True),fromfile=r['id']+'/V0/'+r['file'],tofile=r['id']+'/'+v+'/'+r['file'])))
  out.append(r)
 (BASE/'registry/cases_precomparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 for name in ['hardhat.config.js','package.json','package-lock.json']:shutil.copyfile(STAND/name,BASE/'project'/name)
 shutil.copytree(STAND/'scripts',BASE/'project/scripts',dirs_exist_ok=True)
 # A dependency link is read-only reuse, not a new install or a modified dependency set.
 target=BASE/'project/node_modules'
 if not target.exists():target.symlink_to(STAND.resolve()/'node_modules',target_is_directory=True)
 (BASE/'scenarios.json').write_text(json.dumps({r['id']:r['scenarios'] for r in out},indent=2)+'\n')
 print('Prepared',len(out),'files,',len(out)*4,'variant sources,',sum(len(r['scenarios']) for r in out),'scenarios per arm')
if __name__=='__main__':main()
