// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title LandscapeFund
 * @author Eco Nojin Team
 * @notice قرارداد هوشمند صندوق مدیریت یکپارچه منظر
 */

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract LandscapeFund is AccessControl, Pausable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    string public constant VERSION = "2.0.0";
    uint256 public constant MAX_FEE_BPS = 500;
    uint256 public constant DEFAULT_FEE_BPS = 100;
    
    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");
    
    Counters.Counter private _villageIdCounter;
    
    struct Village {
        uint256 id;
        string villageId;
        string name;
        address manager;
        uint256 feeBps;
        uint256 totalCollected;
        uint256 totalDistributed;
        uint256 pendingWithdrawal;
        bool active;
    }
    
    mapping(uint256 => Village) public villages;
    mapping(string => uint256) public villageIdToNumber;
    
    uint256 public totalCollectedGlobal;
    uint256 public totalDistributedGlobal;
    
    event VillageRegistered(uint256 indexed id, string villageId, address indexed manager);
    event FeeCollected(uint256 indexed villageId, uint256 amount, string source);
    event WithdrawalCompleted(uint256 indexed villageId, uint256 amount, address indexed manager);
    
    error VillageNotFound(uint256 villageId);
    error VillageAlreadyExists(string villageId);
    error InvalidFee(uint256 feeBps);
    error InvalidAmount(uint256 amount);
    error InsufficientFunds();
    error InvalidAddress(address addr);
    error Unauthorized(address caller);
    
    modifier villageExists(uint256 villageId) {
        if (villages[villageId].id == 0) revert VillageNotFound(villageId);
        _;
    }
    
    modifier onlyVillageManager(uint256 villageId) {
        if (msg.sender != villages[villageId].manager) revert Unauthorized(msg.sender);
        _;
    }
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MANAGER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(DISTRIBUTOR_ROLE, msg.sender);
    }
    
    function registerVillage(
        string memory villageId, string memory name,
        address manager, uint256 feeBps
    ) external onlyRole(MANAGER_ROLE) whenNotPaused returns (uint256 id) {
        if (villageIdToNumber[villageId] != 0) revert VillageAlreadyExists(villageId);
        if (manager == address(0)) revert InvalidAddress(manager);
        if (feeBps > MAX_FEE_BPS) revert InvalidFee(feeBps);
        
        _villageIdCounter.increment();
        id = _villageIdCounter.current();
        
        villages[id] = Village({
            id: id, villageId: villageId, name: name,
            manager: manager,
            feeBps: feeBps == 0 ? DEFAULT_FEE_BPS : feeBps,
            totalCollected: 0, totalDistributed: 0,
            pendingWithdrawal: 0, active: true
        });
        
        villageIdToNumber[villageId] = id;
        emit VillageRegistered(id, villageId, manager);
    }
    
    function collectFee(uint256 villageId, string memory source)
        external payable whenNotPaused nonReentrant villageExists(villageId) {
        if (msg.value == 0) revert InvalidAmount(msg.value);
        
        villages[villageId].totalCollected += msg.value;
        villages[villageId].pendingWithdrawal += msg.value;
        totalCollectedGlobal += msg.value;
        
        emit FeeCollected(villageId, msg.value, source);
    }
    
    function requestWithdrawal(uint256 villageId)
        external whenNotPaused nonReentrant villageExists(villageId) onlyVillageManager(villageId) {
        uint256 amount = villages[villageId].pendingWithdrawal;
        if (amount == 0) revert InsufficientFunds();
        
        villages[villageId].pendingWithdrawal = 0;
        villages[villageId].totalDistributed += amount;
        totalDistributedGlobal += amount;
        
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
        
        emit WithdrawalCompleted(villageId, amount, msg.sender);
    }
    
    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
    
    receive() external payable whenNotPaused {
        totalCollectedGlobal += msg.value;
    }
}
