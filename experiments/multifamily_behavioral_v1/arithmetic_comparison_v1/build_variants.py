import pathlib,json,hashlib,shutil,difflib
root=pathlib.Path.cwd(); out=root/'experiments/multifamily_behavioral_v1/arithmetic_comparison_v1'; base=root/'experiments/multifamily_behavioral_v1/stand_reproduction/20261023T024815Z_oJrMgr/project'
review=json.load(open('/Users/moldir_2024icloud.com/Downloads/RMT_Source_Review_33/contract_review_33.json'))
(out/'review_inputs').mkdir(exist_ok=True)
for n in ['IMPLEMENTATION_BRIEF_RU.md','CONTRACT_MAP_RU.md','contract_review_33.json']: shutil.copyfile('/Users/moldir_2024icloud.com/Downloads/RMT_Source_Review_33/'+n,out/'review_inputs'/n)
p=out/'project';p.mkdir(exist_ok=True)
for n in ['package.json','package-lock.json','hardhat.config.js']:shutil.copyfile(base/n,p/n)
if not (p/'node_modules').exists(): (p/'node_modules').symlink_to(base/'node_modules',target_is_directory=True)
# Config explicit changes: remove author reporter; paths are new project defaults. Compiler and network settings unchanged.
s=(p/'hardhat.config.js').read_text();s=s[:s.index('  mocha:')]+ '  mocha: { reporter: "spec" },\n};\n';(p/'hardhat.config.js').write_text(s)
helper='''\n// AI-assisted experimental checked arithmetic; not an original SafeMath release.\n// Post-result add/mul checks follow the idiom in this dataset's BECToken SafeMath.\nlibrary ResearchChecked {\n function add(uint a,uint b) internal pure returns(uint) { uint c=a+b; require(c>=a); return c; }\n function sub(uint a,uint b) internal pure returns(uint) { require(b<=a); return a-b; }\n function mul(uint a,uint b) internal pure returns(uint) { uint c=a*b; require(a==0 || c/a==b); return c; }\n}\n'''
# exact statement, operands, operator, replacement template
spec={
'BECToken.sol':[('uint256 amount = uint256(cnt) * _value;','uint256(cnt)','_value','mul','uint256 amount = {e};')],
'integer_overflow_1.sol':[('sellerBalance += value;','sellerBalance','value','add','sellerBalance = {e};')],
'integer_overflow_add.sol':[('count += input;','count','input','add','count = {e};')],
'overflow_simple_add.sol':[('balance += deposit;','balance','deposit','add','balance = {e};')],
'integer_overflow_minimal.sol':[('count -= input;','count','input','sub','count = {e};')],
'integer_overflow_mul.sol':[('count *= input;','count','input','mul','count = {e};')],
'integer_overflow_multitx_multifunc_feasible.sol':[('count -= input;','count','input','sub','count = {e};')],
'integer_overflow_multitx_onefunc_feasible.sol':[('count -= input;','count','input','sub','count = {e};')],
'integer_overflow_mapping_sym_1.sol':[('map[k] -= v;','map[k]','v','sub','map[k] = {e};')],
'overflow_single_tx.sol':[(f'count {sym}= input;','count','input',op,'count = {e};') for sym,op in [('+','add'),('*','mul'),('-','sub')]],
'timelock.sol':[('lockTime[msg.sender] += _secondsToIncrease;','lockTime[msg.sender]','_secondsToIncrease','add','lockTime[msg.sender] = {e};')],
 'token.sol':[
 ('require(balances[msg.sender] - _value >= 0);','balances[msg.sender]','_value','sub','require({e} >= 0);'),
 ('balances[msg.sender] -= _value;','balances[msg.sender]','_value','sub','balances[msg.sender] = {e};'),
 ('balances[_to] += _value;','balances[_to]','_value','add','balances[_to] = {e};')],
 'tokensalechallenge.sol':[
 ('require(msg.value == numTokens * PRICE_PER_TOKEN);','numTokens','PRICE_PER_TOKEN','mul','require(msg.value == {e});'),
 ('balanceOf[msg.sender] += numTokens;','balanceOf[msg.sender]','numTokens','add','balanceOf[msg.sender] = {e};'),
 ('balanceOf[msg.sender] -= numTokens;','balanceOf[msg.sender]','numTokens','sub','balanceOf[msg.sender] = {e};'),
 ('msg.sender.transfer(numTokens * PRICE_PER_TOKEN);','numTokens','PRICE_PER_TOKEN','mul','msg.sender.transfer({e});')]
}
registry=[]
for c in review['contracts']:
 if c['benchmark_category']!='arithmetic':continue
 name=c['file'];src=(base/c['source_path']).read_text();assert hashlib.sha256(src.encode()).hexdigest()==c['source_sha256']
 entry=dict(c);entry.update(targets=[dict(statement=t[0],left=t[1],right=t[2],operator=t[3]) for t in spec[name]],variants={},group='AR_ADDER_CLONE' if name in ['integer_overflow_add.sol','overflow_simple_add.sol'] else name)
 for v in range(4):
  text=src
  if v:
   for old,a,b,op,template in spec[name]:
    assert text.count(old)>=1
    expr=f'{a} '+{'add':'+','sub':'-','mul':'*'}[op]+f' {b}'
    if v in [1,3]:expr=f'ResearchChecked.{op}({a}, {b})'
    guard={'add':f'{b} <= uint256(-1) - {a}','sub':f'{b} <= {a}','mul':f'{a} == 0 || {b} <= uint256(-1) / {a}'}[op]
    text=text.replace(old,('require('+guard+');\n        ' if v in [2,3] else '')+template.format(e=expr),1)
   text+=helper if v in [1,3] else ''
  dest=p/'contracts'/f'V{v}'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
  d=out/'diffs'/name;d.mkdir(parents=True,exist_ok=True)
  (d/f'V{v}.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),text.splitlines(True),fromfile='V0/'+name,tofile=f'V{v}/'+name)))
  entry['variants'][f'V{v}']={'path':str(dest.relative_to(out)),'sha256':hashlib.sha256(text.encode()).hexdigest()}
 registry.append(entry)
(out/'registry.json').write_text(json.dumps({'RQ':review['approved_RQ_unchanged'],'clone_groups':review['clone_groups'],'cases':registry},ensure_ascii=False,indent=2))
# This generator is saved in the stage directory; invoke from repository root.
