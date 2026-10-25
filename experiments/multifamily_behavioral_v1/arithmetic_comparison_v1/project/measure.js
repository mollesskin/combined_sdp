const fs=require('fs'),path=require('path');
const {ethers,network,artifacts}=require('hardhat');
const M=(1n<<256n)-1n, MOD=M+1n,E=10n**18n;
const out=path.resolve(process.env.OUTPUT_DIR);fs.mkdirSync(out,{recursive:true});
const cases=JSON.parse(fs.readFileSync('../registry.json')).cases;
const stringify=x=>JSON.stringify(x,(_,v)=>typeof v==='bigint'?v.toString():v,2);
const rows=[],abi=[],compilers=[];
function scenarios(file,a,b){
 const step=(method,args=[],kind='allowed',op=null)=>({method,args,kind,op});
 const op=(field,type,input)=>({field,type,input});
 if(['integer_overflow_1.sol','integer_overflow_add.sol','overflow_simple_add.sol'].includes(file)){
  let f=file==='integer_overflow_add.sol'?'run':'add',initial=file==='integer_overflow_1.sol'?0n:1n;
  return [['ordinary',[step(f,[0n],'allowed',op('value','add',0n)),step(f,[7n],'allowed',op('value','add',7n))]],['boundary',[step(f,[M-initial],'allowed',op('value','add',M-initial)),step(f,[1n],'unsafe',op('value','add',1n))]]];
 }
 if(file==='integer_overflow_mapping_sym_1.sol')return [['zero',[step('init',[7n,0n],'allowed',op('value','sub',0n))]],['underflow',[step('init',[7n,1n],'unsafe',op('value','sub',1n))]]];
 if(file.includes('minimal')||file.includes('multitx')){
  let pre=file.includes('multifunc')?[step('run',[M]),step('init')]:file.includes('onefunc')?[step('run',[M])]:[];
  return [['ordinary',[...pre,step('run',[0n],'allowed',op('value','sub',0n)),step('run',[1n],'allowed',op('value','sub',1n))]],['underflow',[...pre,step('run',[2n],'unsafe',op('value','sub',2n))]]];
 }
 if(file==='integer_overflow_mul.sol')return [['ordinary',[step('run',[0n],'allowed',op('value','mul',0n))]],['boundary',[step('run',[M/2n],'allowed',op('value','mul',M/2n)),step('run',[2n],'unsafe',op('value','mul',2n))]]];
 if(file==='overflow_single_tx.sol')return [
 ['add',[step('overflowaddtostate',[7n],'allowed',op('value','add',7n)),step('overflowaddtostate',[M],'unsafe',op('value','add',M))]],
 ['sub',[step('underflowtostate',[1n],'allowed',op('value','sub',1n)),step('underflowtostate',[1n],'unsafe',op('value','sub',1n))]],
 ['mul',[step('overflowmultostate',[2n],'allowed',op('value','mul',2n)),step('overflowmultostate',[M/2n],'allowed',op('value','mul',M/2n)),step('overflowmultostate',[2n],'unsafe',op('value','mul',2n))]]];
 if(file==='token.sol')return [
 ['ordinary',[step('transfer',[b,7n]),{...step('transfer',[a,7n]),sender:1},step('transfer',[b,0n]),step('transfer',[a,10n])]],
 ['underflow',[{...step('transfer',[a,1n],'unsafe'),sender:1}]],['self_insufficient',[{...step('transfer',[b,1n],'unsafe'),sender:1}]]];
 if(file==='BECToken.sol')return [['ordinary',[step('batchTransfer',[[b],10n]),step('batchTransfer',[[a],10n]),step('batchTransfer',[[b,b],5n])]],['overflow',[{...step('batchTransfer',[[a,b],1n<<255n],'unsafe'),sender:1}]]];
 if(file==='tokensalechallenge.sol')return [['ordinary',[{...step('buy',[1n]),value:E},step('sell',[1n]),step('buy',[0n]),step('sell',[0n])]],['insufficient',[step('sell',[1n],'reject')]],['overflow',[{...step('buy',[M/E+1n],'unsafe'),value:((M/E+1n)*E)%MOD}]]];
 if(file==='timelock.sol')return [['ordinary',[{...step('deposit'),value:1n},step('increaseLockTime',[1n],'allowed',op('lock','add',1n)),step('withdraw',[],'reject'),{...step('withdraw'),advance:8n*86400n}]],['overflow',[{...step('deposit'),value:1n},step('increaseLockTime',['TO_ZERO'],'unsafe',op('lock','add','TO_ZERO'))]]];
 throw Error(file);
}
async function main(){
 for(const c of cases){
  let baseABI;
  for(let v=0;v<4;v++){
   const file=c.file,source=`contracts/V${v}/${file}`;
   const names=(await artifacts.getAllFullyQualifiedNames()).filter(n=>n.startsWith(source+':')&&!n.endsWith(':ResearchChecked'));
   const name=file==='BECToken.sol'?names.find(n=>n.endsWith(':BecToken')):names[0];
   const art=await artifacts.readArtifact(name),build=await artifacts.getBuildInfo(name);
   if(v===0)baseABI=JSON.stringify(art.abi);
   abi.push({file,variant:`V${v}`,equal_V0:baseABI===JSON.stringify(art.abi),abi:art.abi});
   compilers.push({file,variant:`V${v}`,solcVersion:build.solcVersion,solcLongVersion:build.solcLongVersion,settings:build.input.settings});
   const signers=await ethers.getSigners();const aa=signers[0].address,bb=signers[1].address;
   for(const [scenario,steps] of scenarios(file,aa,bb)){
    await network.provider.send('hardhat_reset');
    const ss=await ethers.getSigners(),a=ss[0].address,b=ss[1].address;
    let contract;
    try{
     const factory=await ethers.getContractFactory(art.abi,art.bytecode,ss[0]);
     contract=await factory.deploy(...(file==='token.sol'?[10n]:file==='tokensalechallenge.sol'?[a,{value:E}]:[]));await contract.waitForDeployment();
    }catch(e){rows.push({file,variant:`V${v}`,scenario,compilation_status:'success',setup_status:'error',execution_status:'missing',error:String(e)});continue;}
    const slot=async n=>BigInt(await ethers.provider.getStorage(contract.target,n));
    async function state(){
     const s={slot0:await slot(0),slot1:await slot(1),contract_wei:await ethers.provider.getBalance(contract.target)};
     if(file==='integer_overflow_mapping_sym_1.sol')s.value=await slot(ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(['uint256','uint256'],[7n,0n])));
     else if(file==='timelock.sol'){s.lock=await contract.lockTime(a);s.credit=await contract.balances(a);}
     else if(['token.sol','BECToken.sol','tokensalechallenge.sol'].includes(file)){s.a=await contract.balanceOf(a);s.b=await contract.balanceOf(b);if(file!=='tokensalechallenge.sol')s.supply=await contract.totalSupply();}
     else s.value=await slot(file.includes('multitx')?1:0);
     return s;
    }
    for(let i=0;i<steps.length;i++){
     let t=steps[i];if(t.advance){await network.provider.send('evm_increaseTime',[parseInt(t.advance.toString(),10)]);await network.provider.send('evm_mine');}
     const before=await state();let args=t.args.map(x=>x==='TO_ZERO'?MOD-before.lock:x), expected={...before};let math=null;
     if(t.op){const x=before[t.op.field],y=t.op.input==='TO_ZERO'?MOD-before.lock:t.op.input;math=t.op.type==='add'?x+y:t.op.type==='sub'?x-y:x*y;expected[t.op.field]=math;}
     if(['token.sol','BECToken.sol'].includes(file)){
      const sender=t.sender===1?'b':'a';if(file==='token.sol'){expected[sender]-=args[1];expected[args[0]===a?'a':'b']+=args[1];}
      else {expected[sender]-=BigInt(args[0].length)*args[1];for(const receiver of args[0])expected[receiver===a?'a':'b']+=args[1];}
     }
     if(file==='tokensalechallenge.sol'){expected.a+=t.method==='buy'?args[0]:-args[0];expected.contract_wei+=t.method==='buy'?(t.value||0n):-args[0]*E;}
     if(file==='timelock.sol'&&t.method==='deposit'){expected.credit+=t.value;expected.contract_wei+=t.value;}
     if(file==='timelock.sol'&&t.method==='withdraw'&&t.kind==='allowed'){expected.credit=0n;expected.contract_wei=0n;}
     // Mirror exact storage aliases for declared observable state.
     if('value'in expected&&file!=='integer_overflow_mapping_sym_1.sol')expected[file.includes('multitx')?'slot1':'slot0']=expected.value;
     if(file.includes('multifunc')&&t.method==='init')expected.slot0=1n;
     if(file.includes('onefunc')&&before.slot0===0n)expected.slot0=1n;
     let receipt,error=null,status;
     try{const tx=await contract.connect(ss[t.sender||0])[t.method](...args,{value:t.value||0n,gasLimit:6000000n});receipt=await tx.wait();status=receipt.status===1?'success':'reverted';}
     catch(e){error={message:e.message,data:e.data,transactionHash:e.transactionHash};if(e.transactionHash)receipt=await ethers.provider.getTransactionReceipt(e.transactionHash);status=receipt&&receipt.status===0?'reverted':'infrastructure_error';}
     const actual=await state();
     if(file==='timelock.sol'&&t.method==='deposit'&&status==='success'){const block=await ethers.provider.getBlock(receipt.blockNumber);expected.lock=BigInt(block.timestamp)+604800n;}
     // Setup calls through init branches intentionally preserve count; their state oracle includes initialized.
     const rollback=stringify(actual)===stringify(before)&&(!receipt||receipt.logs.length===0);
     const differences={};for(const k of Object.keys(expected))if(expected[k]!==actual[k])differences[k]=(actual[k]-expected[k]).toString();
     const mustReject=t.kind==='unsafe'||t.kind==='reject';
     const correct=status==='success'?!mustReject&&Object.keys(differences).length===0:status==='reverted'?mustReject&&rollback:false;
     const discrepancy=t.op&&status==='success'?actual[t.op.field]-math:null;
     const arithmetic_trace=[];
     function trace(label,left,right,type){const result=type==='add'?left+right:type==='sub'?left-right:left*right;arithmetic_trace.push({label,left,right,type,mathematical_result:result,in_uint256_range:result>=0n&&result<=M,modular_result:((result%MOD)+MOD)%MOD});}
     if(t.op)trace(t.op.field,before[t.op.field],t.op.input==='TO_ZERO'?MOD-before.lock:t.op.input,t.op.type);
     if(file==='token.sol'){const sender=t.sender===1?'b':'a',receiver=args[0]===a?'a':'b';trace('require/debit',before[sender],args[1],'sub');trace('credit_after_debit',sender===receiver?((before[sender]-args[1]+MOD)%MOD):before[receiver],args[1],'add');}
     if(file==='BECToken.sol')trace('batch_amount',BigInt(args[0].length),args[1],'mul');
     if(file==='tokensalechallenge.sol'){trace('price',args[0],E,'mul');trace('credit/debit',before.a,args[0],t.method==='buy'?'add':'sub');}
     const wrap=status==='success'&&arithmetic_trace.some(x=>!x.in_uint256_range);
     const observed_modular_result=t.op&&status==='success'&&math!==actual[t.op.field]&&actual[t.op.field]===((math%MOD)+MOD)%MOD;
     const rawpath=path.join(out,`${file}.V${v}.${scenario}.${i}.json`);
     const row={file,group:c.group,variant:`V${v}`,scenario,step:i,method:t.method,compilation_status:'success',setup_status:'success',execution_status:status,kind:t.kind,inputs:{sender:ss[t.sender||0].address,args,value_wei:t.value||0n},before,expected:mustReject?before:expected,mathematical_expected:math,unsafe_mathematical_state:mustReject?expected:null,actual,discrepancy,field_discrepancies:status==='success'?differences:null,arithmetic_trace,wraparound:wrap,wraparound_evidence:wrap?(observed_modular_result?'observed_modular_state':'inferred_from_executed_source_and_operands'):null,full_observed_rollback:status==='reverted'?rollback:null,allowed_operation_passed:t.kind==='allowed'?correct:null,correct,violated_properties:correct?[]:[mustReject?'safe_rejection_and_rollback':'exact_permitted_state'],gas_used:receipt?receipt.gasUsed:null,raw_output:rawpath,error};
     fs.writeFileSync(rawpath,stringify({row,receipt:receipt?receipt.toJSON():null}));rows.push(row);
    }
   }
  }
 }
 fs.writeFileSync(path.join(out,'measurements.json'),stringify(rows));fs.writeFileSync(path.join(out,'abi_comparisons.json'),stringify(abi));fs.writeFileSync(path.join(out,'compiler_settings.json'),stringify(compilers));
 const columns=['file','group','variant','scenario','step','method','compilation_status','setup_status','execution_status','kind','inputs','before','expected','mathematical_expected','actual','discrepancy','field_discrepancies','arithmetic_trace','wraparound','wraparound_evidence','full_observed_rollback','allowed_operation_passed','correct','violated_properties','gas_used','raw_output'];
 const cell=v=>'"'+(typeof v==='object'?stringify(v):String(v??'')).replaceAll('"','""')+'"';
 fs.writeFileSync(path.join(out,'measurements.csv'),columns.join(',')+'\n'+rows.map(r=>columns.map(k=>cell(r[k])).join(',')).join('\n'));
 console.log(stringify({rows:rows.length,incorrect:rows.filter(r=>!r.correct).map(r=>({file:r.file,v:r.variant,s:r.scenario,step:r.step,status:r.execution_status,error:r.error?.message})),infrastructure:rows.filter(r=>r.execution_status==='infrastructure_error').length}));
}
main().catch(e=>{console.error(e);process.exitCode=1});
