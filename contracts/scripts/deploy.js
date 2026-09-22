const { ethers } = require("hardhat");

async function main() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("🚀 Eco Nojin - Deploying EcoCoin Protocol");
  console.log("═══════════════════════════════════════════════════════\n");

  const [deployer] = await ethers.getSigners();
  console.log("📍 Deployer address:", deployer.address);
  console.log("💰 Deployer balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH\n");

  // ═══════════════════════════════════════════════════════
  // Genesis Configuration
  // ═══════════════════════════════════════════════════════
  const minDurations = [30, 90, 180, 365, 540, 0];
  const activityThresholds = [0, 1000, 10000, 50000, 0, 0];
  const minAccuracies = [0, 9500, 9800, 10000, 10000, 10000];
  const maxDiscrepancies = [0, 200, 100, 50, 0, 0];
  const oracleUptimes = [0, 9500, 9950, 9950, 9950, 9950];
  const requiredRegions = [0, 3, 3, 5, 5, 5];
  const emissionCaps = [0, 10000000, 50000000, 200000000, 500000000, 100000000000];

  const network = await ethers.provider.getNetwork();
  console.log(`Network: ${network.name} (Chain ID: ${network.chainId})`);
  console.log("Deployer:", deployer.address);

  // ═══════════════════════════════════════════════════════
  // 1. Deploy PhaseGate (no dependencies)
  // ═══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying PhaseGate...");
  
  const PhaseGate = await ethers.getContractFactory("PhaseGate");
  const phaseGate = await PhaseGate.deploy(
    minDurations,
    [0, 1000, 10000, 50000, 0, 0], // activityThresholds
    [0, 9500, 9800, 10000, 10000, 10000], // minAccuracies
    [0, 200, 100, 50, 0, 0], // maxDiscrepancies
    [0, 9500, 9950, 9950, 9950, 9950], // oracleUptimes
    [0, 3, 3, 5, 5, 5], // requiredRegions
    [0, 10000000, 50000000, 200000000, 500000000, 100000000000] // emissionCaps
  );
  await phaseGate.waitForDeployment();
  const phaseGateAddress = await phaseGate.getAddress();
  console.log("✅ PhaseGate deployed at:", phaseGateAddress);

  // ═══════════════════════════════════════════════════════
  // 2. Deploy EcoCoin (no deps)
  // ═══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying EcoCoin (ECO)...");
  
  const EcoCoin = await ethers.getContractFactory("EcoCoin");
  const ecoCoin = await EcoCoin.deploy();
  await ecoCoin.waitForDeployment();
  const ecoCoinAddress = await ecoCoin.getAddress();
  console.log("✅ EcoCoin deployed at:", ecoCoinAddress);

  // ═══════════════════════════════════════════════════════
  // 3. Deploy ImpactCertificate (SBT)
  // ══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying ImpactCertificate (ENIC)...");
  
  const ImpactCertificate = await ethers.getContractFactory("ImpactCertificate");
  const impactCertificate = await ImpactCertificate.deploy();
  await impactCertificate.waitForDeployment();
  const impactCertificateAddress = await impactCertificate.getAddress();
  console.log("✅ ImpactCertificate deployed at:", impactCertificateAddress);

  // ══════════════════════════════════════════════════════
  // 4. Deploy ImpactOracle (depends on ImpactCertificate, EcoCoin, PhaseGate)
  // ══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying ImpactOracle...");
  
  const ImpactOracle = await ethers.getContractFactory("ImpactOracle");
  const impactOracle = await ImpactOracle.deploy(
    impactCertificateAddress,
    ecoCoinAddress,
    phaseGateAddress
  );
  await impactOracle.waitForDeployment();
  const impactOracleAddress = await impactOracle.getAddress();
  console.log("✅ ImpactOracle deployed at:", impactOracleAddress);

  // ══════════════════════════════════════════════════════
  // 5. Deploy EcoTreasury (depends on EcoCoin)
  // ═════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying EcoTreasury...");
  
  const EcoTreasury = await ethers.getContractFactory("EcoTreasury");
  const ecoTreasury = await EcoTreasury.deploy(ecoCoinAddress, deployer.address);
  await ecoTreasury.waitForDeployment();
  const ecoTreasuryAddress = await ecoTreasury.getAddress();
  console.log("✅ EcoTreasury deployed at:", ecoTreasuryAddress);

  // ══════════════════════════════════════════════════════
  // 6. Deploy EcosystemFund (depends on EcoCoin)
  // ═════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying EcosystemFund...");
  
  const EcosystemFund = await ethers.getContractFactory("EcosystemFund");
  const ecosystemFund = await EcosystemFund.deploy(ecoCoinAddress);
  await ecosystemFund.waitForDeployment();
  const ecosystemFundAddress = await ecosystemFund.getAddress();
  console.log("✅ EcosystemFund deployed at:", ecosystemFundAddress);

  // ══════════════════════════════════════════════════════
  // 6. Deploy MintController (depends on all above)
  // ══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("📦 Deploying MintController...");
  
  const MintController = await ethers.getContractFactory("MintController");
  const mintController = await MintController.deploy(
    ecoCoinAddress,
    impactCertificateAddress, // not used in constructor but kept for reference
    phaseGateAddress,
    impactOracleAddress,
    ecoTreasuryAddress,
    ecosystemFundAddress
  );
  await mintController.waitForDeployment();
  const mintControllerAddress = await mintController.getAddress();
  console.log("✅ MintController deployed at:", mintControllerAddress);

  // ══════════════════════════════════════════════════════
  // Post-deployment setup
  // ══════════════════════════════════════════════════════
  console.log("\n───────────────────────────────────────────────────────");
  console.log("🔧 Post-deployment configuration...");
  
  // Transfer MINTER_ROLE to MintController
  const EcoCoin = await ethers.getContractFactory("EcoCoin");
  const ecoCoin = await EcoCoin.attach(ecoCoinAddress);
  const MINTER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE"));
  await ecoCoin.grantRole(ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE")), mintControllerAddress);
  await ecoCoin.revokeRole(ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE")), deployer.address);
  console.log("✅ MINTER_ROLE transferred to MintController");

  // Transfer MINTER_ROLE in ImpactCertificate to ImpactOracle
  const ImpactCertificate = await ethers.getContractFactory("ImpactCertificate");
  const impactCert = await ImpactCertificate.attach(impactCertificateAddress);
  const IC_MINTER = ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE"));
  await impactCert.grantRole(IC_MINTER, impactOracleAddress);
  await impactCert.revokeRole(IC_MINTER, deployer.address);
  console.log("✅ ImpactCertificate MINTER_ROLE transferred to ImpactOracle");

  // Transfer PHASE_GATE_ROLE in EcoCoin to PhaseGate
  const PHASE_GATE_ROLE = ethers.keccak256(ethers.toUtf8Bytes("PHASE_GATE_ROLE"));
  await ecoCoin.grantRole(PHASE_GATE_ROLE, phaseGateAddress);
  await ecoCoin.revokeRole(PHASE_GATE_ROLE, deployer.address);
  console.log("✅ EcoCoin PHASE_GATE_ROLE transferred to PhaseGate");

  // Grant ORACLE_ROLE in ImpactOracle to deployer (for initial testing)
  const ImpactOracleContract = await ethers.getContractFactory("ImpactOracle");
  const impactOracle = await ImpactOracleContract.attach(impactOracleAddress);
  const ORACLE_ROLE = ethers.keccak256(ethers.toUtf8Bytes("ORACLE_ROLE"));
  await impactOracle.grantRole(ORACLE_ROLE, deployer.address);
  console.log("✅ ORACLE_ROLE granted to deployer");

  // Grant PHASE_CONTROLLER to PhaseGate
  const PhaseGateContract = await ethers.getContractFactory("PhaseGate");
  const phaseGate = await PhaseGateContract.attach(phaseGateAddress);
  const PHASE_CTRL = ethers.keccak256(ethers.toUtf8Bytes("PHASE_CONTROLLER_ROLE"));
  await phaseGate.grantRole(ethers.keccak256(ethers.toUtf8Bytes("PHASE_CONTROLLER_ROLE")), deployer.address);
  console.log("✅ PHASE_CONTROLLER_ROLE granted to deployer");

  // ═══════════════════════════════════════════════════════
  // Summary
  // ═══════════════════════════════════════════════════════
  const networkInfo = await ethers.provider.getNetwork();
  console.log("\n═══════════════════════════════════════════════════════");
  console.log("📋 Deployment Summary");
  console.log("═══════════════════════════════════════════════════════");
  console.log(`Network:          ${networkInfo.name} (Chain ID: ${networkInfo.chainId})`);
  console.log(`Deployer:         ${deployer.address}`);
  console.log("");
  console.log(`PhaseGate:        ${phaseGateAddress}`);
  console.log(`EcoCoin (ECO):    ${ecoCoinAddress}`);
  console.log(`ImpactCertificate: ${impactCertificateAddress}`);
  console.log(`ImpactOracle:     ${impactOracleAddress}`);
  console.log(`EcoTreasury:      ${ecoTreasuryAddress}`);
  console.log(`EcosystemFund:    ${ecosystemFundAddress}`);
  console.log(`MintController:   ${mintControllerAddress}`);
  console.log("");
  console.log("═══════════════════════════════════════════════════════");
  console.log("🔍 To verify contracts on Polygonscan:");
  console.log(`   npx hardhat verify --network amoy ${phaseGateAddress} [30,90,180,365,540,0] [0,1000,10000,50000,0,0] [0,9500,9800,10000,10000,10000] [0,200,100,50,0,0] [0,9500,9950,9950,9950,9950] [0,3,3,5,5,5] [0,10000000,50000000,200000000,500000000,100000000000]`);
  console.log(`   npx hardhat verify --network amoy ${ecoCoinAddress}`);
  console.log(`   npx hardhat verify --network amoy ${impactCertificateAddress}`);
  console.log(`   npx hardhat verify --network amoy ${impactOracleAddress} ${impactCertificateAddress} ${ecoCoinAddress} ${phaseGateAddress}`);
  console.log(`   npx hardhat verify --network amoy ${ecoTreasuryAddress} ${ecoCoinAddress} ${deployer.address}`);
  console.log(`   npx hardhat verify --network amoy ${ecosystemFundAddress} ${ecoCoinAddress}`);
  console.log(`   npx hardhat verify --network amoy ${mintControllerAddress} ${ecoCoinAddress} 0x0 ${phaseGateAddress} ${impactOracleAddress} ${ecoTreasuryAddress} ${ecosystemFundAddress}`);
  console.log("");
  console.log("💾 Save these addresses to your .env file:");
  console.log(`   PHASE_GATE_ADDRESS=${phaseGateAddress}`);
  console.log(`   ECO_COIN_ADDRESS=${ecoCoinAddress}`);
  console.log(`   IMPACT_CERTIFICATE_ADDRESS=${impactCertificateAddress}`);
  console.log(`   IMPACT_ORACLE_ADDRESS=${impactOracleAddress}`);
  console.log(`   ECO_TREASURY_ADDRESS=${ecoTreasuryAddress}`);
  console.log(`   ECOSYSTEM_FUND_ADDRESS=${ecosystemFundAddress}`);
  console.log(`   MINT_CONTROLLER_ADDRESS=${mintControllerAddress}`);
  console.log("═══════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });