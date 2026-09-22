// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title EcoCoin
 * @notice ERC-20 token for ecosystem restoration rewards
 * @dev Immutable, non-upgradable contract with hard cap, phased minting, and EIP-2612 Permit
 */
contract EcoCoin is ERC20, ERC20Burnable, ERC20Pausable, ERC20Permit, AccessControl, ReentrancyGuard {
    string public constant VERSION = "1.0.0";
    uint256 public constant HARD_CAP = 100_000_000_000 * 10**18; // 100B ECO

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PHASE_GATE_ROLE = keccak256("PHASE_GATE_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    uint256 public immutable chainId;
    address public immutable contractAddress;

    uint256 public burnRate; // basis points (200 = 2%)
    uint256 public phaseEmissionCap;
    uint256 public currentPhase;

    mapping(uint256 => uint256) public phaseEmissionUsed;

    event PhaseActivated(uint256 indexed phase, uint256 timestamp);
    event Minted(address indexed to, uint256 amount, uint256 impactId, uint256 phase);
    event Burned(uint256 amount, uint256 timestamp);
    event PhaseEmissionCapUpdated(uint256 indexed phase, uint256 newCap);
    event BurnRateUpdated(uint256 newRate);
    event PhaseEmissionCapSet(uint256 indexed phase, uint256 cap);

    constructor() ERC20("Eco Nojin EcoCoin", "ECO") ERC20Pausable() ERC20Permit("Eco Nojin EcoCoin") {
        chainId = block.chainid;
        contractAddress = address(this);
        burnRate = 200; // 2% = 200 basis points
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender); // temporary, will be transferred to MintController
        _grantRole(PHASE_GATE_ROLE, msg.sender); // temporary, will be transferred to PhaseGate
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    /**
     * @notice Transfer protocol roles to their designated contracts
     * @dev Should be called once after all contracts are deployed
     * @param _minterRoleReceiver Address to receive MINTER_ROLE (MintController)
     * @param _phaseGateRoleReceiver Address to receive PHASE_GATE_ROLE (PhaseGate)
     * @param _pauserRoleReceiver Address to receive PAUSER_ROLE (Emergency multisig)
     */
    function transferProtocolRoles(
        address _minterRoleReceiver,
        address _phaseGateRoleReceiver,
        address _pauserRoleReceiver
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        // Transfer MINTER_ROLE to MintController
        if (_minterRoleReceiver != address(0)) {
            _grantRole(MINTER_ROLE, _minterRoleReceiver);
            _revokeRole(MINTER_ROLE, msg.sender);
        }

        // Transfer PHASE_GATE_ROLE to PhaseGate
        if (_phaseGateRoleReceiver != address(0)) {
            _grantRole(PHASE_GATE_ROLE, _phaseGateRoleReceiver);
            _revokeRole(PHASE_GATE_ROLE, msg.sender);
        }

        // Transfer PAUSER_ROLE to emergency multisig
        if (_pauserRoleReceiver != address(0)) {
            _grantRole(PAUSER_ROLE, _pauserRoleReceiver);
            _revokeRole(PAUSER_ROLE, msg.sender);
        }

        emit ProtocolRolesTransferred(_minterRoleReceiver, _phaseGateRoleReceiver, _pauserRoleReceiver);
    }

    event ProtocolRolesTransferred(
        address indexed minterRoleReceiver,
        address indexed phaseGateRoleReceiver,
        address indexed pauserRoleReceiver
    );

    function mint(address to, uint256 amount, uint256 impactId, uint256 phase) external onlyRole(MINTER_ROLE) nonReentrant {
        _requirePhaseActive();
        _checkPhaseEmissionCap(phase, amount);
        _checkHardCap(amount);

        uint256 burnAmount = (amount * burnRate) / 10000;
        uint256 netAmount = amount - burnAmount;

        if (burnAmount > 0) {
            _burn(address(this), burnAmount);
            emit Burned(burnAmount, block.timestamp);
        }

        _mint(to, netAmount);
        emit Minted(to, netAmount, impactId, phase);

        phaseEmissionUsed[phase] += amount;
    }

    function _checkHardCap(uint256 amount) internal view {
        require(totalSupply() + amount <= HARD_CAP, "Hard cap exceeded");
    }

    function _checkPhaseEmissionCap(uint256 phase, uint256 amount) internal view {
        require(phaseEmissionUsed[phase] + amount <= phaseEmissionCap, "Phase emission cap exceeded");
    }

    function _requirePhaseActive() internal view {
        require(currentPhase >= 2, "Phase not active for minting"); // Phase 2+
    }

    function setBurnRate(uint256 newRate) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newRate <= 1000, "Burn rate max 10%"); // max 10%
        burnRate = newRate;
        emit BurnRateUpdated(newRate);
    }

    function setPhaseEmissionCap(uint256 phase, uint256 cap) external onlyRole(PHASE_GATE_ROLE) {
        require(cap <= HARD_CAP, "Cap cannot exceed hard cap");
        phaseEmissionCap = cap;
        emit PhaseEmissionCapSet(phase, cap);
    }

    function activatePhase(uint256 phase) external onlyRole(PHASE_GATE_ROLE) {
        require(phase > currentPhase, "Invalid phase");
        currentPhase = phase;
        emit PhaseActivated(phase, block.timestamp);
    }

    function getChainId() external view returns (uint256) {
        return chainId;
    }

    function contractAddressView() external view returns (address) {
        return contractAddress;
    }

    function _beforeTokenTransfer(address from, address to, uint256 amount) internal override(ERC20, ERC20Pausable, ERC20Permit) {
        super._beforeTokenTransfer(from, to, amount);
        if (currentPhase < 3) { // Phase 3 = Self-Custody
            require(from == address(0) || to == address(0) || hasRole(MINTER_ROLE, from) || hasRole(MINTER_ROLE, to), "Transfers restricted in current phase");
        }
    }
}