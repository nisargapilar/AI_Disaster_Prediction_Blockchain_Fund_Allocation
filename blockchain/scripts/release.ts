import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const contractAddress = "0x5D556C4307932FF613c80dEB8dF600378E401EC5";
  const disasterRelief = await ethers.getContractAt("DisasterRelief", contractAddress);

  // Check balance before
  const balanceBefore = await disasterRelief.contractBalance();
  console.log("Contract balance before:", ethers.formatEther(balanceBefore), "POL");

  // For this test, release a small amount to your own wallet
  // (in production this would be the NGO/govt wallet)
  const [signer] = await ethers.getSigners();
  const ngoWallet = signer.address; // using your own address as a stand-in NGO wallet for the test
  const amount = ethers.parseEther("0.005"); // release 0.005 of the 0.02 POL
  const eventId = "TEST-EVENT-001";

  console.log(`Releasing ${ethers.formatEther(amount)} POL to ${ngoWallet}...`);

  const tx = await disasterRelief.releaseFunds(ngoWallet, amount, eventId);
  console.log("Transaction sent:", tx.hash);

  const receipt = await tx.wait();
  console.log("Confirmed in block:", receipt?.blockNumber);

  // Check balance after
  const balanceAfter = await disasterRelief.contractBalance();
  console.log("Contract balance after:", ethers.formatEther(balanceAfter), "POL");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});