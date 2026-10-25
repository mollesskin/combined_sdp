const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const hre = require("hardhat");

const base = path.resolve(__dirname, "../..");
const ether = hre.ethers.parseEther("1");

function artifact(name) {
  return JSON.parse(fs.readFileSync(path.join(base, "artifacts", `${name}.json`), "utf8"));
}

async function deploy(name, signer, args = []) {
  const info = artifact(name);
  const factory = new hre.ethers.ContractFactory(info.abi, info.bytecode, signer);
  const contract = await factory.deploy(...args);
  await contract.waitForDeployment();
  return contract;
}

async function ordinary(variant, donor) {
  const dao = await deploy(variant, donor);
  await (await dao.donate(donor.address, { value: ether })).wait();
  const creditBefore = await dao.queryCredit.staticCall(donor.address);
  await (await dao.withdraw(ether)).wait();
  const result = {
    creditBefore,
    creditAfter: await dao.queryCredit.staticCall(donor.address),
    daoBalanceAfter: await hre.ethers.provider.getBalance(dao.target),
  };
  assert.equal(result.creditBefore, ether);
  assert.equal(result.creditAfter, 0n);
  assert.equal(result.daoBalanceAfter, 0n);
  return result;
}

async function nested(variant, donor) {
  const dao = await deploy(variant, donor);
  const attacker = await deploy("OneReentryAttacker", donor, [dao.target]);
  await (await dao.donate(donor.address, { value: ether })).wait();
  await (await dao.donate(attacker.target, { value: ether })).wait();
  const before = await hre.ethers.provider.getBalance(attacker.target);
  await (await attacker.attack({ gasLimit: 5000000 })).wait();
  const after = await hre.ethers.provider.getBalance(attacker.target);
  const result = {
    attackerReceived: after - before,
    attackerCreditAfter: await dao.queryCredit.staticCall(attacker.target),
    donorCreditAfter: await dao.queryCredit.staticCall(donor.address),
    daoBalanceAfter: await hre.ethers.provider.getBalance(dao.target),
    callbacks: await attacker.callbacks.staticCall(),
  };
  assert.equal(result.callbacks, 1n);
  assert.equal(result.donorCreditAfter, ether);
  if (variant === "V0") {
    assert.equal(result.attackerReceived, 2n * ether);
    assert.equal(result.daoBalanceAfter, 0n);
    assert.equal(result.attackerCreditAfter, (1n << 256n) - ether);
  } else {
    assert.equal(result.attackerReceived, ether);
    assert.equal(result.daoBalanceAfter, ether);
    assert.equal(result.attackerCreditAfter, 0n);
  }
  return result;
}

async function rejectedCallback(variant, donor) {
  const dao = await deploy(variant, donor);
  const reject = await deploy("RejectEther", donor, [dao.target]);
  await (await dao.donate(reject.target, { value: ether })).wait();
  await (await reject.withdraw({ gasLimit: 5000000 })).wait();
  const result = {
    recipientBalance: await hre.ethers.provider.getBalance(reject.target),
    recipientCreditAfter: await dao.queryCredit.staticCall(reject.target),
    daoBalanceAfter: await hre.ethers.provider.getBalance(dao.target),
  };
  assert.equal(result.recipientBalance, 0n);
  assert.equal(result.recipientCreditAfter, 0n);
  assert.equal(result.daoBalanceAfter, ether);
  return result;
}

async function main() {
  const runId = process.env.SIMPLE_DAO_RUN_ID;
  if (!/^r[12]$/.test(runId || "")) {
    throw new Error("Set SIMPLE_DAO_RUN_ID to r1 or r2");
  }
  const [donor] = await hre.ethers.getSigners();
  const report = {
    runId,
    evm: "Hardhat shanghai",
    chainId: (await hre.ethers.provider.getNetwork()).chainId,
    cases: {},
  };
  for (const variant of ["V0", "V1", "V2", "V3"]) {
    report.cases[variant] = {
      ordinary: await ordinary(variant, donor),
      nested: await nested(variant, donor),
      rejectedCallback: await rejectedCallback(variant, donor),
    };
  }
  const output = path.join(base, `behavioral_results_${runId}.json`);
  fs.writeFileSync(output, JSON.stringify(report, (_key, value) =>
    typeof value === "bigint" ? value.toString() : value, 2) + "\n");
  console.log(`PASS 4 variants × 3 scenarios; results: ${output}`);
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
