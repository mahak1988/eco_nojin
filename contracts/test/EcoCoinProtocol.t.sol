// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/EcoCoin.sol";
import "../src/PhaseGate.sol";
import "../src/ImpactOracle.sol";
import "../src/ImpactCertificate.sol";
import "../src/MintController.sol";
import "../src/EcoGovernance.sol";
import "../src/EcoTreasury.sol";
import "../src/EcosystemFund.sol";
import "../src/EcoWalletBridge.sol";

/**
 * @title EcoCoin Protocol Test Suite
 * @notice Comprehensive tests for EcoCoin protocol contracts
 */
contract EcoCoinProtocolTest is Test {
    EcoCoin ecoCoin;
    PhaseGate phaseGate;
    ImpactOracle impactOracle;
    ImpactCertificate impactCertificate;
    MintController mintController;
    EcoGovernance governance;
    EcoTreasury treasury;
    EcosystemFund ecosystemFund;
    EcoWalletBridge walletBridge;

    address admin = address(0x1);
    address oracle = address(0x2);
    address producer = address(0x3);
    address verifier = address(0x4);
    address governanceAddr = address(0x5);

    // Phase configuration
    uint256[6] minDurations = [1, 30, 90, 180, 365, 730]; // days
    uint256[6] activityThresholds = [0, 100, 500, 1000, 5000, 10000];
    uint256[6] minAccuracies = [0, 9000, 9500, 9700, 9800, 9900];
    uint256[6] maxDiscrepancies = [10000, 5000, 2000, 1000, 500, 200];
    uint256[6] oracleUptimes = [0, 9900, 9950, 9970, 9990, 9995];
    uint256[6] requiredRegions = [0, 3, 5, 10, 20, 30];
    uint256[6] emissionCaps = [0, 1000000e18, 5000000e18, 20000000e18, 50000000e18, 100000000e18];

    function setUp() public {
        vm.startPrank(admin);

        // Deploy contracts
        phaseGate = new PhaseGate(
            minDurations,
            activityThresholds,
            minAccuracies,
            maxDiscrepancies,
            oracleUptimes,
            requiredRegions,
            emissionCaps
        );

        ecoCoin = new EcoCoin();
        impactCertificate = new ImpactCertificate();
        impactOracle = new ImpactOracle(
            address(impactCertificate),
            address(ecoCoin),
            address(phaseGate)
        );
        treasury = new EcoTreasury();
        ecosystemFund = new EcosystemFund();
        mintController = new MintController(
            address(ecoCoin),
            address(impactCertificate),
            address(phaseGate),
            address(impactOracle),
            address(treasury),
            address(0) // ecosystemFund placeholder
        );
        walletBridge = new EcoWalletBridge(
            address(ecoCoin),
            admin,
            10000e18, // max claim per tx
            0, // migration not started
            0  // migration not ended
        );

        governance = new EcoGovernance(
            address(ecoCoin),
            address(impactCertificate),
            address(phaseGate),
            address(impactOracle),
            address(mintController),
            address(treasury),
            address(0), // ecosystemFund
            address(walletBridge),
            admin
        );

        // Setup roles
        ecoCoin.transferProtocolRoles(address(mintController), address(phaseGate), address(governance));
        impactCertificate._grantRole(impactCertificate.REVOKER_ROLE(), address(governance));
        impactOracle._grantRole(impactOracle.ORACLE_ROLE(), oracle);
        impactOracle._grantRole(impactOracle.DISPUTE_ROLE(), address(governance));
        phaseGate._grantRole(phaseGate.PHASE_CONTROLLER(), address(governance));
        mintController._grantRole(mintController.ORACLE_ROLE(), oracle);

        vm.stopPrank();
    }

    // ========== EcoCoin Tests ==========

    function testEcoCoinDeployment() public {
        assertEq(ecoCoin.name(), "Eco Nojin EcoCoin");
        assertEq(ecoCoin.symbol(), "ECO");
        assertEq(ecoCoin.HARD_CAP(), 100_000_000_000 * 10**18);
        assertEq(ecoCoin.burnRate(), 200);
        assertTrue(ecoCoin.hasRole(ecoCoin.DEFAULT_ADMIN_ROLE(), admin));
    }

    function testEcoCoinMint() public {
        vm.startPrank(admin);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), admin);

        uint256 amount = 10000e18;
        ecoCoin.mint(producer, amount, 1, 2);

        assertEq(ecoCoin.balanceOf(producer), 9800e18); // 2% burned
        assertEq(ecoCoin.totalSupply(), 9800e18);
        vm.stopPrank();
    }

    function testEcoCoinBurn() public {
        vm.startPrank(admin);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), admin);

        ecoCoin.mint(producer, 10000e18, 1, 2);
        uint256 beforeSupply = ecoCoin.totalSupply();

        ecoCoin.burn(1000e18);
        assertEq(ecoCoin.totalSupply(), beforeSupply - 1000e18);
        vm.stopPrank();
    }

    function testEcoCoinPhaseGatedTransfers() public {
        vm.startPrank(admin);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), admin);

        ecoCoin.mint(producer, 10000e18, 1, 2);
        ecoCoin.mint(address(0x10), 10000e18, 2, 2);

        // Phase 2: transfers restricted
        vm.expectRevert("Transfers restricted in current phase");
        ecoCoin.transfer(address(0x10), 1000e18);

        // Activate phase 3
        governance.activateNextPhase(); // Phase 3

        // Phase 3: transfers allowed
        ecoCoin.transfer(address(0x10), 1000e18);
        assertEq(ecoCoin.balanceOf(address(0x10)), 1000e18);

        vm.stopPrank();
    }

    function testEcoCoinPermit() public {
        vm.startPrank(admin);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), admin);

        ecoCoin.mint(producer, 10000e18, 1, 2);

        // Test EIP-2612 permit
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(
            producer,
            ecoCoin.DOMAIN_SEPARATOR(),
            keccak256(abi.encode(
                ecoCoin.PERMIT_TYPEHASH(),
                producer,
                address(0x10),
                1000e18,
                ecoCoin.nonces(producer),
                block.timestamp + 1 hours
            ))
        );

        ecoCoin.permit(producer, address(0x10), 1000e18, block.timestamp + 1 hours, v, r, s);
        assertEq(ecoCoin.allowance(producer, address(0x10)), 1000e18);
        vm.stopPrank();
    }

    function testEcoCoinHardCap() public {
        vm.startPrank(admin);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), admin);

        // Try to mint beyond hard cap
        uint256 nearCap = ecoCoin.HARD_CAP() - 1000e18;
        ecoCoin.mint(producer, nearCap, 1, 2);

        vm.expectRevert("Hard cap exceeded");
        ecoCoin.mint(producer, 2000e18, 2, 2);
        vm.stopPrank();
    }

    function testEcoCoinBurnRateUpdate() public {
        vm.startPrank(admin);
        ecoCoin.setBurnRate(500); // 5%
        assertEq(ecoCoin.burnRate(), 500);

        vm.expectRevert("Burn rate max 10%");
        ecoCoin.setBurnRate(2000);
        vm.stopPrank();
    }

    function testEcoCoinRoleTransfer() public {
        vm.startPrank(admin);
        ecoCoin.transferProtocolRoles(admin, admin, admin);
        // Should emit event
        vm.stopPrank();
    }

    // ========== PhaseGate Tests ==========

    function testPhaseGateInitialization() public {
        assertEq(phaseGate.currentPhase(), 0);
        assertEq(phaseGate.PHASE_COUNT(), 6);
        assertTrue(phaseGate.isPhaseActive(0));
        assertFalse(phaseGate.isPhaseActive(1));
    }

    function testPhaseGateSequentialActivation() public {
        vm.startPrank(admin);
        // Try to skip phase - should fail
        vm.expectRevert("Phases must activate sequentially");
        phaseGate.activatePhase(2);
        vm.stopPrank();
    }

    function testPhaseGateThresholds() public {
        // Activate phase 1 (genesis)
        vm.warp(block.timestamp + 2 days);
        vm.startPrank(admin);
        phaseGate.activatePhase(1);
        assertTrue(phaseGate.isPhaseActive(1));

        // Check thresholds
        (bool active, , , uint256 activities, uint256 verified, uint256 discrepancy) = phaseGate.currentPhaseInfo();
        assertEq(activities, 0);
        assertEq(verified, 0);
        vm.stopPrank();
    }

    function testPhaseGateEmissionCap() public {
        vm.startPrank(admin);
        phaseGate.setEmissionCap(2, 5000000e18);
        assertEq(phaseGate.getEmissionCap(2), 5000000e18);
        assertEq(phaseGate.getEmissionUsed(2), 0);

        // Record emission
        phaseGate.recordEmission(2, 1000e18);
        assertEq(phaseGate.getEmissionUsed(2), 1000e18);

        // Check cap
        assertTrue(phaseGate.checkEmissionCap(2, 1000e18));
        vm.stopPrank();
    }

    function testPhaseGateMinDuration() public {
        // Try to activate phase 1 before min duration
        vm.startPrank(admin);
        vm.expectRevert("Minimum duration not elapsed");
        phaseGate.activatePhase(1);
        vm.stopPrank();

        // Wait for min duration
        vm.warp(block.timestamp + 2 days);
        vm.startPrank(admin);
        phaseGate.activatePhase(1);
        assertTrue(phaseGate.isPhaseActive(1));
        vm.stopPrank();
    }

    // ========== ImpactOracle Tests ==========

    function testOracleRegistration() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        assertTrue(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).active);
        assertEq(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).stake, 1000e18);
        vm.stopPrank();
    }

    function testAttestationSubmission() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        vm.stopPrank();

        vm.startPrank(verifier);
        bytes32 activityId = keccak256("activity1");
        impactOracle.submitAttestation(
            activityId,
            keccak256("evidence1"),
            0, // satellite
            90, // confidence
            block.timestamp,
            "0x1234"
        );
        vm.stopPrank();

        // Check attestation recorded
        bytes32 key = keccak256(abi.encodePacked(activityId, verifier));
        assertTrue(impactOracle.attestations(key).processed);
    }

    function testImpactReportAndChallenge() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        vm.stopPrank();

        vm.startPrank(verifier);
        bytes32 activityId = keccak256("activity2");
        impactOracle.submitImpactReport(
            activityId,
            keccak256("evidence"),
            0, // satellite
            90,
            keccak256("impact_data"),
            keccak256("evidence_ipfs"),
            1 // methodology version
        );
        vm.stopPrank();

        // Challenge
        vm.startPrank(address(0x3));
        impactOracle.challengeActivity(keccak256("activity2"));
        assertTrue(impactOracle.impactReports(keccak256("activity2")).challenged);
        vm.stopPrank();

        // Resolve challenge
        vm.startPrank(admin);
        impactOracle.resolveChallenge(keccak256("activity2"), true);
        vm.stopPrank();
    }

    function testMetricsFinalization() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        impactOracle.registerOracle(address(0x3), 80, 85, 500e18);
        impactOracle.registerOracle(address(0x4), 90, 95, 500e18);
        vm.stopPrank();

        vm.startPrank(verifier);
        bytes32 activityId = keccak256("activity3");
        impactOracle.submitAttestation(activityId, keccak256("ev1"), 0, 90, block.timestamp, "0x1");
        vm.stopPrank();

        vm.startPrank(address(0x3));
        impactOracle.submitAttestation(activityId, keccak256("ev2"), 0, 95, block.timestamp, "0x2");
        vm.stopPrank();

        vm.startPrank(address(0x4));
        impactOracle.submitAttestation(activityId, keccak256("ev3"), 1, 85, block.timestamp, "0x3");
        vm.stopPrank();

        // Finalize
        vm.startPrank(admin);
        // Need to submit impact report first
        impactOracle.submitImpactReport(
            activityId,
            keccak256("ev"),
            0, 90,
            keccak256("impact"),
            keccak256("ev_ipfs"),
            1
        );
        // Wait for challenge window
        vm.warp(block.timestamp + 8 days);
        impactOracle.finalizeMetrics(activityId);
        vm.stopPrank();
    }

    function testSlashingLogic() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        vm.stopPrank();

        // Slash node
        vm.startPrank(admin);
        impactOracle.slashNode(verifier, 500e18);

        // Check slashed
        bytes32 nodeKey = keccak256(abi.encodePacked(verifier));
        assertTrue(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).slashed);
        assertFalse(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).active);
        assertEq(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).stake, 500e18);
        vm.stopPrank();
    }

    function testStakeAddition() public {
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        vm.stopPrank();

        vm.startPrank(verifier);
        impactOracle.addStake(verifier, 500e18);

        assertEq(impactOracle.oracleNodes(keccak256(abi.encodePacked(verifier))).stake, 1500e18);
        vm.stopPrank();
    }

    // ========== ImpactCertificate Tests ==========

    function testCertificateMinting() public {
        vm.startPrank(admin);
        impactCertificate._grantRole(impactCertificate.MINTER_ROLE(), admin);

        uint256 tokenId = impactCertificate.mintCertificate(
            producer,
            keccak256("evidence"),
            90,
            1,
            keccak256("impact"),
            "ipfs://metadata"
        );

        assertEq(impactCertificate.balanceOf(producer), 1);
        assertEq(impactCertificate.ownerOf(0), producer);
        assertTrue(impactCertificate.activityData(0).status == 1); // provisional
    }

    function testCertificateNonTransferable() public {
        vm.startPrank(admin);
        impactCertificate._grantRole(impactCertificate.MINTER_ROLE(), admin);

        impactCertificate.mintCertificate(producer, keccak256("ev"), 90, 1, keccak256("impact"), "ipfs://");

        vm.startPrank(producer);
        vm.expectRevert("ImpactCertificate: non-transferable");
        impactCertificate.transferFrom(producer, address(0x10), 0);
    }

    function testCertificateStatusUpdates() public {
        vm.startPrank(admin);
        impactCertificate._grantRole(impactCertificate.MINTER_ROLE(), admin);

        impactCertificate.mintCertificate(producer, keccak256("ev"), 90, 1, keccak256("impact"), "ipfs://");

        // Update to verified
        impactCertificate.updateStatus(0, 2); // verified
        assertEq(impactCertificate.activityData(0).status, 2);

        // Dispute
        vm.startPrank(producer);
        impactCertificate.dispute(0);
        assertEq(impactCertificate.activityData(0).status, 3);

        // Resolve
        vm.startPrank(admin);
        impactCertificate.resolveDispute(0, true);
        assertEq(impactCertificate.activityData(0).status, 2);
    }

    // ========== MintController Tests ==========

    function testMintControllerDistribution() public {
        vm.startPrank(admin);
        // Grant oracle role
        mintController._grantRole(mintController.ORACLE_ROLE(), admin);

        // Activate phase 2
        governance.activateNextPhase(); // Phase 1
        governance.activateNextPhase(); // Phase 2

        vm.stopPrank();

        // Request mint
        MintController.MintRequest memory request = MintController.MintRequest({
            activityId: keccak256("activity1"),
            recipient: producer,
            impactScore: 10000,
            confidence: 90,
            phase: 2,
            timestamp: block.timestamp,
            impactHash: keccak256("impact")
        );

        vm.startPrank(admin);
        uint256 minted = mintController.requestMint(request);
        vm.stopPrank();

        // Check distribution: 70/15/10/5 after 2% burn
        // net = 10000 * (1 - 0.02) = 9800
        // producer = 9800 * 0.7 = 6860
        // platform = 9800 * 0.15 = 1470
        // ecosystem = 9800 * 0.1 = 980
        // governance = 9800 * 0.05 = 490
        // Total = 6860 + 1470 + 980 + 490 = 9800
        assertEq(minted, 9800e18);
    }

    function testMintControllerPhaseCap() public {
        vm.startPrank(admin);
        mintController._grantRole(mintController.ORACLE_ROLE(), admin);
        governance.activateNextPhase(); // P1
        governance.activateNextPhase(); // P2
        vm.stopPrank();

        // Set phase cap
        governance.setPhaseGateConfig(2, 1000e18);

        // First mint - should succeed
        MintController.MintRequest memory request1 = MintController.MintRequest({
            activityId: keccak256("act1"),
            recipient: producer,
            impactScore: 10000,
            confidence: 100,
            phase: 2,
            timestamp: block.timestamp,
            impactHash: keccak256("impact")
        });

        vm.startPrank(admin);
        mintController.requestMint(request1);
        vm.stopPrank();

        // Second mint - should be capped
        MintController.MintRequest memory request2 = MintController.MintRequest({
            activityId: keccak256("act2"),
            recipient: address(0x3),
            impactScore: 10000,
            confidence: 100,
            phase: 2,
            timestamp: block.timestamp,
            impactHash: keccak256("impact2")
        });

        vm.startPrank(admin);
        mintController.requestMint(request2);
        // Second mint should return reduced amount (cap remaining)
        // but the contract just returns producer amount, need to check balance
        assertEq(ecoCoin.totalSupply(), 1000e18); // capped at phase cap
        vm.stopPrank();
    }

    function testMintControllerDuplicatePrevention() public {
        vm.startPrank(admin);
        mintController._grantRole(mintController.ORACLE_ROLE(), admin);
        governance.activateNextPhase();
        governance.activateNextPhase();
        vm.stopPrank();

        MintController.MintRequest memory request = MintController.MintRequest({
            activityId: keccak256("dup"),
            recipient: producer,
            impactScore: 10000,
            confidence: 90,
            phase: 2,
            timestamp: block.timestamp,
            impactHash: keccak256("impact")
        });

        vm.startPrank(admin);
        mintController.requestMint(request);
        vm.stopPrank();

        // Try duplicate
        vm.startPrank(admin);
        vm.expectRevert("Already minted");
        mintController.requestMint(request);
    }

    // ========== PhaseGate Tests ==========

    function testPhaseGateOracleUptime() public {
        vm.startPrank(verifier);
        phaseGate.reportOracleUptime(9990); // 99.9%
        vm.stopPrank();

        (, , , , , , uint256 uptimeSum, uint256 checks) = phaseGate.getPhaseState(0);
        assertEq(checks, 1);
        assertEq(uptimeSum, 9990);
    }

    function testPhaseGateDiscrepancy() public {
        vm.startPrank(verifier);
        phaseGate.recordDiscrepancy();
        vm.stopPrank();

        (, , , , , uint256 discrepancy, ) = phaseGate.getPhaseState(0);
        assertEq(discrepancy, 1);
    }

    // ========== EcoWalletBridge Tests ==========

    function testBridgeMerkleRoot() public {
        vm.startPrank(admin);
        bytes32 root = keccak256("merkle_root");
        walletBridge.updateMerkleRoot(root);
        assertEq(walletBridge.merkleRoot(), root);
        vm.stopPrank();
    }

    function testBridgeKYC() public {
        address user = address(0x100);
        vm.startPrank(admin);
        walletBridge.verifyKYC(user, true);
        assertTrue(walletBridge.kycVerified(user));
        vm.stopPrank();
    }

    function testBridgeClaim() public {
        address user = address(0x100);
        uint256 amount = 1000e18;

        // Set up merkle root
        bytes32 leaf = keccak256(abi.encodePacked(user, amount));
        bytes32 root = keccak256(abi.encodePacked(leaf));
        bytes32[] memory proof = new bytes32[](0); // Single leaf tree

        vm.startPrank(admin);
        walletBridge.updateMerkleRoot(root);
        walletBridge.setMigrationConfig(10000e18, block.timestamp, block.timestamp + 30 days);
        walletBridge.verifyKYC(user, true);
        vm.stopPrank();

        // Claim
        walletBridge.claim(1000e18, new bytes32[](0), address(0));
    }

    // ========== EcoGovernance Tests ==========

    function testGovernanceProposal() public {
        // Would need to set up full governor with voting
        // Placeholder for integration test
    }

    // ========== Integration Tests ==========

    function testFullActivityFlow() public {
        // 1. Register oracle
        vm.startPrank(admin);
        impactOracle.registerOracle(verifier, 100, 90, 1000e18);
        vm.stopPrank();

        // 2. Submit attestations
        vm.startPrank(verifier);
        bytes32 activityId = keccak256("full_flow_activity");
        impactOracle.submitAttestation(activityId, keccak256("sat_evidence"), 0, 95, block.timestamp, "0x1");
        vm.stopPrank();

        // 3. Submit impact report
        impactOracle.submitImpactReport(
            activityId,
            keccak256("commitment"),
            0, 95,
            keccak256("impact_hash"),
            keccak256("evidence_cid"),
            1
        );

        // 3. Challenge window passes
        vm.warp(block.timestamp + 8 days);

        // 4. Finalize metrics
        vm.startPrank(admin);
        impactOracle.finalizeMetrics(activityId);
        vm.stopPrank();

        // Check minted
        // Note: finalizeMetrics calls _mintRewards internally
    }

    // ========== Security Tests ==========

    function testReentrancyProtection() public {
        // EcoCoin has ReentrancyGuard on mint()
        // This would need a malicious contract to test properly
    }

    function testAccessControl() public {
        // Only authorized roles can call sensitive functions
        vm.expectRevert("AccessControl: account");
        vm.startPrank(producer);
        ecoCoin._grantRole(ecoCoin.MINTER_ROLE(), producer);
    }

    function testPauseMechanism() public {
        vm.startPrank(admin);
        ecoCoin.pause();

        vm.expectRevert("ERC20Pausable: token transfer while paused");
        ecoCoin.transfer(address(0x10), 100);

        ecoCoin.unpause();
    }

    // ========== Helper ==========
}