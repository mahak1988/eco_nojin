const { ethers } = require("hardhat");

async function main() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("🚀 Eco Nojin - Deploying Smart Contracts");
  console.log("═══════════════════════════════════════════════════════\n");

  const [deployer] = await ethers.getSigners();
  console.log("📍 Deployer address:", deployer.address);
  console.log("💰 Deployer balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH\n");

  // ═══════════════════════════════════════════════════════
  // Deploy CarbonCredit
  // ═══════════════════════════════════════════════════════
  console.log("───────────────────────────────────────────────────────");
  console.log("📦 Deploying CarbonCredit (ENCC)...");
  
  const CarbonCredit = await ethers.getContractFactory("CarbonCredit");
  const carbonCredit = await CarbonCredit.deploy();
  await carbonCredit.waitForDeployment();
  
  const carbonCreditAddress = await carbonCredit.getAddress();
  console.log("✅ CarbonCredit deployed at:", carbonCreditAddress);
  console.log("   Symbol: ENCC");
  console.log("   Max Supply: 1,000,000,000 ENCC");

  // ═══════════════════════════════════════════════════════
  // Deploy LandscapeFund
  // ═══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying LandscapeFund...");
  
  const LandscapeFund = await ethers.getContractFactory("LandscapeFund");
  const landscapeFund = await LandscapeFund.deploy();
  await landscapeFund.waitForDeployment();
  
  const landscapeFundAddress = await landscapeFund.getAddress();
  console.log("✅ LandscapeFund deployed at:", landscapeFundAddress);
  console.log("   Default Fee: 1% (100 bps)");
  console.log("   Max Fee: 5% (500 bps)");

  // ═══════════════════════════════════════════════════════
  // Summary
  // ═══════════════════════════════════════════════════════
  console.log("\n═══════════════════════════════════════════════════════");
  console.log("📋 Deployment Summary");
  console.log("═══════════════════════════════════════════════════════");
  console.log(`Network:          ${(await ethers.provider.getNetwork()).name}`);
  console.log(`Chain ID:         ${(await ethers.provider.getNetwork()).chainId}`);
  console.log(`Deployer:         ${deployer.address}`);
  console.log(`CarbonCredit:     ${carbonCreditAddress}`);
  console.log(`LandscapeFund:    ${landscapeFundAddress}`);
  console.log("═══════════════════════════════════════════════════════\n");

  // ═══════════════════════════════════════════════════════
  // Verification Instructions
  // ═══════════════════════════════════════════════════════
  console.log("🔍 To verify contracts on Polygonscan:");
  console.log(`   npx hardhat verify --network mumbai ${carbonCreditAddress}`);
  console.log(`   npx hardhat verify --network mumbai ${landscapeFundAddress}`);
  console.log("\n💾 Save these addresses to your .env file:");
  console.log(`   CARBON_CREDIT_ADDRESS=${carbonCreditAddress}`);
  console.log(`   LANDSCAPE_FUND_ADDRESS=${landscapeFundAddress}`);
  console.log("═══════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
