// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title CarbonCredit
 * @author Eco Nojin Team
 * @notice قرارداد هوشمند مدیریت اعتبارات کربن با امنیت کامل
 */

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract CarbonCredit is ERC20, ERC20Burnable, ERC20Pausable, AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    string public constant VERSION = "2.0.0";
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;
    uint256 public constant MIN_MINT_AMOUNT = 1 * 10**18;
    
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    
    Counters.Counter private _projectIdCounter;
    
    struct CarbonProject {
        uint256 id;
        string projectId;
        string projectType;
        string location;
        address owner;
        uint256 startDate;
        bool verified;
        bool active;
        uint256 totalCreditsMinted;
        string metadataURI;
    }
    
    mapping(uint256 => CarbonProject) public projects;
    mapping(string => uint256) public projectIdToNumber;
    uint256 public totalRetiredCredits;
    
    event ProjectRegistered(uint256 indexed id, string projectId, address indexed owner);
    event ProjectVerified(uint256 indexed id, address indexed verifier);
    event CreditsMinted(uint256 indexed projectId, address indexed to, uint256 amount);
    event CreditsRetired(address indexed retiredBy, uint256 amount, string reason);
    
    error ProjectNotFound(uint256 projectId);
    error ProjectAlreadyExists(string projectId);
    error ProjectNotVerified(uint256 projectId);
    error MaxSupplyExceeded();
    error InvalidAmount(uint256 amount);
    error InvalidAddress(address addr);
    
    modifier projectExists(uint256 projectId) {
        if (projects[projectId].id == 0) revert ProjectNotFound(projectId);
        _;
    }
    
    constructor() ERC20("Eco Nojin Carbon Credit", "ENCC") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
    }
    
    function registerProject(
        string memory projectId,
        string memory projectType,
        string memory location,
        string memory metadataURI
    ) external onlyRole(MINTER_ROLE) whenNotPaused returns (uint256 id) {
        if (projectIdToNumber[projectId] != 0) revert ProjectAlreadyExists(projectId);
        
        _projectIdCounter.increment();
        id = _projectIdCounter.current();
        
        projects[id] = CarbonProject({
            id: id, projectId: projectId,
            projectType: projectType, location: location,
            owner: msg.sender, startDate: block.timestamp,
            verified: false, active: true,
            totalCreditsMinted: 0, metadataURI: metadataURI
        });
        
        projectIdToNumber[projectId] = id;
        emit ProjectRegistered(id, projectId, msg.sender);
    }
    
    function verifyProject(uint256 projectId) external onlyRole(VERIFIER_ROLE) projectExists(projectId) {
        projects[projectId].verified = true;
        emit ProjectVerified(projectId, msg.sender);
    }
    
    function mint(uint256 projectId, address to, uint256 amount)
        external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        if (to == address(0)) revert InvalidAddress(to);
        if (amount < MIN_MINT_AMOUNT) revert InvalidAmount(amount);
        if (!projects[projectId].verified) revert ProjectNotVerified(projectId);
        if (totalSupply() + amount > MAX_SUPPLY) revert MaxSupplyExceeded();
        
        _mint(to, amount);
        projects[projectId].totalCreditsMinted += amount;
        emit CreditsMinted(projectId, to, amount);
    }
    
    function retire(uint256 amount, string memory reason)
        external whenNotPaused nonReentrant {
        if (amount == 0) revert InvalidAmount(amount);
        if (balanceOf(msg.sender) < amount) revert InvalidAmount(amount);
        
        _burn(msg.sender, amount);
        totalRetiredCredits += amount;
        emit CreditsRetired(msg.sender, amount, reason);
    }
    
    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
    
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal override(ERC20, ERC20Pausable) {
        super._beforeTokenTransfer(from, to, amount);
    }
}
