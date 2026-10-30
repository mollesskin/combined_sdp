import pathlib,json,hashlib,shutil,difflib
R=pathlib.Path.cwd();S=R/'experiments/multifamily_behavioral_v1/dos_comparison_v1';P=S/'project';B=S.parent/'stand_reproduction/20261023T024815Z_oJrMgr/project';P.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not (S/'previous_stages_before.json').exists():
 (S/'previous_stages_before.json').write_text(json.dumps({name:{str(p.relative_to(S.parent/name)):sha(p) for p in (S.parent/name).rglob('*') if p.is_file()} for name in ['arithmetic_comparison_v1','access_control_comparison_v1']},indent=2))
I=S/'inputs';I.mkdir(exist_ok=True)
for n in ['CONTRACT_MAP_RU.md','contract_review_33.json']:shutil.copyfile('/Users/moldir_2024icloud.com/Downloads/RMT_Source_Review_33/'+n,I/n)
shutil.copyfile(B.parent/'baseline-tests.log',I/'baseline-tests.log')
for n in ['package.json','package-lock.json','hardhat.config.js']:shutil.copyfile(B/n,P/n)
if not (P/'node_modules').exists():(P/'node_modules').symlink_to(B/'node_modules',target_is_directory=True)
s=(P/'hardhat.config.js').read_text();s=s[:s.index('  mocha:')]+'  mocha: { reporter: "spec" },\n};\n';s=s.replace('hardfork: "shanghai",','hardfork: "shanghai",\n      blockGasLimit: 30000000,');(P/'hardhat.config.js').write_text(s)
(S/'config.diff').write_text(''.join(difflib.unified_diff((B/'hardhat.config.js').read_text().splitlines(True),s.splitlines(True),fromfile='baseline/config',tofile='dos/config')))
review=json.load(open(I/'contract_review_33.json'));reg=[]
for c in review['contracts']:
 if c['benchmark_category']!='denial_of_service':continue
 n=c['file'];src=(B/c['source_path']).read_text();assert sha(B/c['source_path'])==c['source_sha256'];assert sha(B/c['test_path'])==c['test_sha256']
 variants=['V0','PULL','FALLBACK'] if n=='auction.sol' else ['V0','F1'] if n=='dos_simple.sol' else ['V0','V1','V2','V3']
 e={'file':n,'source_sha256':c['source_sha256'],'test_sha256':c['test_sha256'],'review_proposal':c,'track':'alternatives' if n=='auction.sol' else 'single' if n=='dos_simple.sol' else 'factorial','group':n,'variants':{},'requirement':{'auction.sol':'Accept strictly higher bids despite receiver refusal; preserve former bidder refund entitlement until payout; multiple claim tx permitted; current bid remains held. No batching.','dos_address.sol':'Public append 350 caller addresses per request; explicit cleanup after length>1500 intentionally deletes all accepted records, ends length0/win true; multiple cleanup calls permitted and admission paused during cleanup.','dos_number.sol':'Public insertion and explicit physical clearDOS after numElements>1500; end numElements=array.length=0 with accepted values intact until requested deletion. Preserve separate logical clear() reuse semantics. Multiple cleanup tx permitted.','dos_simple.sol':'Original fill350 while length<1500, then clear cycle; after cleanup length0 and next fill350 works. Existing maximum1750 retained; multiple cleanup calls allowed, false return means cleanup phase, not necessarily completion.'}[n]}
 for v in variants:
  text=src
  if n=='auction.sol' and v!='V0':
   old='require(currentFrontrunner.send(currentBid));'
   text=text.replace(old,'refunds[currentFrontrunner] += currentBid;' if v=='PULL' else 'if (!currentFrontrunner.send(currentBid)) {\n        refunds[currentFrontrunner] += currentBid;\n      }')
   text=text.replace('contract DosAuction {','contract DosAuction {\n  mapping(address => uint) public refunds;\n  // AI-assisted refund workflow; account-specific claim, CEI with atomic revert.\n  function withdrawRefund(address recipient) public {\n    uint amount = refunds[msg.sender];\n    refunds[msg.sender] = 0;\n    recipient.transfer(amount);\n  }')
   # Append mapping AFTER original fields, preserving source storage slots0/1.
   text=text.replace('  mapping(address => uint) public refunds;\n','')
   pos=text.rfind('}');text=text[:pos]+'  mapping(address => uint) public refunds;\n'+text[pos:]
  if n=='dos_address.sol':
   if v in ['V1','V3']:
    text=text.replace('bool win = false;','bool win = false;\n    bool public clearing = false;')
    text=text.replace('if(creditorAddresses.length>1500) {\n            creditorAddresses = new address[](0);\n            win = true;\n        }','''if (!clearing) {
            if (creditorAddresses.length <= 1500) return;
            clearing = true;
        }
        uint work = creditorAddresses.length > 350 ? 350 : creditorAddresses.length;
        creditorAddresses.length -= work;
        if (creditorAddresses.length == 0) {
            win = true;
            clearing = false;
        }''')
    text=text.replace('function addCreditors() public returns (bool) {','function addCreditors() public returns (bool) {\n        require(!clearing);')
   if v in ['V2','V3']:text=text.replace('for(uint i=0;i<350;i++) {','require(creditorAddresses.length <= 1750 - 350);\n        for(uint i=0;i<350;i++) {')
  if n=='dos_number.sol':
   if v in ['V1','V3']:
    text=text.replace('uint[] array;','uint[] array;\n    bool public clearing = false;')
    text=text.replace('function insertNnumbers(uint value,uint numbers) public {','function insertNnumbers(uint value,uint numbers) public {\n        require(!clearing);')
    text=text.replace('function clear() public {','function clear() public {\n        require(!clearing);')
    text=text.replace('require(numElements>1500);\n        array = new uint[](0);\n        numElements = 0;','''if (!clearing) {
            require(numElements > 1500);
            clearing = true;
        }
        uint work = array.length > 350 ? 350 : array.length;
        array.length -= work;
        if (numElements > array.length) numElements = array.length;
        if (array.length == 0) {
            numElements = 0;
            clearing = false;
        }''')
   if v in ['V2','V3']:text=text.replace('// Gas DOS if number > 382','require(numElements <= 1750 && numbers <= 1750 - numElements);\n        // Gas DOS if number > 382')
  if n=='dos_simple.sol' and v=='F1':
   text=text.replace('address[] listAddresses;','address[] listAddresses;\n    bool public clearing = false;')
   text=text.replace('if(listAddresses.length<1500) {','if(listAddresses.length<1500 && !clearing) {')
   text=text.replace('listAddresses = new address[](0);','''clearing = true;
            uint work = listAddresses.length > 350 ? 350 : listAddresses.length;
            listAddresses.length -= work;
            if (listAddresses.length == 0) clearing = false;''')
  dest=P/'contracts'/v/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
  d=S/'diffs'/n;d.mkdir(parents=True,exist_ok=True);(d/(v+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),text.splitlines(True),fromfile='V0/'+n,tofile=v+'/'+n)))
  e['variants'][v]={'path':str(dest.relative_to(S)),'sha256':sha(dest)}
 shutil.copyfile(B/c['test_path'],I/pathlib.Path(c['test_path']).name);reg.append(e)
(S/'registry.json').write_text(json.dumps({'RQ':'How effective are combinations of security design patterns compared with their individual components in preventing vulnerabilities in Ethereum smart contracts?','AI_assisted':True,'cases':reg,'clone_groups_note':'No clone groups for these four files specified in existing review; four singleton groups do not prove independence.'},ensure_ascii=False,indent=2))
