const fs=require('fs'),path=require('path');
const {ethers,network,artifacts}=require('hardhat');
const MOD=1n<<256n,MAX=MOD-1n,Z=ethers.ZeroAddress;
const S=path.resolve(__dirname,'..'),OUT=path.resolve(process.env.OUTPUT_DIR||'../runs/unset');
if(fs.existsSync(OUT))throw Error('Refuse to overwrite output: '+OUT);fs.mkdirSync(OUT,{recursive:true});
const cases=JSON.parse(fs.readFileSync(path.join(S,'registry.json'))).cases;
const json=x=>JSON.stringify(x,(_,v)=>typeof v==='bigint'?v.toString():v,2);
const hashSlot=(key,base)=>ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(['uint256','uint256'],[key,base]));
const arrBase=base=>BigInt(ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(['uint256'],[base])));
const collision=(MOD-arrBase(1n))%MOD,bonusCollision=(1n+MOD-arrBase(0n))%MOD;
const fnNames={'incorrect_constructor_name1.sol':'IamMissing','incorrect_constructor_name2.sol':'missing','incorrect_constructor_name3.sol':'Constructor','wallet_03_wrong_constructor.sol':'initWallet'};
const contractNames={'arbitrary_location_write_simple.sol':'Wallet','wallet_04_confused_sign.sol':'Wallet','mapping_write.sol':'Map','multiowned_vulnerable.sol':'TestContract','mycontract.sol':'MyContract','phishable.sol':'Phishable','parity_wallet_bug_2.sol':'WalletLibrary','simple_suicide.sol':'SimpleSuicide','unprotected0.sol':'Unprotected','wallet_02_refund_nosub.sol':'Wallet','wallet_03_wrong_constructor.sol':'Wallet','incorrect_constructor_name1.sol':'Missing','incorrect_constructor_name2.sol':'Missing','incorrect_constructor_name3.sol':'Missing'};
const rows=[],abis=[],settings=[],scenarioManifest=[];
function plans(file,a,b,c){
 const t=(method,args=[],sender=0,kind='allowed',effect='same',value=0n)=>({method,args,sender,kind,effect,value});
 if(file==='arbitrary_location_write_simple.sol')return [
  ['ordinary',[t('PushBonusCode',[7n],1,'allowed','push'),t('UpdateBonusCodeAt',[0n,9n],2,'allowed','update'),t('PopBonusCode',[],1,'allowed','pop'),t('UpdateBonusCodeAt',[0n,1n],1,'forbidden'),t('Destroy',[],1,'forbidden')]],
  ['empty_pop_takeover',[t('PopBonusCode',[],1,'forbidden'),t('UpdateBonusCodeAt',[bonusCollision,BigInt(b)],1,'forbidden'),t('Destroy',[],1,'forbidden')]],['owner_destroy',[t('Destroy',[],0,'allowed','destroy')]]];
 if(fnNames[file]){
  const init=fnNames[file],wallet=file.startsWith('wallet');
  return [
   ['deployment_authority',[t('$deployment',[],0,'allowed','deployment')]],
   ['legitimate',wallet?[t('deposit',[],1,'allowed','deposit',10n),t('withdraw',[4n],1,'allowed','withdraw'),t('migrateTo',[c],0,'allowed','migrate')]:[t('$fund',[],1,'allowed','fund',10n),t('withdraw',[],0,'allowed','all')]],
   ['takeover',[...(wallet?[t('deposit',[],0,'allowed','deposit',10n)]:[t('$fund',[],0,'allowed','fund',10n)]),t(init,[],1,'forbidden'),t(wallet?'migrateTo':'withdraw',wallet?[c]:[],1,'forbidden')]],
   ['repeat_initializer',[t(init,[],0,'forbidden'),t(init,[],1,'forbidden')]]];
 }
 if(file==='wallet_04_confused_sign.sol')return [
  ['allowed_partial',[t('deposit',[],1,'allowed','deposit',10n),t('withdraw',[0n],1,'allowed','withdraw'),t('withdraw',[4n],1,'allowed','withdraw')]],
  ['allowed_full',[t('deposit',[],1,'allowed','deposit',10n),t('withdraw',[10n],1,'allowed','withdraw')]],
  ['excess',[t('deposit',[],0,'allowed','deposit',100n),t('deposit',[],1,'allowed','deposit',10n),t('withdraw',[11n],1,'forbidden')]],
  ['no_credit',[t('deposit',[],0,'allowed','deposit',100n),t('withdraw',[1n],1,'forbidden')]],
  ['migration',[t('deposit',[],1,'allowed','deposit',10n),t('migrateTo',[c],1,'forbidden'),t('migrateTo',[c],0,'allowed','migrate')]]];
 if(file==='wallet_02_refund_nosub.sol')return [
  ['normal_refund',[t('deposit',[],0,'allowed','deposit',100n),t('deposit',[],1,'allowed','deposit',10n),t('withdraw',[4n],1,'allowed','withdraw'),t('refund',[],1,'allowed','refund'),t('refund',[],1,'allowed','refund'),t('deposit',[],1,'allowed','deposit',3n),t('refund',[],1,'allowed','refund')]],
  ['rejecting_receiver',[t('deposit',[],0,'allowed','deposit',10n),{...t('refund',[],0,'must_revert'),via:'rejector'}]],
  ['migration',[t('deposit',[],1,'allowed','deposit',10n),t('migrateTo',[c],1,'forbidden'),t('migrateTo',[c],0,'allowed','migrate')]]];
 if(file==='mapping_write.sol')return [
  ['normal_keys',[t('set',[1n,7n],1,'allowed','map_set'),t('set',[1n,9n],2,'allowed','map_set'),t('set',[1n<<255n,MAX],1,'allowed','map_set'),t('set',[MAX,13n],1,'allowed','map_set')]],
  ['owner_collision',[t('set',[collision,BigInt(b)],1,'allowed','map_set'),t('withdraw',[],1,'forbidden')]]];
 if(file==='multiowned_vulnerable.sol')return [
  ['delegation',[t('$fund',[],2,'allowed','fund',10n),t('newOwner',[b],0,'allowed','grant'),t('newOwner',[c],1,'allowed','grant'),t('deleteOwner',[c],1,'allowed','revoke'),t('deleteOwner',[b],0,'allowed','revoke'),t('withdrawAll',[],1,'forbidden'),t('withdrawAll',[],0,'allowed','all')]],
  ['self_grant',[t('$fund',[],0,'allowed','fund',10n),t('newOwner',[b],1,'forbidden'),t('withdrawAll',[],1,'forbidden')]],
  ['delegated_withdraw',[t('$fund',[],0,'allowed','fund',10n),t('newOwner',[b],0,'allowed','grant'),t('withdrawAll',[],1,'allowed','all')]]];
 if(['mycontract.sol','phishable.sol'].includes(file)){
  const method=file==='mycontract.sol'?'sendTo':'withdrawAll',args=file==='mycontract.sol'?[c,4n]:[c];
  return [['direct_owner',[t(method,args,0,'allowed',file==='mycontract.sol'?'send':'recipient_all')]],['direct_outsider',[t(method,args,1,'forbidden')]],['origin_phishing',[{...t(method,args,0,'forbidden'),via:'relay'}]]];
 }
 if(file==='unprotected0.sol')return [['outsider',[t('changeOwner',[b],1,'forbidden')]],['normal_transfer',[t('changeOwner',[b],0,'allowed','owner'),t('changeOwner',[c],0,'forbidden'),t('changeOwner',[c],1,'allowed','owner')]]];
 if(file==='simple_suicide.sol')return [['outsider',[t('sudicideAnyone',[],1,'forbidden')]],['owner',[t('sudicideAnyone',[],0,'allowed','destroy')]]];
 if(file==='parity_wallet_bug_2.sol')return [
  ['legitimate',[t('initWallet',[[b],1,100n],0,'allowed','parity_init'),t('$fund',[],2,'allowed','fund',10n),t('execute',[c,4n,'0x'],0,'allowed','parity_pay'),t('execute',[c,1n,'0x'],2,'forbidden'),t('initWallet',[[c],1,1n],0,'must_revert'),t('kill',[c],0,'allowed','destroy_to')]],
  ['first_initWallet',[t('$fund',[],0,'allowed','fund',10n),t('initWallet',[[],1,100n],1,'forbidden'),t('kill',[c],1,'forbidden')]],
  ['first_initMultiowned',[t('initMultiowned',[[],1],1,'forbidden')]],
  ['first_initDaylimit',[t('initDaylimit',[777n],1,'forbidden')]],
  ['separate_legitimate',[t('initDaylimit',[100n],0,'allowed','daylimit'),t('initMultiowned',[[b],1],0,'allowed','multiinit')]]];
 throw Error('No plan '+file);
}
async function run(){
 for(const item of cases){
  const file=item.file;if(item.track==='unresolved')continue;
  const baseline=await artifacts.readArtifact(`contracts/V0/${file}:${contractNames[file]}`);
  for(const v of Object.keys(item.variants)){
   const fq=`contracts/${v}/${file}:${contractNames[file]}`,art=await artifacts.readArtifact(fq),info=await artifacts.getBuildInfo(fq);
   abis.push({file,variant:v,equal_V0:JSON.stringify(art.abi)===JSON.stringify(baseline.abi),baseline:baseline.abi,actual:art.abi});
   settings.push({file,variant:v,solcVersion:info.solcVersion,solcLongVersion:info.solcLongVersion,settings:info.input.settings});
   const preliminary=await ethers.getSigners(),addrs=preliminary.slice(0,3).map(s=>s.address);
   for(const [scenario,steps] of plans(file,...addrs)){
    scenarioManifest.push({file,variant:v,scenario,steps});
    await network.provider.send('hardhat_reset');
    const ss=await ethers.getSigners(),addresses=ss.slice(0,3).map(s=>s.address),[a,b,c]=addresses;
    let contract,relay,rejector;
    const setup={funding:null,deploy_receipt:null};
    try{
     if(['mycontract.sol','simple_suicide.sol'].includes(file)){
      const future=ethers.getCreateAddress({from:a,nonce:(await ss[0].getNonce())+1});
      const tx=await ss[0].sendTransaction({to:future,value:10n});await tx.wait();setup.funding={method:'prefund_future_CREATE',address:future,value_wei:10n,hash:tx.hash};
     }
     const F=await ethers.getContractFactory(art.abi,art.bytecode,ss[0]);contract=await F.deploy(...(file==='phishable.sol'?[a]:[]));await contract.waitForDeployment();setup.deploy_receipt=(await contract.deploymentTransaction().wait()).toJSON();
     relay=await (await ethers.getContractFactory('ResearchRelay')).deploy();await relay.waitForDeployment();
     rejector=await (await ethers.getContractFactory('ResearchRejector')).deploy();await rejector.waitForDeployment();
     if(file==='mapping_write.sol'){await network.provider.send('hardhat_setBalance',[contract.target,'0x1']);setup.funding={method:'hardhat_setBalance',value_wei:1n};}
     if(['phishable.sol','arbitrary_location_write_simple.sol'].includes(file)){const tx=await ss[0].sendTransaction({to:contract.target,value:10n});await tx.wait();setup.funding={method:'payable_fallback',value_wei:10n,hash:tx.hash};}
     if(file==='wallet_02_refund_nosub.sol'&&scenario==='rejecting_receiver'){
      // Rejector needs a real user claim; relay fixture accepts initial deposit via its caller.
      const data=contract.interface.encodeFunctionData('deposit');
      // ResearchRejector has no payable invocation: fund contract account locally, then impersonate only this fixture for deposit.
      await network.provider.send('hardhat_setBalance',[rejector.target,'0x1000000000000000000']);
      await network.provider.send('hardhat_impersonateAccount',[rejector.target]);
      try{const rs=await ethers.getSigner(rejector.target);await (await contract.connect(rs).deposit({value:5n})).wait();}finally{await network.provider.send('hardhat_stopImpersonatingAccount',[rejector.target]);}
      setup.rejector_claim={value_wei:5n,method:'locally funded fixture impersonation for deposit; real refund uses rejecting contract fallback'};
     }
    }catch(e){rows.push({file,variant:v,scenario,compilation_status:'success',setup_status:'error',execution_status:'missing',error:String(e),correct:null,setup});continue;}
    const accountAddresses=[...addresses,relay.target,rejector.target],accountKeys=['user0','user1','user2','relay','rejector'];
    const rawRead=async pos=>BigInt(await ethers.provider.getStorage(contract.target,pos));
    const ownerAddress=n=>ethers.getAddress(ethers.toBeHex(n&((1n<<160n)-1n),20));
    const isWallet=file.startsWith('wallet_0');
    const mapKeys=[1n,1n<<255n,MAX,collision];
    async function observe(){
     let rawSlots=[0n,1n,2n,3n,4n,5n,6n,7n,8n];
     if(file==='parity_wallet_bug_2.sol')rawSlots.push(261n,262n,263n,264n,265n,...addresses.map(x=>BigInt(hashSlot(BigInt(x),261n))));
     if(isWallet)rawSlots.push(...accountAddresses.map(x=>BigInt(hashSlot(BigInt(x),1n))));
     if(file==='arbitrary_location_write_simple.sol')rawSlots.push(arrBase(0n),arrBase(0n)+1n);
     if(file==='mapping_write.sol')rawSlots.push(...mapKeys.map(k=>v==='V0'?(arrBase(1n)+k)%MOD:BigInt(hashSlot(k,1n))));
     if(file==='multiowned_vulnerable.sol')rawSlots.push(...addresses.map(x=>BigInt(hashSlot(BigInt(x),1n))));
     const vals=await Promise.all(rawSlots.map(rawRead));const storage=Object.fromEntries(rawSlots.map((k,i)=>[k.toString(),vals[i]]));
     const state={contract_wei:await ethers.provider.getBalance(contract.target),code_present:(await ethers.provider.getCode(contract.target))!=='0x'};
     if(file==='arbitrary_location_write_simple.sol'){state.owner=ownerAddress(vals[1]);state.length=vals[0];state.element0=await rawRead(arrBase(0n));}
     else if(file==='mapping_write.sol'){state.owner=ownerAddress(vals[0]);for(let i=0;i<mapKeys.length;i++)state['key'+i]=await rawRead(v==='V0'?(arrBase(1n)+mapKeys[i])%MOD:BigInt(hashSlot(mapKeys[i],1n)));}
     else if(file==='multiowned_vulnerable.sol'){state.root=await contract.root();for(let i=0;i<3;i++)state['parent'+i]=await contract.owners(addresses[i]);}
     else if(file==='parity_wallet_bug_2.sol'&&!state.code_present){Object.assign(state,{required:0n,numOwners:0n,dailyLimit:0n,spentToday:0n,lastDay:0n,isOwner0:false,isOwner1:false,isOwner2:false});}
     else if(file==='parity_wallet_bug_2.sol'){state.required=await contract.m_required();state.numOwners=await contract.m_numOwners();state.dailyLimit=await contract.m_dailyLimit();state.spentToday=await contract.m_spentToday();state.lastDay=await contract.m_lastDay();for(let i=0;i<3;i++)state['isOwner'+i]=await contract.isOwner(addresses[i]);}
     else if(file!=='simple_suicide.sol'){state.owner=ownerAddress(vals[0]);}
     if(isWallet)for(let i=0;i<accountAddresses.length;i++)state['credit'+i]=await rawRead(hashSlot(BigInt(accountAddresses[i]),1n));
     const balances=await Promise.all(accountAddresses.map(x=>ethers.provider.getBalance(x)));
     return {state,storage,accounts:Object.fromEntries(accountKeys.map((k,i)=>[k,balances[i]]))};
    }
    const initial=await observe();const claimLedger=Object.fromEntries(accountAddresses.map((_,i)=>['credit'+i,initial.state['credit'+i]||0n]));
    for(let index=0;index<steps.length;index++){
     const t=steps[index],before=await observe(),expected={...before.state},expectedAccounts={...before.accounts};
     const senderKey='user'+t.sender,receiverKey=t.args[0]===a?'user0':t.args[0]===b?'user1':t.args[0]===c?'user2':null;
     const creditKey='credit'+t.sender;
     function payout(key,amount){expected.contract_wei-=amount;expectedAccounts[key]+=amount;}
     if(t.kind==='allowed'){
      if(t.effect==='deployment')expected.owner=a;
      if(t.effect==='fund'){expected.contract_wei+=t.value;expectedAccounts[senderKey]-=t.value;}
      if(t.effect==='deposit'){claimLedger[creditKey]+=t.value;expected[creditKey]=claimLedger[creditKey];expected.contract_wei+=t.value;expectedAccounts[senderKey]-=t.value;}
      if(t.effect==='withdraw'){claimLedger[creditKey]-=t.args[0];expected[creditKey]=claimLedger[creditKey];payout(senderKey,t.args[0]);}
      if(t.effect==='refund'){payout(senderKey,claimLedger[creditKey]);claimLedger[creditKey]=0n;expected[creditKey]=0n;}
      if(t.effect==='all')payout(senderKey,before.state.contract_wei);
      if(['migrate','recipient_all','destroy_to'].includes(t.effect))payout(receiverKey,before.state.contract_wei);
      if(t.effect==='send')payout(receiverKey,t.args[1]);
      if(t.effect==='destroy'){payout(senderKey,before.state.contract_wei);expected.code_present=false;}
      if(t.effect==='destroy_to')expected.code_present=false;
      if(t.effect==='owner')expected.owner=t.args[0];
      if(t.effect==='grant')expected['parent'+addresses.indexOf(t.args[0])]=addresses[t.sender];
      if(t.effect==='revoke')expected['parent'+addresses.indexOf(t.args[0])]=Z;
      if(t.effect==='push'){expected.length+=1n;if(before.state.length===0n)expected.element0=t.args[0];}
      if(t.effect==='pop'){expected.length-=1n;if(expected.length===0n)expected.element0=0n;}
      if(t.effect==='update'&&t.args[0]===0n)expected.element0=t.args[1];
      if(t.effect==='map_set')expected['key'+mapKeys.indexOf(t.args[0])]=t.args[1];
      if(['parity_init','multiinit'].includes(t.effect)){expected.numOwners=BigInt(t.args[0].length)+1n;expected.required=t.args[1];for(let i=0;i<3;i++)expected['isOwner'+i]=i===t.sender||t.args[0].includes(addresses[i]);}
      if(['parity_init','daylimit'].includes(t.effect))expected.dailyLimit=t.effect==='parity_init'?t.args[2]:t.args[0];
      if(t.effect==='parity_pay')payout(receiverKey,t.args[1]);
     }
     let receipt=null,error=null,status,txHash=null,returnValue=null;
     try{
      if(t.method==='$deployment')status='observation';
      else {
       let tx;
       if(t.method==='$fund')tx=await ss[t.sender].sendTransaction({to:contract.target,value:t.value,gasLimit:6000000n});
       else {const data=baseline.abi.length?new ethers.Interface(baseline.abi).encodeFunctionData(t.method,t.args):null;
        if(t.via)tx=await (t.via==='relay'?relay:rejector).connect(ss[t.sender]).invoke(contract.target,data,{value:t.value,gasLimit:6000000n});
        else tx=await ss[t.sender].sendTransaction({to:contract.target,data,value:t.value,gasLimit:6000000n});
       }
       txHash=tx.hash;receipt=await tx.wait();status=receipt.status===1?'success':'reverted';
      }
     }catch(e){error={message:e.message,data:e.data,transactionHash:e.transactionHash};txHash=e.transactionHash||txHash;if(txHash)receipt=await ethers.provider.getTransactionReceipt(txHash);status=receipt&&receipt.status===0?'reverted':'infrastructure_error';}
     const actual=await observe(),normalizedAccounts={...actual.accounts};
     if(receipt)normalizedAccounts[senderKey]+=receipt.gasUsed*receipt.gasPrice;
     // SELFDESTRUCT removes storage as well as code under the pinned Shanghai semantics.
     if(t.kind==='allowed'&&['destroy','destroy_to'].includes(t.effect))for(const k of Object.keys(expected))if(k!=='contract_wei'&&k!=='code_present')expected[k]=typeof expected[k]==='bigint'?0n:typeof expected[k]==='boolean'?false:Z;
     if(t.kind==='allowed'&&['parity_init','daylimit'].includes(t.effect)&&receipt){const blk=await ethers.provider.getBlock(receipt.blockNumber);expected.lastDay=BigInt(blk.timestamp)/86400n;}
     if(t.kind==='allowed'&&t.effect==='parity_pay'&&receipt){const blk=await ethers.provider.getBlock(receipt.blockNumber);const day=BigInt(blk.timestamp)/86400n;expected.lastDay=day;expected.spentToday=(day>before.state.lastDay?0n:before.state.spentToday)+t.args[1];}
     const stateErrors=Object.fromEntries(Object.keys(expected).filter(k=>actual.state[k]!==expected[k]).map(k=>[k,{expected:expected[k],actual:actual.state[k],discrepancy:typeof expected[k]==='bigint'?actual.state[k]-expected[k]:null}]));
     const accountErrors=Object.fromEntries(accountKeys.filter(k=>normalizedAccounts[k]!==expectedAccounts[k]).map(k=>[k,{expected:expectedAccounts[k],actual:normalizedAccounts[k],discrepancy:normalizedAccounts[k]-expectedAccounts[k]}]));
     const rollback=json(actual.state)===json(before.state)&&json(actual.storage)===json(before.storage)&&json(normalizedAccounts)===json(before.accounts)&&(!receipt||receipt.logs.length===0);
     const noEffect=json(actual.state)===json(before.state)&&json(normalizedAccounts)===json(before.accounts)&&json(actual.storage)===json(before.storage);
     let correct=null;if(status!=='infrastructure_error')correct=t.kind==='must_revert'?status==='reverted'&&rollback:t.kind==='forbidden'?((status==='reverted'&&rollback)||(status==='success'&&noEffect)):(['success','observation'].includes(status)&&Object.keys(stateErrors).length===0&&Object.keys(accountErrors).length===0);
     let getter=null;
     if(file==='mapping_write.sol'&&t.effect==='map_set'&&status==='success'){try{const val=await contract.get(t.args[0]);getter={expected:t.args[1],actual:val,passed:val===t.args[1]};if(!getter.passed)correct=false;}catch(e){getter={status:'error',message:e.message};correct=false;}}
     const deltas=Object.fromEntries(accountKeys.map(k=>[k,normalizedAccounts[k]-before.accounts[k]]));
     const applicability={owner_integrity:'owner'in before.state||'root'in before.state||file==='parity_wallet_bug_2.sol',credit_accounting:isWallet,code_lifecycle:['simple_suicide.sol','arbitrary_location_write_simple.sol','parity_wallet_bug_2.sol'].includes(file),wei_outflow:true,gas:receipt!==null,full_rollback:status==='reverted'};
     const rawpath=path.join(OUT,`${file}.${v}.${scenario}.${index}.json`);
     const row={file,group:item.group,track:item.track,variant:v,scenario,step:index,method:t.method,kind:t.kind,effect:t.effect,compilation_status:'success',setup_status:'success',execution_status:status,inputs:{sender:addresses[t.sender],args:t.args,value_wei:t.value,via:t.via||null,gas_limit:t.method==='$deployment'?null:'6000000'},before,expected:{state:expected,accounts:expectedAccounts},actual,actual_accounts_excluding_tx_gas:normalizedAccounts,state_differences:stateErrors,account_differences:accountErrors,getter_check:getter,correct,security_pass:t.kind==='allowed'?null:correct,functionality_pass:t.kind==='allowed'?correct:null,full_observed_rollback:status==='reverted'?rollback:null,forbidden_no_effect:t.kind==='forbidden'?noEffect:null,contract_outflow_wei:before.state.contract_wei-actual.state.contract_wei,account_deltas_wei_excluding_tx_gas:deltas,applicability,gas_used:receipt?receipt.gasUsed:null,error,raw_output:rawpath};
     fs.writeFileSync(rawpath,json({row,receipt:receipt?receipt.toJSON():null,setup}));rows.push(row);
    }
   }
  }
 }
 fs.writeFileSync(path.join(OUT,'measurements.json'),json(rows));fs.writeFileSync(path.join(OUT,'abi_comparisons.json'),json(abis));fs.writeFileSync(path.join(OUT,'compiler_settings.json'),json(settings));fs.writeFileSync(path.join(OUT,'scenario_manifest.json'),json(scenarioManifest));
 const columns=['file','group','track','variant','scenario','step','method','kind','effect','compilation_status','setup_status','execution_status','inputs','expected','actual','state_differences','account_differences','correct','security_pass','functionality_pass','full_observed_rollback','forbidden_no_effect','contract_outflow_wei','account_deltas_wei_excluding_tx_gas','applicability','gas_used','error','raw_output'];
 const csvCell=x=>'"'+(typeof x==='object'?json(x):String(x??'')).replaceAll('"','""')+'"';fs.writeFileSync(path.join(OUT,'measurements.csv'),columns.join(',')+'\n'+rows.map(r=>columns.map(k=>csvCell(r[k])).join(',')).join('\n'));
 console.log(json({rows:rows.length,files:new Set(rows.map(r=>r.file)).size,errors:rows.filter(r=>!['success','reverted','observation'].includes(r.execution_status)),failed:rows.filter(r=>r.correct===false).map(r=>({file:r.file,variant:r.variant,scenario:r.scenario,step:r.step,kind:r.kind,status:r.execution_status,state_differences:r.state_differences,accounts:r.account_differences}))}));
}
run().catch(e=>{console.error(e);process.exitCode=1});
