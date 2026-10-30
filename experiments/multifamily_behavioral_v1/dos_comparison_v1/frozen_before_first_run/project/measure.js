const fs=require('fs'),path=require('path');
const {ethers,network,artifacts}=require('hardhat');
const S=path.resolve(__dirname,'..'),OUT=path.resolve(process.env.OUTPUT_DIR||'../runs/unset');
if(fs.existsSync(OUT))throw Error('Refuse output overwrite '+OUT);fs.mkdirSync(OUT,{recursive:true});
const registry=JSON.parse(fs.readFileSync(path.join(S,'registry.json'))).cases;
const GAS=12000000n,BLOCK=30000000n,CHUNK=350n,MAXSTEPS=20;
const json=x=>JSON.stringify(x,(_,v)=>typeof v==='bigint'?v.toString():v,2);
const write=(n,x)=>fs.writeFileSync(path.join(OUT,n),json(x));
const rows=[],operations=[],statusHistory=[],compiler=[],abis=[];
const names={'auction.sol':'DosAuction','dos_address.sol':'DosGas','dos_number.sol':'DosNumber','dos_simple.sol':'DosOneFunc'};
let context;
function same(a,b){return json(a)===json(b);}
async function setup(file,v,scenario){
 await network.provider.send('hardhat_reset');
 const signers=await ethers.getSigners(),fq=`contracts/${v}/${file}:${names[file]}`;
 const art=await artifacts.readArtifact(fq),factory=await ethers.getContractFactory(art.abi,art.bytecode,signers[0]);
 const victim=await factory.deploy();await victim.waitForDeployment();
 const fixture=await (await ethers.getContractFactory('BidderFixture',signers[1])).deploy();await fixture.waitForDeployment();
 const accountAddresses=[...signers.slice(0,3).map(x=>x.address),fixture.target];
 context={file,v,scenario,signers,victim,fixture,accountAddresses,index:0,deploy:{victim:(await victim.deploymentTransaction().wait()).toJSON(),fixture:(await fixture.deploymentTransaction().wait()).toJSON()}};
 write(`${file}.${v}.${scenario}.setup.json`,context.deploy);return context;
}
const arrayBase=file=>BigInt(ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(['uint256'],[file==='dos_number.sol'?1n:0n])));
async function slot(n){return BigInt(await ethers.provider.getStorage(context.victim.target,n));}
async function state(){
 const {file,v,victim,accountAddresses}=context;
 const storage=await Promise.all([0n,1n,2n].map(slot));
 const s={contract_wei:await ethers.provider.getBalance(victim.target),storage0:storage[0],storage1:storage[1],storage2:storage[2]};
 if(file==='auction.sol'){
  s.leader=ethers.getAddress(ethers.toBeHex(storage[0]&((1n<<160n)-1n),20));s.bid=storage[1];
  s.claims={};for(const a of accountAddresses)s.claims[a]=v==='V0'?0n:await victim.refunds(a);
 }else{
  s.length=storage[file==='dos_number.sol'?1:0];s.logical=file==='dos_number.sol'?storage[0]:s.length;
  s.clearing=v==='V1'||v==='V3'||v==='F1'?await victim.clearing():false;
  s.win=file==='dos_address.sol'?await victim.iWin():null;
  const base=arrayBase(file),idx=[0n,s.length/2n,s.length?s.length-1n:0n];s.samples={};
  for(const i of idx)s.samples[i.toString()]=await slot(base+i);
 }
 s.accounts=await Promise.all(accountAddresses.map(x=>ethers.provider.getBalance(x)));
 return s;
}
async function records(length,label,expected){
 const base=arrayBase(context.file),values=[];
 for(let first=0n;first<length;first+=128n){const ids=[];for(let i=first;i<length&&i<first+128n;i++)ids.push(i);values.push(...await Promise.all(ids.map(i=>slot(base+i))));}
 const bad=[];for(let i=0;i<values.length;i++)if(values[i]!==expected(BigInt(i)))bad.push(String(i));
 const raw=`${context.file}.${context.v}.${context.scenario}.${label}.records.json`;
 write(raw,{length,values,incorrect_indices:bad});return {checked:length,correct:bad.length===0,raw_output:path.join(OUT,raw)};
}
async function classify(hash,error){
 if(hash){const receipt=await ethers.provider.getTransactionReceipt(hash);if(receipt)return {status:receipt.status===1?'success':'reverted',receipt};const tx=await ethers.provider.getTransaction(hash);return {status:tx?'pending':'infrastructure_error',receipt:null};}
 if(error&&/exceeds.*block gas limit|exceed.*block.*gas|gas limit.*block|transaction gas limit/i.test(error.message))return {status:'rejected_before_inclusion',receipt:null};
 return {status:'infrastructure_error',receipt:null};
}
async function tx(method,args=[],options={}){
 const c=context,phase=options.phase||'work',sender=options.sender??0;
 const before=await state();let hash=null,error=null;
 try{
  const target=options.fixture?c.fixture:c.victim;
  const sent=await target.connect(c.signers[sender])[method](...args,{value:options.value||0n,gasLimit:options.gasLimit||GAS});hash=sent.hash;
  await sent.wait();
 }catch(e){hash=e.transactionHash||hash;error={message:e.message,data:e.data,code:e.code,transactionHash:e.transactionHash||null};}
 const {status,receipt}=await classify(hash,error),actual=await state(),normalized={...actual,accounts:[...actual.accounts]};
 if(receipt)normalized.accounts[sender]+=receipt.gasUsed*receipt.gasPrice;
 const rollback=status==='reverted'?same(normalized,before)&&receipt.logs.length===0:null;
 const result={file:c.file,variant:c.v,scenario:c.scenario,step:c.index++,phase,method,inputs:{args,sender:c.signers[sender].address,value_wei:options.value||0n,gas_limit:options.gasLimit||GAS,via_fixture:!!options.fixture},compilation_status:'success',setup_status:'success',execution_status:status,before,actual,actual_excluding_tx_gas:normalized,full_observed_rollback:rollback,gas_used:receipt?receipt.gasUsed:null,error,transaction_hash:hash};
 result.raw_output=path.join(OUT,`${c.file}.${c.v}.${c.scenario}.${result.step}.json`);rows.push(result);
 fs.writeFileSync(result.raw_output,json({row:result,receipt:receipt?receipt.toJSON():null}));return result;
}
function update(row,extra){Object.assign(row,extra);const raw=JSON.parse(fs.readFileSync(row.raw_output));raw.row=row;fs.writeFileSync(row.raw_output,json(raw));}
function sumGas(rs){return rs.every(r=>r.gas_used!==null)?rs.reduce((a,r)=>a+r.gas_used,0n):null;}
const isFailure=r=>['infrastructure_error','pending','rejected_before_inclusion'].includes(r.execution_status);
async function arrayWorkflow(file,v,scenario,batches){
 await setup(file,v,scenario);const start=rows.length,requested=BigInt(batches)*CHUNK,loads=[];
 const loadMethod=file==='dos_address.sol'?'addCreditors':file==='dos_number.sol'?'insertNnumbers':'ifillArray';
 for(let i=0;i<batches;i++){
  const r=await tx(loadMethod,file==='dos_number.sol'?[1n,CHUNK]:[],{phase:'load'});
  const volume=isFailure(r)?null:r.actual.logical-r.before.logical;
  const capacityPolicy=['V2','V3'].includes(v)&&r.before.logical+CHUNK>1750n;
  update(r,{requested_work:CHUNK,accepted_work:volume,rejected_work:volume===null?null:CHUNK-volume,rejection_reason:r.execution_status==='reverted'?capacityPolicy?'capacity_policy':'execution_revert':null,admission_correct:volume===null?null:(r.execution_status==='success'?volume===CHUNK:r.full_observed_rollback),expected_change:r.execution_status==='success'?'append 350 exact records':'rollback; rejected request still counted'});loads.push(r);
 }
 const accepted=loads.every(r=>r.accepted_work!==null)?loads.reduce((a,r)=>a+r.accepted_work,0n):null;
 const pre=await state(),value=file==='dos_number.sol'?1n:BigInt(context.signers[0].address);
 const intact=await records(pre.length,'before_cleanup',()=>value);
 const cleanup=[],method=file==='dos_address.sol'?'emptyCreditors':file==='dos_number.sol'?'clearDOS':'ifillArray';
 let reason='step_budget_exhausted';
 for(let step=0;step<MAXSTEPS;step++){
  const before=await state();if(before.length===0n){reason='completed';break;}
  const r=await tx(method,[],{phase:'cleanup'});const progress=isFailure(r)?null:r.before.length-r.actual.length;
  update(r,{requested_work:r.before.length,completed_work:progress,progress_monotonic:progress===null?null:progress>0n&&progress<=r.before.length,expected_final:{length:'0',logical:'0',win:file==='dos_address.sol'?true:null},retained_records_requirement:'remaining prefix is unchanged; only explicitly requested cleanup deletes records'});cleanup.push(r);
  if(r.execution_status!=='success'){reason=r.execution_status;break;}
  if(r.actual.length===0n){reason='completed';break;}
  if(progress<=0n){reason='successful_no_progress';break;}
 }
 const final=await state(),completed=accepted===null?null:accepted-final.length;
 const finalRecords=await records(pre.length,'after_cleanup',i=>i<final.length?value:0n);
 const acceptedComplete=accepted===null||accepted===0n?null:final.length===0n&&final.logical===0n&&(file!=='dos_address.sol'||final.win===true);
 const admitted=loads.every(r=>r.admission_correct===true)&&intact.correct;
 const operationGas=sumGas([...loads,...cleanup]);let refill=null;
 if(acceptedComplete){
  const r=await tx(loadMethod,file==='dos_number.sol'?[9n,CHUNK]:[],{phase:'post_completion_refill'});
  const verify=await records(CHUNK,'refill',()=>file==='dos_number.sol'?9n:value);
  refill={correct:r.execution_status==='success'&&r.actual.logical===CHUNK&&verify.correct,gas_used:r.gas_used,raw_output:r.raw_output,records:verify};
 }
 operations.push({file,variant:v,scenario,track:file==='dos_simple.sol'?'single':'factorial',requested_work:requested,accepted_work:accepted,rejected_work:accepted===null?null:requested-accepted,completed_work:completed,completion_requested:{numerator:completed,denominator:requested},completion_accepted:{numerator:completed,denominator:accepted},full_requested_task_complete:acceptedComplete===null?null:acceptedComplete&&accepted===requested&&admitted&&finalRecords.correct,accepted_part_complete:acceptedComplete,capacity_rejected:loads.reduce((a,r)=>a+(r.rejection_reason==='capacity_policy'?(r.rejected_work||0n):0n),0n),load_transactions:loads.length,cleanup_transactions:cleanup.length,transactions_to_complete:acceptedComplete?loads.length+cleanup.length:null,steps_limit:MAXSTEPS,cleanup_gas_budget:240000000n,total_workflow_gas_budget:BigInt(batches+MAXSTEPS)*GAS,load_gas_used:sumGas(loads),cleanup_gas_used:sumGas(cleanup),total_workflow_gas_used:operationGas,cleanup_stop_reason:reason,initial_state:pre,final_state:final,records_preserved_before_cleanup:intact,records_correct_after_cleanup:finalRecords,admission_correct:admitted,post_completion_refill:refill,error:loads.some(isFailure)||cleanup.some(isFailure)?'nonexecuted_or_infrastructure_status':null,raw_outputs:rows.slice(start).map(r=>r.raw_output)});
}
async function numberExtras(v){
 await setup('dos_number.sol',v,'logical_clear_reuse');const start=rows.length;
 for(let i=0;i<5;i++)await tx('insertNnumbers',[1n,CHUNK],{phase:'load'});
 const before=await state(),r=await tx('clear',[],{phase:'logical_clear'}),q=await tx('insertNnumbers',[9n,CHUNK],{phase:'reuse'});
 const verify=await records(1750n,'reuse',i=>i<350n?9n:1n);
 operations.push({file:'dos_number.sol',variant:v,scenario:'logical_clear_reuse',track:'functional_check',requested_work:2100n,accepted_work:q.execution_status==='success'?2100n:null,completed_work:null,completion_requested:null,full_requested_task_complete:r.execution_status==='success'&&r.actual.logical===0n&&r.actual.length===before.length&&q.execution_status==='success'&&q.actual.logical===350n&&verify.correct,records_check:verify,total_workflow_gas_used:sumGas(rows.slice(start)),raw_outputs:rows.slice(start).map(r=>r.raw_output)});
 await setup('dos_number.sol',v,'oversize_insert');const rr=await tx('insertNnumbers',[1n,5000n],{phase:'oversize'});
 const accepted=isFailure(rr)?null:rr.actual.logical;
 update(rr,{requested_work:5000n,accepted_work:accepted,rejected_work:accepted===null?null:5000n-accepted});
 operations.push({file:'dos_number.sol',variant:v,scenario:'oversize_insert',track:'scope_limit',requested_work:5000n,accepted_work:accepted,rejected_work:accepted===null?null:5000n-accepted,completed_work:accepted,completion_requested:{numerator:accepted,denominator:5000n},full_requested_task_complete:accepted===5000n,execution_status:rr.execution_status,total_workflow_gas_used:rr.gas_used,full_observed_rollback:rr.full_observed_rollback,raw_outputs:[rr.raw_output]});
}
async function auction(v,refusing){
 const scenario=refusing?'refusing_bidder':'ordinary_bidder';await setup('auction.sol',v,scenario);const c=context,start=rows.length,old=refusing?c.fixture.target:c.signers[1].address;
 const first=await tx(refusing?'placeBid':'bid',refusing?[c.victim.target]:[],{sender:1,fixture:refusing,value:10n,phase:'first_bid'});
 const higher=await tx('bid',[],{sender:2,value:20n,phase:'higher_bid'});
 const accepted=higher.execution_status==='success'&&higher.actual.leader===c.signers[2].address&&higher.actual.bid===20n;
 let paid=higher.actual_excluding_tx_gas.accounts[1]-higher.before.accounts[1]+higher.actual_excluding_tx_gas.accounts[3]-higher.before.accounts[3];
 const outstanding=higher.actual.claims[old],backing=higher.actual.contract_wei===higher.actual.bid+Object.values(higher.actual.claims).reduce((a,b)=>a+b,0n);
 update(higher,{requested_work:'1 higher bid',bid_progress_complete:accepted,prior_bid_refund_entitlement_wei:accepted?10n:null,paid_old_bidder_wei:paid,registered_refund_wei:accepted?outstanding:null,entitlement_preserved:accepted?paid+outstanding===10n:null,live_bid_backed:backing,expected_success_state:{leader:c.signers[2].address,bid:20n,former_bid_paid_plus_claim:'10'}});
 const eq=await tx('bid',[],{sender:0,value:20n,phase:'equal_bid_rejection'});update(eq,{correct_rejection:eq.execution_status==='reverted'&&eq.full_observed_rollback});
 let claimFailed=null,recovery=null,repeat=null;
 if(v!=='V0'&&accepted&&outstanding>0n){
  if(refusing){const r=await tx('claim',[c.victim.target,c.fixture.target],{sender:1,fixture:true,phase:'claim_to_refusing_recipient'});claimFailed=r.execution_status==='reverted'&&r.full_observed_rollback&&r.actual.claims[old]===10n;update(r,{claim_preserved_after_failure:claimFailed});}
  const r=await tx(refusing?'claim':'withdrawRefund',refusing?[c.victim.target,c.signers[1].address]:[c.signers[1].address],{sender:1,fixture:refusing,phase:'refund_recovery'});
  const gained=r.actual_excluding_tx_gas.accounts[1]-r.before.accounts[1]+r.actual_excluding_tx_gas.accounts[3]-r.before.accounts[3];paid+=gained;
  recovery=r.execution_status==='success'&&gained===10n&&r.actual.claims[old]===0n;update(r,{recovery_correct:recovery,paid_old_bidder_wei:gained});
  const q=await tx(refusing?'claim':'withdrawRefund',refusing?[c.victim.target,c.signers[1].address]:[c.signers[1].address],{sender:1,fixture:refusing,phase:'repeat_claim'});
  const gainedAgain=q.actual_excluding_tx_gas.accounts[1]-q.before.accounts[1]+q.actual_excluding_tx_gas.accounts[3]-q.before.accounts[3];repeat=q.execution_status==='success'&&gainedAgain===0n&&q.actual.claims[old]===0n;update(q,{repeat_claim_no_extra_payout:repeat});
 }
 const final=await state();operations.push({file:'auction.sol',variant:v,scenario,track:'alternatives',requested_work:1n,accepted_work:accepted?1n:0n,completed_work:accepted?1n:0n,completion_requested:{numerator:accepted?1n:0n,denominator:1n},full_requested_task_complete:accepted&&backing&&paid===10n&&final.bid===20n&&final.contract_wei===20n&&Object.values(final.claims).every(x=>x===0n)&&eq.correct_rejection,former_bidder:old,higher_bid_accepted:accepted,refund_entitlement_after_outbid_wei:accepted?10n:null,refund_paid_before_claim_wei:higher.paid_old_bidder_wei,refund_owed_after_outbid_wei:accepted?outstanding:null,eventual_refund_paid_wei:accepted?paid:null,baseline_uncompleted_live_bid_wei:accepted?null:final.bid,live_bid_backed:backing,claim_failure_rollback:claimFailed,recovery_correct:recovery,repeat_claim_no_extra_payout:repeat,claim_applicability:outstanding>0n&&accepted?'deferred_claim_required':'N/A: immediate refund or outbid not accepted',final_state:final,total_workflow_gas_used:sumGas(rows.slice(start)),workflow_transactions:rows.length-start,transaction_limit:8,gas_budget:96000000n,raw_outputs:rows.slice(start).map(r=>r.raw_output)});
}
async function miningStatus(v){
 await setup('dos_simple.sol',v,'mining_status');const c=context,hashes=[],history=[];
 try{
  await network.provider.send('evm_setAutomine',[false]);await network.provider.send('evm_setIntervalMining',[0]);
  const input={from:c.signers[0].address,to:c.victim.target,data:c.victim.interface.encodeFunctionData('ifillArray'),gas:ethers.toQuantity(GAS)};
  for(let i=0;i<4;i++)hashes.push(await network.provider.send('eth_sendTransaction',[input]));
  for(let block=1;block<=4;block++){
   await network.provider.send('evm_mine');
   let pending=0;
   for(let i=0;i<hashes.length;i++){
    const st=await classify(hashes[i],null);if(st.status==='pending')pending++;
    history.push({file:c.file,variant:v,scenario:'mining_status',after_mined_blocks:block,index:i,hash:hashes[i],execution_status:st.status,receipt:st.receipt?st.receipt.toJSON():null,gas_used:st.receipt?st.receipt.gasUsed:null});
   }
   if(!pending)break;
  }
  const final=await state(),verify=await records(1400n,'mining_final',()=>BigInt(c.signers[0].address));
  let preError=null,preHash=null;try{preHash=await network.provider.send('eth_sendTransaction',[{...input,gas:ethers.toQuantity(BLOCK+1n)}]);}catch(e){preError={message:e.message,code:e.code};}
  const status=await classify(preHash,preError);
  const probe={file:c.file,variant:v,scenario:'block_budget_admission_probe',gas_limit:BLOCK+1n,execution_status:status.status,error:preError,hash:preHash,applicability:'classifier diagnostic only; excluded from workload efficiency'};
  history.push(probe);statusHistory.push(...history);write(`${c.file}.${v}.mining_status.json`,{history,final,verify});
  operations.push({file:c.file,variant:v,scenario:'mining_status',track:'status_diagnostic',requested_work:1400n,accepted_work:final.length,completed_work:final.length,completion_requested:{numerator:final.length,denominator:1400n},full_requested_task_complete:final.length===1400n&&verify.correct,status_history_raw:path.join(OUT,`${c.file}.${v}.mining_status.json`),first_block_pending:history.filter(x=>x.after_mined_blocks===1&&x.execution_status==='pending').length,final_pending:hashes.filter(h=>history.filter(x=>x.hash===h&&x.after_mined_blocks).at(-1)?.execution_status==='pending').length,admission_probe_status:status.status,notes:'Noninclusion after one block is not an execution failure or permanent DoS'});
 }finally{await network.provider.send('evm_setAutomine',[true]);await network.provider.send('evm_setIntervalMining',[0]);await network.provider.send('hardhat_reset');}
}
function exportCSV(filename,data){const cols=[...new Set(data.flatMap(x=>Object.keys(x)))];const cell=v=>'"'+(typeof v==='object'?json(v):String(v??'')).replaceAll('"','""')+'"';fs.writeFileSync(path.join(OUT,filename),cols.join(',')+'\n'+data.map(r=>cols.map(k=>cell(r[k])).join(',')).join('\n'));}
async function main(){
 for(const c of registry){
  const baseline=await artifacts.readArtifact(`contracts/V0/${c.file}:${names[c.file]}`);
  for(const v of Object.keys(c.variants)){
   const fq=`contracts/${v}/${c.file}:${names[c.file]}`,art=await artifacts.readArtifact(fq),b=await artifacts.getBuildInfo(fq);
   compiler.push({file:c.file,variant:v,solcVersion:b.solcVersion,solcLongVersion:b.solcLongVersion,settings:b.input.settings});abis.push({file:c.file,variant:v,equal_V0:same(art.abi,baseline.abi),actual:art.abi,baseline:baseline.abi});
  }
 }
 // Always export partial evidence if an infrastructure exception interrupts the suite.
 try{
  for(const c of registry)for(const v of Object.keys(c.variants)){
   if(c.file==='auction.sol'){await auction(v,false);await auction(v,true);}
   else if(c.file==='dos_simple.sol'){await arrayWorkflow(c.file,v,'natural_cycle',5);await miningStatus(v);}
   else {await arrayWorkflow(c.file,v,'load_1750',5);await arrayWorkflow(c.file,v,'load_5950',17);if(c.file==='dos_number.sol')await numberExtras(v);}
  }
 }finally{
  write('measurements.json',rows);write('operations.json',operations);write('status_history.json',statusHistory);write('compiler_settings.json',compiler);write('abi_comparisons.json',abis);
  exportCSV('measurements.csv',rows);exportCSV('operations.csv',operations);exportCSV('status_history.csv',statusHistory);
 }
 console.log(json({observations:rows.length,operations:operations.length,statuses:rows.reduce((a,r)=>(a[r.execution_status]=(a[r.execution_status]||0)+1,a),{}),outcomes:operations.map(o=>({file:o.file,variant:o.variant,scenario:o.scenario,requested:o.requested_work,accepted:o.accepted_work,completed:o.completed_work,complete:o.full_requested_task_complete,cleanup_steps:o.cleanup_transactions,reason:o.cleanup_stop_reason,error:o.error}))}));
}
main().catch(e=>{write('infrastructure_exception.json',{message:e.message,stack:e.stack});console.error(e);process.exitCode=1});
