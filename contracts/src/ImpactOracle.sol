// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./ImpactCertificate.sol";
import "./PhaseGate.sol";
import "./EcoCoin.sol";

/**
 * @title ImpactOracle
 * @notice Multi-source verification oracle for ecosystem restoration activities
 * @dev Accepts signed attestations from registered oracle nodes, computes impact scores,
 *      manages challenge periods, and mints ImpactCertificates and EcoCoin
 */
contract ImpactOracle is AccessControl, ReentrancyGuard {
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant DISPUTE_ROLE = keccak256("DISPUTE_ROLE");

    ImpactCertificate public immutable impactCertificate;
    EcoCoin public immutable ecoCoin;
    PhaseGate public immutable phaseGate;

    struct OracleNode {
        address node;
        uint256 weight;          // voting weight
        uint256 stake;           // stake amount for slashing
        uint8 reputation;        // 0-100
        bool active;
        bool slashed;            // whether node has been slashed
    }

    struct Attestation {
        bytes32 activityId;
        address reporter;
        bytes32 commitment;        // hash of off-chain evidence
        uint8 dataType;            // 0=satellite, 1=gps_photo, 2=field, 3=lab, 4=community
        uint8 confidence;          // 0-100
        uint256 timestamp;
        bytes signature;
        bool processed;
    }

    // Track all attestation keys for an activity to enable aggregation
    mapping(bytes32 => bytes32[]) public activityAttestationKeys;

    struct ImpactReport {
        bytes32 activityId;
        address reporter;
        bytes32 commitment;
        uint8 dataType;
        uint8 confidence;
        uint256 timestamp;
        bytes32 impactHash;        // hash of detailed impact data
        bytes32 evidenceCommitment; // hash of off-chain evidence (IPFS/Filecoin)
        uint16 methodologyVersion;
        bool challenged;
        uint256 challengeDeadline;
    }

    struct ImpactMetrics {
        uint8 confidence;           // aggregated confidence 0-100
        uint256 impactScore;        // normalized 0-10000
        uint256 trustMultiplier;    // basis points (10000 = 1.0x)
        uint16 survivalFactor;      // basis points
        uint16 scarcityFactor;      // basis points
        uint256 challengeDeadline;
    }

    uint256 public constant CHALLENGE_WINDOW = 7 days;
    uint256 public constant MAX_CONFIDENCE = 100;

    mapping(bytes32 => OracleNode) public oracleNodes;
    mapping(bytes32 => Attestation) public attestations;
    mapping(bytes32 => ImpactReport) public impactReports;
    mapping(bytes32 => ImpactMetrics[]) public pendingMetrics;
    mapping(bytes32 => mapping(address => bool)) public challengers;

uint256 public challengeWindow;
uint256 public minOracleWeight;
uint256 public slashAmount;

event NodeRegistered(address indexed node, uint256 weight, uint8 reputation);
    event AttestationSubmitted(bytes32 indexed activityId, address indexed reporter, uint8 dataType, uint8 confidence);
    event ImpactReportCreated(bytes32 indexed activityId, address indexed reporter, uint8 confidence, uint256 timestamp);
    event ChallengeRaised(bytes32 indexed activityId, address indexed challenger);
    event ChallengeResolved(bytes32 indexed activityId, bool upheld);
    event MetricsFinalized(bytes32 indexed activityId, uint8 confidence, uint256 impactScore);
    event EcoCoinMinted(address indexed to, uint256 amount, bytes32 activityId, uint256 phase);
    event NodeSlashed(address indexed node, uint256 amount);
    event StakeAdded(address indexed node, uint256 amount);

    constructor(
        address _impactCertificate,
        address _ecoCoin,
        address _phaseGate
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORACLE_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
        _grantRole(DISPUTE_ROLE, msg.sender);

        impactCertificate = ImpactCertificate(_impactCertificate);
        ecoCoin = EcoCoin(_ecoCoin);
        phaseGate = PhaseGate(_phaseGate);

        challengeWindow = CHALLENGE_WINDOW;
        minOracleWeight = 1;
        slashAmount = 0; // to be set by governance
    }

    function registerOracle(address node, uint256 weight, uint8 reputation, uint256 stake) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(reputation <= 100, "Invalid reputation");
        require(stake >= minOracleWeight, "Insufficient stake");
        oracleNodes[keccak256(abi.encodePacked(node))] = OracleNode({
            node: node,
            weight: weight,
            stake: stake,
            reputation: reputation,
            active: true,
            slashed: false
        });
        emit NodeRegistered(node, weight, reputation);
    }

    function submitAttestation(
        bytes32 activityId,
        bytes32 commitment,
        uint8 dataType,
        uint8 confidence,
        uint256 timestamp,
        bytes calldata signature
    ) external onlyRole(ORACLE_ROLE) {
        require(confidence <= MAX_CONFIDENCE, "Confidence exceeds max");
        require(timestamp <= block.timestamp, "Future timestamp");
        require(timestamp >= block.timestamp - 30 days, "Timestamp too old");

        bytes32 key = keccak256(abi.encodePacked(activityId, msg.sender));
        require(!attestations[key].processed, "Already processed");

        Attestation storage att = attestations[key];
        att.activityId = activityId;
        att.reporter = msg.sender;
        att.commitment = commitment;
        att.dataType = dataType;
        att.confidence = confidence;
        att.timestamp = timestamp;
        att.signature = bytes(signature);
        att.processed = true;

        // Track this attestation key for the activity
        activityAttestationKeys[activityId].push(key);

        emit AttestationSubmitted(activityId, msg.sender, dataType, confidence);

        // Try to finalize if we have enough attestations
        _tryFinalize(activityId);
    }

    function submitImpactReport(
        bytes32 activityId,
        bytes32 commitment,
        uint8 dataType,
        uint8 confidence,
        bytes32 impactHash,
        bytes32 evidenceCommitment,
        uint16 methodologyVersion
    ) external onlyRole(ORACLE_ROLE) {
        require(confidence <= MAX_CONFIDENCE, "Confidence exceeds max");
        require(impactReports[activityId].timestamp == 0, "Report exists");

        ImpactReport storage report = impactReports[activityId];
        report.activityId = activityId;
        report.reporter = msg.sender;
        report.commitment = commitment;
        report.dataType = dataType;
        report.confidence = confidence;
        report.timestamp = block.timestamp;
        report.impactHash = impactHash;
        report.evidenceCommitment = evidenceCommitment;
        report.methodologyVersion = methodologyVersion;
        report.challenged = false;
        report.challengeDeadline = block.timestamp + challengeWindow;

        emit ImpactReportCreated(activityId, msg.sender, confidence, block.timestamp);

        // Open challenge period
        pendingMetrics[activityId].push(ImpactMetrics({
            confidence: confidence,
            impactScore: 0,
            trustMultiplier: 10000,
            survivalFactor: 10000,
            scarcityFactor: 10000,
            challengeDeadline: block.timestamp + challengeWindow
        }));
    }

    function challengeActivity(bytes32 activityId) external {
        require(impactReports[activityId].timestamp > 0, "No report to challenge");
        require(!impactReports[activityId].challenged, "Already challenged");
        require(block.timestamp <= impactReports[activityId].challengeDeadline, "Challenge window closed");
        require(!challengers[activityId][msg.sender], "Already challenged");

        impactReports[activityId].challenged = true;
        challengers[activityId][msg.sender] = true;
        emit ChallengeRaised(activityId, msg.sender);
    }

    function resolveChallenge(bytes32 activityId, bool upheld) external onlyRole(DISPUTE_ROLE) {
        require(impactReports[activityId].challenged, "Not challenged");
        impactReports[activityId].challenged = false;
        impactReports[activityId].challengeDeadline = 0;

        if (upheld) {
            // Challenger was wrong - could slash if staked
        } else {
            // Report rejected
            impactReports[activityId].timestamp = 0;
        }
        emit ChallengeResolved(activityId, upheld);
    }

    function finalizeMetrics(bytes32 activityId) external onlyRole(ORACLE_ROLE) {
        require(impactReports[activityId].timestamp > 0, "No report");
        require(!impactReports[activityId].challenged, "Under challenge");
        require(block.timestamp > impactReports[activityId].challengeDeadline, "Challenge window open");

        ImpactReport storage report = impactReports[activityId];
        report.challengeDeadline = 0;

        // Compute aggregated metrics from all attestations
        ImpactMetrics memory metrics = _computeAggregatedMetrics(activityId);
        require(metrics.confidence > 0, "Insufficient confidence");

        pendingMetrics[activityId].push(metrics);
        emit MetricsFinalized(activityId, metrics.confidence, metrics.impactScore);

        // Check if phase allows minting
        if (phaseGate.currentPhase() >= 2) {
            _mintRewards(activityId, metrics);
        }
    }

    function _tryFinalize(bytes32 activityId) internal {
        // Check if we have enough attestations to auto-finalize
        // Need at least 3 attestations from different oracles
        if (activityAttestationKeys[activityId].length >= 3) {
            _computeAggregatedMetrics(activityId);
        }
    }

    function _computeAggregatedMetrics(bytes32 activityId) internal view returns (ImpactMetrics memory) {
        bytes32[] storage keys = activityAttestationKeys[activityId];
        uint256 numAttestations = keys.length;

        if (numAttestations == 0) {
            return ImpactMetrics(0, 0, 10000, 10000, 10000, 0);
        }

        // Data type multipliers (satellite > gps_photo > field > lab > community)
        uint256[5] memory dataTypeMultipliers = [12000, 11000, 10000, 9000, 8000];

        // Aggregation variables
        uint256 weightedConfidenceSum = 0;
        uint256 totalWeight = 0;
        uint256 weightedImpactSum = 0;
        uint256 totalReputationWeight = 0;
        uint256 totalOracleWeight = 0;

        // Track unique oracle addresses
        address[] memory oracleAddresses = new address[](keys.length);
        uint256 uniqueCount = 0;

        for (uint256 i = 0; i < keys.length; i++) {
            Attestation storage att = attestations[keys[i]];
            if (!att.processed) continue;

            // Get oracle info
            bytes32 nodeKey = keccak256(abi.encodePacked(att.reporter));
            OracleNode storage node = oracleNodes[nodeKey];

            if (!node.active) continue;

            // Check if oracle already processed for this activity
            bool isDuplicate = false;
            for (uint256 j = 0; j < uniqueCount; j++) {
                if (oracleAddresses[j] == att.reporter) {
                    isDuplicate = true;
                    break;
                }
            }
            if (isDuplicate) continue;

            oracleAddresses[uniqueCount] = att.reporter;
            uniqueCount++;

            // Oracle weight = reputation (0-100) * stake weight
            uint256 oracleWeight = (node.reputation * node.weight) / 100;
            if (oracleWeight == 0) oracleWeight = 1;

            // Data type multiplier (0=satellite: 1.2x, 1=gps: 1.1x, 2=field: 1.0x, 3=lab: 0.9x, 4=community: 0.8x)
            uint256 dataTypeMultiplier = dataTypeMultipliers[att.dataType];

            // Weighted confidence
            weightedConfidenceSum += att.confidence * oracleWeight * dataTypeMultiplier / 10000;

            // Impact contribution (base impact * confidence * dataTypeMultiplier)
            uint256 baseImpact = 10000; // Normalized base
            uint256 impactContribution = (baseImpact * att.confidence * dataTypeMultiplier) / 1000000;
            weightedImpactSum += impactContribution * oracleWeight;

            // Trust multiplier based on oracle reputation
            totalReputationWeight += node.reputation * oracleWeight;

            totalWeight += oracleWeight * dataTypeMultiplier / 10000;
            totalOracleWeight += oracleWeight;
        }

        // Compute final metrics
        ImpactMetrics memory metrics;

        // Aggregated confidence (weighted average)
        metrics.confidence = totalWeight > 0 ? uint8(weightedConfidenceSum / totalWeight) : 0;

        // Impact score (0-10000)
        metrics.impactScore = totalOracleWeight > 0 ? (weightedImpactSum * 10000) / (totalOracleWeight * 100) : 0;

        // Trust multiplier based on average oracle reputation
        metrics.trustMultiplier = totalOracleWeight > 0 ? (totalReputationWeight * 100) / totalOracleWeight : 10000;

        // Survival factor - based on data quality (satellite data = higher survival)
        metrics.survivalFactor = 10000;

        // Scarcity factor - based on region/ecosystem rarity
        metrics.scarcityFactor = 10000;

        metrics.challengeDeadline = 0;

        return metrics;
    }

    function _mintRewards(bytes32 activityId, ImpactMetrics memory metrics) internal {
        // Calculate raw impact
        uint256 rawImpact = (metrics.impactScore * metrics.trustMultiplier) / 10000;
        rawImpact = (rawImpact * metrics.survivalFactor) / 10000;
        rawImpact = (rawImpact * metrics.scarcityFactor) / 10000;

        uint256 minted = rawImpact; // simplified
        uint256 phase = phaseGate.currentPhase();
        uint256 phaseCap = phaseGate.getEmissionCap(phase);

        // Mint via EcoCoin (which handles burn and split)
        uint256 activityIdNum = uint256(activityId);
        ecoCoin.mint(msg.sender, minted, activityIdNum, phaseGate.currentPhase());

        // Mint Impact Certificate
        bytes32 activityIdHash = keccak256(abi.encodePacked("activity", activityId, block.timestamp));
        impactCertificate.mintCertificate(
            msg.sender,
            keccak256(abi.encodePacked("activity", activityId)),
            metrics.confidence,
            1, // methodology version
            activityId,
            "" // URI - would point to encrypted off-chain data
        );

        phaseGate.recordActivity(phaseGate.currentPhase(), true, false);
        emit EcoCoinMinted(msg.sender, minted, activityId, phaseGate.currentPhase());
    }

    function registerNode(address node, uint256 weight, uint8 reputation) external onlyRole(DEFAULT_ADMIN_ROLE) {
        // Implementation in ImpactCertificate
    }

    function slashNode(address node, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        bytes32 nodeKey = keccak256(abi.encodePacked(node));
        OracleNode storage oracle = oracleNodes[nodeKey];
        require(oracle.node == node, "Node not registered");
        require(!oracle.slashed, "Already slashed");
        require(amount <= oracle.stake, "Amount exceeds stake");

        oracle.stake -= amount;
        oracle.slashed = true;
        oracle.active = false;

        // Transfer slashed amount to treasury (or burn)
        // For now, just reduce stake - in production would transfer to treasury

        emit NodeSlashed(node, amount);
    }

    function addStake(address node, uint256 amount) external {
        bytes32 nodeKey = keccak256(abi.encodePacked(node));
        OracleNode storage oracle = oracleNodes[nodeKey];
        require(oracle.node == node, "Node not registered");
        require(!oracle.slashed, "Node is slashed");

        oracle.stake += amount;
        emit StakeAdded(node, amount);
    }

    function setChallengeWindow(uint256 window) external onlyRole(DEFAULT_ADMIN_ROLE) {
        challengeWindow = window;
    }
}