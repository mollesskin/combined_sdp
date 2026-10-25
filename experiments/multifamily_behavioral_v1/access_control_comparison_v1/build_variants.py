import pathlib,json,hashlib,shutil,difflib,re
R=pathlib.Path.cwd();S=R/'experiments/multifamily_behavioral_v1/access_control_comparison_v1';B=R/'experiments/multifamily_behavioral_v1/stand_reproduction/20261023T024815Z_oJrMgr/project';P=S/'project';P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Read-only snapshot of arithmetic artifacts, not a rerun; no traversal of dependency symlink.
A=S.parent/'arithmetic_comparison_v1'
if not (S/'arithmetic_before.json').exists():(S/'arithmetic_before.json').write_text(json.dumps({str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file()},indent=2))
I=S/'inputs';I.mkdir(exist_ok=True)
for n in ['CONTRACT_MAP_RU.md','contract_review_33.json']:shutil.copyfile('/Users/moldir_2024icloud.com/Downloads/RMT_Source_Review_33/'+n,I/n)
# Working baseline JSON absent: preserve actual vendor saved report and reproduction log separately.
report=S.parent/'vendor/pinned/smartbugs-curated/0.4.x/scripts/test-results.json';shutil.copyfile(report,I/'test-results.json');shutil.copyfile(B.parent/'baseline-tests.log',I/'baseline-tests.log')
j=json.load(open(I/'contract_review_33.json'));r=json.load(open(report));names={x['contractFile'].split('/')[-1] for x in r['passedResults'] if x['contractFile'].startswith('access_control/')};assert len(names)==16
for n in ['package.json','package-lock.json','hardhat.config.js']:shutil.copyfile(B/n,P/n)
if not (P/'node_modules').exists():(P/'node_modules').symlink_to(B/'node_modules',target_is_directory=True)
s=(P/'hardhat.config.js').read_text();s=s[:s.index('  mocha:')]+'  mocha: { reporter: "spec" },\n};\n';(P/'hardhat.config.js').write_text(s)
helper='''\n// AI-assisted local checked subtraction, not a third-party library release.\n// Check the computed modular result before it can be assigned to storage.\nlibrary ResearchDebit {\n function sub(uint a,uint b) internal pure returns(uint) { uint c=a-b; require(c<=a); return c; }\n}\n'''
models={
'FibonacciBalance.sol':('unresolved','Library pointer and exact Fibonacci payout','Public withdraw; fallback explicitly permits library calls; no owner role','No resolved policy for setStart or allowed selectors; isolated computation changes shared-library workflow/storage layout. Need exact sequence and permitted fallback API before architecture comparison.'),
'proxy.sol':('unresolved','Owner/storage and ETH under delegatecall','Constructor sets owner; public forwarding has no explicit target domain','No trusted target set or delegated-user policy specified; benign function in attack fixture cannot define a production trust policy. Do not invent allowlist to force A+B.'),
'arbitrary_location_write_simple.sol':('factorial','owner slot1 and bounded dynamic array','Any user may push/pop/update valid index; only deployer may Destroy','A nonempty pre-guard; B post-result checked subtraction; V3 both. Existing update bound and Destroy owner check retained.'),
'wallet_04_confused_sign.sol':('factorial','Deposit credit and ETH entitlement','Each depositor may withdraw 0..credit; creator may migrate all funds','A replaces reversed >= with <=; B checked debit only, preserving reversed guard. V2 inherits rejection of partial/zero-with-credit withdrawals. V3 expected to restore domain via A, not independent synergy.'),
'mapping_write.sol':('single','owner slot0 integrity; arbitrary uint256 key/value storage','Public set/get arbitrary keys; withdraw restricted to owner, which remains zero/uninitialized','Replace dynamic array with mapping; remove length manipulation only. No key cap or owner initialization. Artificial funding 1 wei disclosed; absent-key get now returns zero instead of possible OOB revert (interface same, behavior extension).'),
'multiowned_vulnerable.sol':('single','Owner-parent tree and funds','Root and delegated owners may add; parent/root may revoke according to existing rule; owners may withdraw','Apply existing onlyOwner to newOwner; no new two-step grant workflow. Existing deleteOwner and withdraw guards retained.'),
'mycontract.sol':('single','Owner-authorized outgoing ETH','Deployment owner may directly sendTo any receiver; intermediary does not inherit authority from tx.origin','Replace tx.origin with msg.sender. Prefund future CREATE address as author test, not artificial owner initialization.'),
'phishable.sol':('single','Owner-authorized outgoing ETH','Constructor-designated owner may directly withdraw to arbitrary receiver; phishing intermediary unauthorized','Replace tx.origin with msg.sender; payable fallback retained; no recipient allowlist.'),
'parity_wallet_bug_2.sol':('single','First initialization authority, owner set and wallet funds','Scoped to author-tested standalone WalletLibrary: deployer initializes; existing owners act under original threshold/daily limit','Single missing-authority fix on all 3 init entrypoints; existing only_uninitialized retained. Append private deploymentAuthority after original fields; no storage shift. This is not a proxy-compatible library fix or historical deployment reconstruction.'),
'simple_suicide.sol':('single','Lifecycle code and ETH under Shanghai','Author functional test designates deployer as owner; infer deployer-only lifecycle authority for this standalone fixture','Add private deployment owner and guard. New authority is an explicit experimental model inferred from functional test, absent in source; no second lifecycle requirement. No-argument ABI used, correcting author JS extra argument only in new measurements.'),
'unprotected0.sol':('single','Owner slot0','Current owner may transfer ownership to any chosen address; outsiders may not','Use existing onlyowner on changeOwner; no acceptance phase or zero-address restriction introduced.'),
'wallet_02_refund_nosub.sol':('single','Per-user claim and ETH accounting','Any depositor may withdraw/refund own credit; creator migration remains allowed','Set credit zero before refund transfer (accounting/CEI fix); allow zero refund as harmless no-effect success; sequential repeats must not pay again; no mutex/owner restriction.'),
'wallet_03_wrong_constructor.sol':('single','Creator slot0 and migration authority','Deployer is creator at construction; each depositor withdraws own credit; only creator migrates','Replace initWallet with constructor, remove runtime init selector. This is a lifecycle/API correction, not comparison of artificial post-deploy guards.')}
for idx,fn in enumerate(['incorrect_constructor_name1.sol','incorrect_constructor_name2.sol','incorrect_constructor_name3.sol']):models[fn]=('single','Owner slot0 and withdrawal authority','Deployer owns at construction; anyone may fund; only owner may withdraw','Replace misnamed initializer with constructor; remove runtime selector. No post-deployment initialization requirement is inferred.')
registry=[]
for c in j['contracts']:
 if c['file'] not in names or c['benchmark_category']!='access_control':continue
 n=c['file'];src=(B/c['source_path']).read_text();assert hashlib.sha256(src.encode()).hexdigest()==c['source_sha256'];assert sha(B/c['test_path'])==c['test_sha256']
 t,asset,roles,decision=models[n];e={'file':n,'source_path':c['source_path'],'test_path':c['test_path'],'source_sha256':c['source_sha256'],'test_sha256':c['test_sha256'],'group':'AC_INIT_CLONE' if n.startswith('incorrect_constructor') else n,'track':t,'protected_asset':asset,'permissions':roles,'decision_and_scope':decision,'author_test_defect':c['observed_subtype'],'review_proposal':c,'variants':{},'existing_mechanisms':{'arbitrary_location_write_simple.sol':['Update bounds guard','Destroy owner guard'],'wallet_04_confused_sign.sol':['Wrong reversed entitlement guard','Creator-only migration','Deposit overflow assertion'],'parity_wallet_bug_2.sol':['only_uninitialized on all init entrypoints','onlyowner','onlymanyowners','daily-limit overflow guard'],'multiowned_vulnerable.sol':['onlyOwner','parent/root deletion rule'],'wallet_02_refund_nosub.sol':['withdraw entitlement','creator-only migration','deposit assertion']}.get(n,['See actual source and permission model; baseline guards retained except declared target'])}
 variants=['V0','V1','V2','V3'] if t=='factorial' else ['V0','F1'] if t=='single' else ['V0']
 for v in variants:
  s=src
  if v!='V0':
   if n=='arbitrary_location_write_simple.sol':
    if v in ['V1','V3']:s=s.replace('require(0 <= bonusCodes.length);','require(0 < bonusCodes.length);')
    if v in ['V2','V3']:s=s.replace('bonusCodes.length--;','bonusCodes.length = ResearchDebit.sub(bonusCodes.length, 1);')+helper
   elif n=='wallet_04_confused_sign.sol':
    if v in ['V1','V3']:s=s.replace('require(amount >= balances[msg.sender]);','require(amount <= balances[msg.sender]);')
    if v in ['V2','V3']:s=s.replace('balances[msg.sender] -= amount;','balances[msg.sender] = ResearchDebit.sub(balances[msg.sender], amount);')+helper
   elif n.startswith('incorrect_constructor'):
    s=re.sub(r'function (IamMissing|missing|Constructor)\(\)', 'constructor()',s)
   elif n=='wallet_03_wrong_constructor.sol':s=s.replace('function initWallet() public','constructor() public')
   elif n=='mapping_write.sol':
    s=s.replace('uint256[] map;','mapping(uint256 => uint256) map;');s=s.replace('         if (map.length <= key) {\n             map.length = key + 1;\n         }\n','')
   elif n=='multiowned_vulnerable.sol':s=s.replace('function newOwner(address _owner) external returns','function newOwner(address _owner) external onlyOwner returns')
   elif n in ['mycontract.sol','phishable.sol']:s=s.replace('require(tx.origin == owner);','require(msg.sender == owner);')
   elif n=='unprotected0.sol':s=s.replace('function changeOwner(address _newOwner)\n         public','function changeOwner(address _newOwner)\n         public onlyowner')
   elif n=='wallet_02_refund_nosub.sol':s=s.replace('msg.sender.transfer(balances[msg.sender]);','uint256 claim = balances[msg.sender];\n         balances[msg.sender] = 0;\n         msg.sender.transfer(claim);')
   elif n=='simple_suicide.sol':s=s.replace('contract SimpleSuicide {','contract SimpleSuicide {\n  address private deploymentOwner;\n  constructor() public { deploymentOwner = msg.sender; }').replace('function sudicideAnyone() {','function sudicideAnyone() {\n    require(msg.sender == deploymentOwner);')
   elif n=='parity_wallet_bug_2.sol':
    s=s.replace('contract WalletLibrary is WalletEvents {','contract WalletLibrary is WalletEvents {\n  constructor() public { deploymentAuthority = msg.sender; }\n  modifier onlyDeploymentAuthority { require(msg.sender == deploymentAuthority); _; }')
    s=s.replace(') only_uninitialized {',') only_uninitialized onlyDeploymentAuthority {') # only init functions; modifier definition contains no this substring
    pos=s.rfind('}');s=s[:pos]+'  address private deploymentAuthority; // appended to preserve existing field slots\n'+s[pos:]
   else:raise Exception(n)
  dest=P/'contracts'/v/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s)
  d=S/'diffs'/n;d.mkdir(parents=True,exist_ok=True);(d/(v+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile='V0/'+n,tofile=v+'/'+n)))
  e['variants'][v]={'path':str(dest.relative_to(S)),'sha256':sha(dest)}
 # Preserve original test as evidence only; never execute author's vulnerable expectations against fixes.
 dest=I/'author_tests'/pathlib.Path(c['test_path']).name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(B/c['test_path'],dest)
 registry.append(e)
assert len(registry)==16
(S/'registry.json').write_text(json.dumps({'RQ':'How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?','report_provenance':str(report.relative_to(R)),'report_note':'Working baseline scripts/test-results.json absent at inspection; saved pinned report lists 16 AC files. Actual 33-file reproduction supported separately by saved baseline-tests.log, not new protected results.','cases':registry},ensure_ascii=False,indent=2))
# Generator saved in stage; invoke from repository root.
