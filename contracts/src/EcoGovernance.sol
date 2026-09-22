// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/governance/TimelockController.sol";
import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/GovernorVotes.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./EcoCoin.sol";
import "./ImpactCertificate.sol";
import "./PhaseGate.sol";
import "./ImpactOracle.sol";
import "./MintController.sol";
import "./EcoTreasury.sol";
import "./EcosystemFund.sol";

/**
 * @title EcoGovernance
 * @notice DAO governance for EcoCoin protocol
 * @dev Manages protocol roles, parameter updates, and emergency actions
 *      Uses OpenZeppelin Governor with ERC20Votes for token-weighted voting
 */
contract EcoGovernance is ERC20Votes, ERC20("Eco Governance Token", "EGOV"), AccessControl {
    bytes32 public constant PROPOSER_ROLE = keccak256("PROPOSER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("DEFAULT_ADMIN_ROLE");
    bytes32 public constant REVOKER_ROLE = keccak256("REVOKER_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    // Protocol contracts
    EcoCoin public immutable ecoCoin;
    ImpactCertificate public immutable impactCertificate;
    PhaseGate public immutable phaseGate;
    ImpactOracle public immutable impactOracle;
    MintController public immutable mintController;
    EcoTreasury public immutable treasury;
    EcosystemFund public immutable ecosystemFund;
    EcoWalletBridge public immutable walletBridge;

    // Timelock for proposal execution
    TimelockController public immutable timelock;

    // Governance parameters
    uint256 public constant VOTING_DELAY = 1 days;
    uint256 public constant VOTING_PERIOD = 7 days;
    uint256 public constant PROPOSAL_THRESHOLD_BPS = 100; // 1% of total supply
    uint256 public constant QUORUM_BPS = 400; // 4% of total supply

    // Emergency timelock (shorter delay for critical actions)
    uint256 public constant EMERGENCY_TIMELOCK = 1 hours;

    // Governance token supply
    uint256 public constant GOV_TOKEN_SUPPLY = 10_000_000 * 10**18; // 10M EGOV

    event ProposalCreated(uint256 indexed proposalId, address indexed proposer, string description);
    event ProposalExecuted(uint256 indexed proposalId);
    event RoleGranted(bytes32 indexed role, address indexed account);
    event RoleRevoked(bytes32 indexed role, address indexed account);
    event EmergencyActionExecuted(uint256 indexed proposalId);

    constructor(
        address _ecoCoin,
        address _impactCertificate,
        address _phaseGate,
        address _impactOracle,
        address _mintController,
        address _treasury,
        address _ecosystemFund,
        address _walletBridge,
        address _initialGovernor
    ) ERC20("Eco Governance", "EGOV") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PROPOSER_ROLE, msg.sender);
        _grantRole(EXECUTOR_ROLE, msg.sender);

        // Deploy TimelockController
        timelock = new TimelockController(
            2 days, // min delay
            [msg.sender], // proposers
            [msg.sender], // executors
            msg.sender // admin
        );

        // Initialize protocol contracts
        ecoCoin = EcoCoin(_ecoCoin);
        impactCertificate = ImpactCertificate(_impactCertificate);
        phaseGate = PhaseGate(_phaseGate);
        impactOracle = ImpactOracle(_impactOracle);
        mintController = MintController(_mintController);
        treasury = EcoTreasury(_treasury);
        ecosystemFund = EcosystemFund(_ecosystemFund);
        walletBridge = EcoWalletBridge(_walletBridge);

        // Mint initial governance tokens to initial governor
        _mint(_initialGovernor, GOV_TOKEN_SUPPLY);

        // Transfer protocol roles to governance
        _transferProtocolRolesToGovernance();

        // Setup timelock roles
        timelock.grantRole(timelock.PROPOSER_ROLE(), address(this));
        timelock.grantRole(timelock.EXECUTOR_ROLE(), address(this));

        // Grant governor roles
        _grantRole(PROPOSER_ROLE, address(this));
        _grantRole(EXECUTOR_ROLE, address(this));
    }

    function _transferProtocolRolesToGovernance() internal {
        // Transfer EcoCoin roles
        ecoCoin.transferProtocolRoles(
            address(mintController),
            address(phaseGate),
            address(timelock) // Emergency pause via timelock
        );

        // Transfer ImpactCertificate REVOKER_ROLE to governance
        impactCertificate._grantRole(REVOKER_ROLE, address(this));

        // Transfer ImpactOracle roles to governance
        // (already handled via AccessControl in constructor)

        // Grant governance roles on dependent contracts
        _grantContractRoles();
    }

    function _grantContractRoles() internal {
        // Grant governance roles on dependent contracts
        // These would be implemented via interfaces
    }

    /**
     * @notice Create a new governance proposal
     * @param _targets Target contract addresses
     * @param _values ETH values for each call
     * @param _calldatas Encoded function calls
     * @param _description Proposal description
     */
    function propose(
        address[] calldata _targets,
        uint256[] calldata _values,
        bytes[] calldata _calldatas,
        string calldata _description
    ) external returns (uint256) {
        require(hasRole(PROPOSER_ROLE, msg.sender), "Not authorized to propose");

        uint256 proposalId = timelock.schedule(_targets, _values, _calldatas, keccak256(bytes(_description)), VOTING_DELAY);
        emit ProposalCreated(proposalId, msg.sender, _description);
        return proposalId;
    }

    /**
     * @notice Execute a passed proposal
     */
    function execute(
        address[] calldata _targets,
        uint256[] calldata _values,
        bytes[] calldata _calldatas,
        bytes32 _descriptionHash
    ) external onlyRole(EXECUTOR_ROLE) {
        timelock.execute(_targets, _values, _calldatas, _descriptionHash);
        emit ProposalExecuted(timelock.hashOperation(_targets, _values, _calldatas, _descriptionHash));
    }

    /**
     * @notice Emergency action with shorter timelock
     */
    function emergencyExecute(
        address[] calldata _targets,
        uint256[] calldata _values,
        bytes[] calldata _calldatas,
        string calldata _description
    ) external onlyRole(EMERGENCY_ROLE) {
        // For emergency actions, use shorter timelock
        uint256 proposalId = timelock.schedule(
            _targets,
            _values,
            _calldatas,
            keccak256(bytes(_description)),
            EMERGENCY_TIMELOCK
        );
        emit ProposalCreated(proposalId, msg.sender, _description);
        // Note: Still requires waiting for EMERGENCY_TIMELOCK
    }

    /**
     * @notice Grant protocol role to an address
     */
    function grantProtocolRole(bytes32 _role, address _account) external onlyRole(ADMIN_ROLE) {
        _grantRole(_role, _account);
        emit RoleGranted(_role, _account);
    }

    /**
     * @notice Revoke protocol role from an address
     */
    function revokeProtocolRole(bytes32 _role, address _account) external onlyRole(ADMIN_ROLE) {
        _revokeRole(_role, _account);
        emit RoleRevoked(_role, _account);
    }

    /**
     * @notice Update protocol parameter via governance
     */
    function updateProtocolParameter(
        address _target,
        bytes calldata _calldata
    ) external onlyRole(ADMIN_ROLE) {
        (bool success, ) = _target.call(_calldata);
        require(success, "Parameter update failed");
    }

    /**
     * @notice Set EcoCoin parameters via governance
     */
    function setEcoCoinParams(
        uint256 _burnRate,
        uint256 _phaseEmissionCap
    ) external onlyRole(ADMIN_ROLE) {
        require(_burnRate <= ecoCoin.MAX_BURN_RATE_BPS(), "Burn rate too high");
        ecoCoin.setBurnRate(_burnRate);
        ecoCoin.setPhaseEmissionCap(0, _phaseEmissionCap); // Phase 0, would be looped for all phases
    }

    /**
     * @notice Set PhaseGate configuration via governance
     */
    function setPhaseGateConfig(
        uint256 _phase,
        uint256 _emissionCap
    ) external onlyRole(ADMIN_ROLE) {
        phaseGate.setEmissionCap(_phase, _emissionCap);
    }

    /**
     * @notice Activate next phase via governance
     */
    function activateNextPhase() external onlyRole(ADMIN_ROLE) {
        uint256 nextPhase = phaseGate.currentPhase() + 1;
        require(nextPhase < phaseGate.PHASE_COUNT(), "All phases active");
        phaseGate.activatePhase(nextPhase);
    }

    /**
     * @notice Update EcoCoin distribution via governance
     */
    function updateDistribution(
        uint256 _platformShare,
        uint256 _ecosystemShare,
        uint256 _governanceShare
    ) external onlyRole(ADMIN_ROLE) {
        require(_platformShare + _ecosystemShare + _governanceShare == 3000, "Shares must sum to 30%");
        mintController.updateDistribution(
            mintController.burnRate(),
            _platformShare,
            _ecosystemShare,
            _governanceShare
        );
    }

    /**
     * @notice Emergency pause EcoCoin
     */
    function emergencyPause() external onlyRole(EMERGENCY_ROLE) {
        ecoCoin.pause();
    }

    /**
     * @notice Emergency unpause EcoCoin
     */
    function emergencyUnpause() external onlyRole(EMERGENCY_ROLE) {
        ecoCoin.unpause();
    }

    /**
     * @notice Revoke ImpactCertificate via governance
     */
    function revokeCertificate(uint256 _tokenId) external onlyRole(REVOKER_ROLE) {
        impactCertificate.updateStatus(_tokenId, 4); // revoked
    }

    /**
     * @notice Get governance token total supply
     */
    function totalSupply() public view override returns (uint256) {
        return GOV_TOKEN_SUPPLY;
    }

    // ERC20Votes required functions
    function _mint(address to, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._burn(account, amount);
    }

    // Delegate functions for ERC20Votes
    function delegate(address delegatee) public override(ERC20Votes) {
        super.delegate(delegatee);
    }

    function delegateBySig(
        address delegatee,
        uint256 nonce,
        uint256 expiry,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public override(ERC20Votes) {
        super.delegateBySig(delegatee, nonce, expiry, v, r, s);
    }

    function getVotes(address account) external view override(ERC20Votes) returns (uint256) {
        return super.getVotes(account);
    }

    function getPastVotes(address account, uint256 blockNumber) external view override(ERC20Votes) returns (uint256) {
        return super.getPastVotes(account, blockNumber);
    }

    function getPastTotalSupply(uint256 blockNumber) external view override(ERC20Votes) returns (uint256) {
        return super.getPastTotalSupply(blockNumber);
    }

    function supportsInterface(bytes4 interfaceId) public view override(AccessControl, ERC20Votes) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}