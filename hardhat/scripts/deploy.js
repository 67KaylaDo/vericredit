const hre = require("hardhat");

async function main() {
  const Factory = await hre.ethers.getContractFactory("VeriCreditRegistry");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();

  console.log("VeriCreditRegistry deployed to:", await contract.getAddress());
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});