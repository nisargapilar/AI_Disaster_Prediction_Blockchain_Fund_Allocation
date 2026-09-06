import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const contractAddress = "0x5D556C4307932FF613c80dEB8dF600378E401EC5";
  const disasterRelief = await ethers.getContractAt("DisasterRelief", contractAddress);

  // Simulate a mock Aadhaar-style ID a field worker would type in
  // (in the real app this comes from the form field, never stored raw)
  const mockAadhaarId = "123456789012"; // 12-digit mock ID
  const beneficiaryHash = ethers.keccak256(ethers.toUtf8Bytes(mockAadhaarId));
  const distributionRecordId = "DIST-RECORD-001";

  console.log("Mock ID (never stored on-chain):", mockAadhaarId);
  console.log("Hash being stored:", beneficiaryHash);

  // Check it's not already verified
  const alreadyVerified = await disasterRelief.isBeneficiaryVerified(beneficiaryHash);
  console.log("Already verified before call?", alreadyVerified);

  if (alreadyVerified) {
    console.log("This mock ID was already verified in a previous run — try a different ID.");
    return;
  }

  console.log(`Verifying beneficiary for record ${distributionRecordId}...`);
  const tx = await disasterRelief.verifyBeneficiary(beneficiaryHash, distributionRecordId);
  console.log("Transaction sent:", tx.hash);

  const receipt = await tx.wait();
  console.log("Confirmed in block:", receipt?.blockNumber);

  // Confirm it now reads as verified
  const nowVerified = await disasterRelief.isBeneficiaryVerified(beneficiaryHash);
  console.log("Verified after call?", nowVerified);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});