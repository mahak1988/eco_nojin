// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./EcoCoin.sol";
import "./ImpactCertificate.sol";
import "./PhaseGate.sol";
import "./ImpactOracle.sol";
import "./EcoTreasury.sol";
import "./EcosystemFund.sol";

/**
 * @title MintController
 * @notice Central controller for EcoCoin minting after verified impact
 * @dev Coordinates ImpactOracle, EcoCoin, PhaseGate, Treasury, and EcosystemFund
 */
contract MintController is AccessControl, ReentrancyGuard {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant WALLET_GATE_ROLE = keccak256("WALLET_GATE_ROLE");

    EcoCoin public immutable ecoCoin;
    ImpactCertificate public immutable impactCertificate;
    PhaseGate public immutable phaseGate;
    ImpactOracle public immutable impactOracle;
    EcoTreasury public immutable treasury;
    EcosystemFund public immutable ecosystemFund;

    struct MintRequest {
        bytes32 activityId;
        address recipient;
        uint256 impactScore;
        uint8 confidence;
        uint256 phase;
        uint256 timestamp;
        bytes32 impactHash;
    }

    // Distribution constants (matching config/distribution_constants.yaml)
    uint256 public constant DIST_PRODUCER_BPS = 7000;     // 70%
    uint256 public constant DIST_PLATFORM_BPS = 1500;     // 15%
    uint256 public constant DIST_ECOSYSTEM_BPS = 1000;    // 10%
    uint256 public constant DIST_GOVERNANCE_BPS = 500;    // 5%
    uint256 public constant DIST_TOTAL_BPS = 10000;       // 100%

    uint256 public constant DEFAULT_BURN_RATE_BPS = 200;  // 2%
    uint256 public constant MAX_BURN_RATE_BPS = 1000;     // 10%

    // Runtime configurable shares (can be updated by governance)
    uint256 public platformShare;     // basis points
    uint256 public ecosystemShare;    // basis points
    uint256 public governanceShare;   // basis points

    mapping(bytes32 => bool) public mintedActivities;

    event MintRequested(bytes32 indexed activityId, address indexed recipient, uint256 amount);
    event MintCompleted(bytes32 indexed activityId, address indexed to, uint256 minted, uint256 burned, uint256 net);
    event DistributionCompleted(uint256 producer, uint256 platform, uint256 ecosystem, uint256 governance);
    event ConfigUpdated(uint256 burnRate, uint256 platformShare, uint256 ecosystemShare, uint256 governanceShare);

    constructor(
        address _ecoCoin,
        address _impactCertificate,
        address _phaseGate,
        address _impactOracle,
        address _treasury,
        address _ecosystemFund
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(ORACLE_ROLE, msg.sender);

        ecoCoin = EcoCoin(_ecoCoin);
        impactCertificate = ImpactCertificate(_impactCertificate);
        phaseGate = PhaseGate(_phaseGate);
        impactOracle = ImpactOracle(_impactOracle);
        treasury = EcoTreasury(_treasury);
        ecosystemFund = EcosystemFund(_ecosystemFund);

        burnRate = DEFAULT_BURN_RATE_BPS;
        platformShare = DIST_PLATFORM_BPS;
        ecosystemShare = DIST_ECOSYSTEM_BPS;
        governanceShare = DIST_GOVERNANCE_BPS;
    }

    function requestMint(MintRequest calldata request) external onlyRole(ORACLE_ROLE) returns (uint256) {
        _requirePhaseActive(request.phase);
        _checkNotMinted(request.activityId);
        _checkPhaseEmissionCap(request.phase, request.impactScore);

        uint256 rawImpact = _calculateRawImpact(request);
        uint256 minted = _applyPhaseCap(request.phase, rawImpact);
        uint256 burned = (minted * burnRate) / DIST_TOTAL_BPS;
        uint256 net = minted - burned;

        // Distribute using constants (70/15/10/5 after burn)
        uint256 producer = (net * DIST_PRODUCER_BPS) / DIST_TOTAL_BPS;
        uint256 platform = (net * platformShare) / DIST_TOTAL_BPS;
        uint256 ecosystem = (net * ecosystemShare) / DIST_TOTAL_BPS;
        uint256 governance = (net * governanceShare) / DIST_TOTAL_BPS;

        // Burn
        if (burned > 0) {
            ecoCoin.burn(burned);
        }

        // Mint net to recipient
        uint256 activityIdNum = uint256(request.activityId);
        ecoCoin.mint(request.recipient, producer, activityIdNum, request.phase);

        // Distribute to treasury and funds
        if (platform > 0) {
            ecoCoin.mint(address(this), platform, activityIdNum, request.phase);
        }
        if (ecosystem > 0) {
            ecoCoin.mint(address(this), ecosystem, activityIdNum, request.phase);
        }
        if (governance > 0) {
            ecoCoin.mint(address(this), governance, activityIdNum, request.phase);
        }

        // Record emission in PhaseGate
        _recordEmission(request.phase, minted);

        mintedActivities[request.activityId] = true;

        emit MintCompleted(request.activityId, request.recipient, minted, burned, net);
        emit DistributionCompleted(producer, platform, ecosystem, governance);

        return producer;
    }

    function _calculateRawImpact(MintRequest calldata request) internal pure returns (uint256) {
        // simplified: impactScore * confidence * trust * survival * scarcity / 10000^4
        uint256 trust = 10000;
        uint256 survival = 10000;
        uint256 scarcity = 10000;

        uint256 result = request.impactScore;
        result = (result * request.confidence) / 100;
        result = (result * trust) / 10000;
        result = (result * 10000) / 10000; // survival
        result = (result * 10000) / 10000; // scarcity
        return result;
    }

    function _applyPhaseCap(uint256 phase, uint256 amount) internal view returns (uint256) {
        // Check PhaseGate emission cap
        bool withinCap = phaseGate.checkEmissionCap(phase, amount);
        if (!withinCap) {
            // Get available capacity
            uint256 cap = phaseGate.getEmissionCap(phase);
            uint256 used = phaseGate.getEmissionUsed(phase);
            if (cap > 0 && used < cap) {
                return cap - used;
            }
            return 0;
        }
        return amount;
    }

    function _requirePhaseActive(uint256 phase) internal view {
        require(phaseGate.isPhaseActive(phase), "Phase not active");
    }

    function _checkNotMinted(bytes32 activityId) internal view {
        require(!mintedActivities[activityId], "Already minted");
    }

    function _checkPhaseEmissionCap(uint256 phase, uint256 amount) internal view {
        require(phaseGate.checkEmissionCap(phase, amount), "Phase emission cap exceeded");
    }

    // Record emission in PhaseGate after successful mint
    function _recordEmission(uint256 phase, uint256 amount) internal {
        phaseGate.recordEmission(phase, amount);
    }

    function updateDistribution(
        uint256 newBurnRate,
        uint256 newPlatformShare,
        uint256 newEcosystemShare,
        uint256 newGovernanceShare
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newBurnRate <= MAX_BURN_RATE_BPS, "Burn rate max 10%");
        require(newPlatformShare + newEcosystemShare + newGovernanceShare == 3000, "Shares must sum to 30%");

        burnRate = newBurnRate;
        platformShare = newPlatformShare;
        ecosystemShare = newEcosystemShare;
        governanceShare = newGovernanceShare;
        emit ConfigUpdated(newBurnRate, newPlatformShare, newEcosystemShare, newGovernanceShare);
    }

    function emergencyPause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        // Implemented in EcoCoin
    }
}