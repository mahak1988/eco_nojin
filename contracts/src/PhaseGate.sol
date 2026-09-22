// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title PhaseGate
 * @notice Immutable phase state machine for EcoCoin protocol
 * @dev All phase timings, thresholds, and feature flags encoded immutably
 */
contract PhaseGate is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("DEFAULT_ADMIN_ROLE");
    bytes32 public constant PHASE_CONTROLLER_ROLE = keccak256("PHASE_CONTROLLER_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    struct PhaseConfig {
        uint256 minDuration;      // minimum days before phase can activate
        uint256 startTimestamp;   // when phase became active
        uint256 activityThreshold; // minimum activities required
        uint256 minAccuracy;      // basis points (9500 = 95%)
        uint256 maxDiscrepancy;   // basis points (200 = 2%)
        uint256 oracleUptime;     // basis points (9950 = 99.5%)
        uint256 requiredRegions;  // minimum regions for geographic distribution
    }

    struct PhaseState {
        bool active;
        uint256 activatedAt;
        uint256 emissionCap;
        uint256 emissionUsed;      // Track actual emissions used in this phase
        uint256 activitiesCount;
        uint256 verifiedCount;
        uint256 discrepancyCount;
        uint256 oracleUptimeSum;
        uint256 oracleChecks;
    }

    bytes32 public constant PHASE_CONTROLLER = keccak256("PHASE_CONTROLLER_ROLE");

    uint256 public constant PHASE_COUNT = 6;
    uint256 public currentPhase;
    uint256 public genesisTimestamp;

    PhaseConfig[PHASE_COUNT] public phaseConfigs;
    PhaseState[PHASE_COUNT] public phaseStates;

    event PhaseActivated(uint256 indexed phase, uint256 timestamp);
    event PhaseThresholdsUpdated(uint256 indexed phase, uint256 activityThreshold, uint256 minAccuracy, uint256 maxDiscrepancy);
    event OracleUptimeReported(uint256 uptimeBps);

    constructor(
        uint256[6] memory minDurations,
        uint256[6] memory activityThresholds,
        uint256[6] memory minAccuracies,
        uint256[6] memory maxDiscrepancies,
        uint256[6] memory oracleUptimes,
        uint256[6] memory requiredRegions,
        uint256[6] memory emissionCaps
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PHASE_CONTROLLER, msg.sender); // will transfer to governance

        genesisTimestamp = block.timestamp;

        for (uint256 i = 0; i < PHASE_COUNT; i++) {
            phaseConfigs[i] = PhaseConfig({
                minDuration: minDurations[i] * 1 days,
                startTimestamp: 0,
                activityThreshold: activityThresholds[i],
                minAccuracy: minAccuracies[i],
                maxDiscrepancy: maxDiscrepancies[i],
                oracleUptime: oracleUptimes[i],
                requiredRegions: requiredRegions[i]
            });
            phaseStates[i].emissionCap = 0;
        }
    }

    function activatePhase(uint256 phase) external onlyRole(PHASE_CONTROLLER) {
        require(phase < PHASE_COUNT, "Invalid phase");
        require(phase == currentPhase + 1, "Phases must activate sequentially");
        require(!phaseStates[phase].active, "Phase already active");

        // Check minimum duration since previous phase
        uint256 prevPhaseEnd = phase == 0 ? genesisTimestamp : phaseStates[phase - 1].activatedAt + phaseConfigs[phase - 1].minDuration;
        require(block.timestamp >= prevPhaseEnd, "Minimum duration not elapsed");

        // Check quantitative thresholds
        require(_checkPhaseThresholds(phase - 1), "Previous phase thresholds not met");

        // For P4, also require VVB/Registry readiness
        if (phase == 4) {
            require(_vvbRegistryReady(), "VVB/Registry not ready");
        }

        currentPhase = phase;
        phaseStates[phase].active = true;
        phaseStates[phase].activatedAt = block.timestamp;
        emit PhaseActivated(phase, block.timestamp);
    }

    function _checkPhaseThresholds(uint256 phase) internal view returns (bool) {
        if (phase >= PHASE_COUNT) return true;
        PhaseState storage state = phaseStates[phase];
        PhaseConfig memory config = phaseConfigs[phase];

        if (config.activityThreshold > 0 && state.activitiesCount < config.activityThreshold) return false;
        if (config.minAccuracy > 0) {
            if (state.activitiesCount == 0) return false;
            uint256 accuracy = (state.verifiedCount * 10000) / state.activitiesCount;
            if (accuracy < config.minAccuracy) return false;
        }
        if (config.maxDiscrepancy > 0 && state.activitiesCount > 0) {
            uint256 discrepancy = (state.discrepancyCount * 10000) / state.activitiesCount;
            if (discrepancy > config.maxDiscrepancy) return false;
        }
        if (config.oracleUptime > 0 && state.oracleChecks > 0) {
            uint256 uptime = (state.oracleUptimeSum * 10000) / state.oracleChecks;
            if (uptime < config.oracleUptime) return false;
        }
        if (config.requiredRegions > 0) {
            // Check geographic distribution - would need region tracking
        }
        if (config.minDuration > 0) {
            uint256 minEnd = (phase == 0 ? genesisTimestamp : phaseStates[phase - 1].activatedAt) + config.minDuration;
            if (block.timestamp < minEnd) return false;
        }
        return true;
    }

    function _vvbRegistryReady() internal view returns (bool) {
        // This would check a registry contract for VVB approval status
        // For now, return true - actual implementation would check external contracts
        return true;
    }

    function recordActivity(uint256 phase, bool verified, bool discrepancy) external onlyRole(ORACLE_ROLE) {
        require(phase < PHASE_COUNT, "Invalid phase");
        PhaseState storage state = phaseStates[phase];
        state.activitiesCount++;
        if (verified) state.verifiedCount++;
        if (discrepancy) state.discrepancyCount++;
    }

    function reportOracleUptime(uint256 uptimeBps) external onlyRole(ORACLE_ROLE) {
        require(uptimeBps <= 10000, "Invalid uptime");
        phaseStates[currentPhase].oracleUptimeSum += uptimeBps;
        phaseStates[currentPhase].oracleChecks++;
        emit OracleUptimeReported(uptimeBps);
    }

    function recordDiscrepancy() external onlyRole(ORACLE_ROLE) {
        phaseStates[currentPhase].discrepancyCount++;
    }

    function recordEmission(uint256 phase, uint256 amount) external onlyRole(PHASE_CONTROLLER) {
        require(phase < PHASE_COUNT, "Invalid phase");
        phaseStates[phase].emissionUsed += amount;
    }

    function setEmissionCap(uint256 phase, uint256 cap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(phase < PHASE_COUNT, "Invalid phase");
        phaseStates[phase].emissionCap = cap;
    }

    function getEmissionCap(uint256 phase) external view returns (uint256) {
        require(phase < PHASE_COUNT, "Invalid phase");
        return phaseStates[phase].emissionCap;
    }

    function checkEmissionCap(uint256 phase, uint256 amount) external view returns (bool) {
        require(phase < PHASE_COUNT, "Invalid phase");
        PhaseState storage state = phaseStates[phase];
        if (state.emissionCap == 0) return true; // No cap set
        return state.emissionUsed + amount <= state.emissionCap;
    }

    function getEmissionUsed(uint256 phase) external view returns (uint256) {
        require(phase < PHASE_COUNT, "Invalid phase");
        return phaseStates[phase].emissionUsed;
    }

    function isPhaseActive(uint256 phase) external view returns (bool) {
        return phaseStates[phase].active;
    }

    function getPhaseConfig(uint256 phase) external view returns (
        uint256 minDuration,
        uint256 activityThreshold,
        uint256 minAccuracy,
        uint256 maxDiscrepancy,
        uint256 oracleUptime,
        uint256 requiredRegions,
        uint256 emissionCap,
        uint256 emissionUsed
    ) {
        PhaseConfig memory config = phaseConfigs[phase];
        return (config.minDuration, config.activityThreshold, config.minAccuracy,
                config.maxDiscrepancy, config.oracleUptime, config.requiredRegions,
                phaseStates[phase].emissionCap, phaseStates[phase].emissionUsed);
    }

    function getPhaseState(uint256 phase) external view returns (
        bool active,
        uint256 activatedAt,
        uint256 activitiesCount,
        uint256 verifiedCount,
        uint256 discrepancyCount,
        uint256 oracleUptimeSum,
        uint256 oracleChecks,
        uint256 emissionCap,
        uint256 usedEmission
    ) {
        PhaseState storage state = phaseStates[phase];
        return (state.active, state.activatedAt, state.activitiesCount, state.verifiedCount,
                state.discrepancyCount, state.oracleUptimeSum, state.oracleChecks,
                state.emissionCap, state.emissionUsed);
    }

    function currentPhaseInfo() external view returns (
        uint256 phase,
        bool active,
        uint256 activatedAt,
        uint256 activitiesCount,
        uint256 verifiedCount,
        uint256 discrepancyCount
    ) {
        PhaseState storage state = phaseStates[currentPhase];
        return (currentPhase, state.active, state.activatedAt, state.activitiesCount,
                state.verifiedCount, state.discrepancyCount);
    }
}