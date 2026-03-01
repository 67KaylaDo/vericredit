const hre = require("hardhat");
const { isHexString, zeroPadValue } = hre.ethers;

function toBytes32(hexNo0x) {
  const hex = hexNo0x.startsWith("0x") ? hexNo0x : "0x" + hexNo0x;
  if (!isHexString(hex)) throw new Error(`Not hex: ${hex}`);
  return zeroPadValue(hex, 32); // ensure bytes32
}

async function main() {
  const CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3";

  // MUST be 64 hex chars each (no 0x needed, but allowed)
  const identityHashHex = "d51562a17b7fbc6288794563ac5edd0693974a85d9a128b535073f466c21ac59";
  const evidenceHashHex = "81b9d0e214240b5e4d3ba6832bd1bb85ce5b60ee90fcdb19f0be85c84ddac059";

  const aiRiskScore = 67;
  const ahpScore = 70;
  const humanConsensusUsed = true;

  const identityHash = toBytes32(identityHashHex);
  const evidenceHash = toBytes32(evidenceHashHex);

  // attach using ABI + address (no name resolution)
  const Contract = await hre.ethers.getContractFactory("VeriCreditRegistry");
  const contract = Contract.attach(CONTRACT_ADDRESS);

  const tx = await contract.recordVerification(
    identityHash,
    aiRiskScore,
    ahpScore,
    humanConsensusUsed,
    evidenceHash
  );

  console.log("TX sent:", tx.hash);
  const receipt = await tx.wait();
  console.log("✅ Mined in block:", receipt.blockNumber);

  const stored = await contract.records(identityHash);
  console.log("📌 Stored Record:", stored);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});