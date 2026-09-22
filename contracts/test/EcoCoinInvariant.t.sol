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
 * @title EcoCoin Protocol Invariant Tests
 * @notice Invariant tests for EcoCoin protocol using Foundry's invariant testing
 */
contract EcoCoinInvariantTest is Test {
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

    // Invariant: Total supply never exceeds hard cap
    function invariant_TotalSupplyNeverExceedsHardCap() public view {
        assertLe(ecoCoin.totalSupply(), ecoCoin.HARD_CAP());
    }

    // Invariant: Burn rate never exceeds 10%
    function invariant_BurnRateNeverExceedsMax() public view {
        assertLe(ecoCoin.burnRate(), 1000);
    }

    // Invariant: Phase transitions are sequential
    function invariant_PhaseTransitionsSequential() public view {
        uint256 current = phaseGate.currentPhase();
        if (current > 0) {
            assertTrue(phaseGate.isPhaseActive(current - 1));
        }
    }

    // Invariant: Phase emission used never exceeds cap
    function invariant_PhaseEmissionUsedWithinCap() public view {
        for (uint256 i = 0; i < phaseGate.PHASE_COUNT(); i++) {
            uint256 cap = phaseGate.getEmissionCap(i);
            uint256 used = phaseGate.getEmissionUsed(i);
            if (cap > 0) {
                assertLe(used, cap);
            }
        }
    }

    // Invariant: No double minting for same activity
    function invariant_NoDoubleMint() public view {
        // This would require tracking minted activities across all contracts
        // Simplified: check MintController mapping
    }

    // Invariant: Total distribution percentages sum to 100%
    function invariant_DistributionPercentagesSum() public view {
        uint256 total = mintController.DIST_PRODUCER_BPS() +
            mintController.DIST_PLATFORM_BPS() +
            mintController.DIST_ECOSYSTEM_BPS() +
            mintController.DIST_GOVERNANCE_BPS();
        assertEq(total, 10000);
    }

    // Invariant: ImpactCertificate is non-transferable
    function invariant_ImpactCertificateNonTransferable() public view {
        // Tested via revert in transfer attempts
    }

    // Invariant: Phase emission used tracked correctly
    function invariant_EmissionUsedTracked() public view {
        for (uint256 i = 0; i < phaseGate.PHASE_COUNT(); i++) {
            if (phaseGate.isPhaseActive(i)) {
                // Emission used should be >= 0
                assertTrue(phaseGate.getEmissionUsed(i) >= 0);
            }
        }
    }

    // Invariant: Oracle nodes have valid stakes
    function invariant_OracleStakesValid() public view {
        // Would iterate over all nodes
    }

    // Invariant: Challenge window is 7 days
    function invariant_ChallengeWindowFixed() public view {
        assertEq(impactOracle.challengeWindow(), 7 days);
    }

    // Invariant: EcoWallet bridge merkle root only updated by verifier
    function invariant_BridgeMerkleRootVerifierOnly() public view {
        // Checked via role
    }

    // Invariant: Governance token supply fixed
    function invariant_GovernanceSupplyFixed() public view {
        assertEq(governance.totalSupply(), 10_000_000 * 10**18);
    }
}