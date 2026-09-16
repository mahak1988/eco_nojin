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
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract CarbonCredit is ERC20, ERC20Burnable, ERC20Pausable, AccessControl, ReentrancyGuard {
    string public constant VERSION = "2.0.0";
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;
    uint256 public constant MIN_MINT_AMOUNT = 1 * 10**18;

    bytes32 public constant ADMIN_ROLE = DEFAULT_ADMIN_ROLE;
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");

    uint256 private _projectIdCounter;
    uint256 public retirementCounter;

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
        uint256 totalCreditsRetired;
    }

    struct Issuance {
        bytes32 id;
        uint256 projectId;
        address recipient;
        uint256 amount;
        uint256 retiredAmount;
        uint256 createdAt;
        bool exists;
    }

    struct Retirement {
        bytes32 id;
        bytes32 issuanceId;
        address retiredBy;
        uint256 amount;
        string reason;
        uint256 timestamp;
        bool exists;
    }

    struct AccountFreeze {
        bool frozen;
        address actor;
        address authority;
        string reason;
        uint256 timestamp;
    }

    mapping(uint256 => CarbonProject) public projects;
    mapping(string => uint256) public projectIdToNumber;
    mapping(bytes32 => Issuance) public issuances;
    mapping(bytes32 => bool) public issuanceUsed;
    mapping(bytes32 => Retirement) public retirements;
    mapping(bytes32 => bool) public retirementUsed;
    mapping(address => AccountFreeze) public freezeRecords;
    mapping(address => bool) public frozenAccounts;
    mapping(bytes32 => mapping(address => uint256)) public issuanceBalances;
    mapping(address => bytes32[]) private _issuanceIdsByAccount;
    mapping(address => mapping(bytes32 => bool)) private _issuanceKnownByAccount;

    uint256 public totalCreditsIssued;
    uint256 public totalRetiredCredits;
    string public metadataURI;
    uint256 public immutable chainId;
    address public immutable contractAddress;

    event ProjectRegistered(uint256 indexed id, string projectId, address indexed owner);
    event ProjectVerified(uint256 indexed id, address indexed verifier);
    event CreditsMinted(uint256 indexed projectId, address indexed to, uint256 amount);
    event CreditsIssued(uint256 indexed projectId, bytes32 indexed issuanceId, address indexed to, uint256 amount);
    event CreditsRetired(address indexed retiredBy, uint256 amount, string reason);
    event CreditsRetiredByIssuance(
        address indexed retiredBy,
        bytes32 indexed issuanceId,
        bytes32 indexed retirementId,
        uint256 amount,
        string reason
    );
    event AccountFrozen(address indexed actor, address indexed authority, string reason, uint256 timestamp);
    event AccountUnfrozen(address indexed actor, address indexed authority, string reason, uint256 timestamp);
    event MetadataURIUpdated(string previousURI, string newURI);
    event ProjectMetadataURIUpdated(uint256 indexed projectId, string previousURI, string newURI);

    error ProjectNotFound(uint256 projectId);
    error ProjectAlreadyExists(string projectId);
    error ProjectAlreadyVerified(uint256 projectId);
    error ProjectNotVerified(uint256 projectId);
    error ProjectInactive(uint256 projectId);
    error InvalidProjectData();
    error MaxSupplyExceeded();
    error InvalidAmount(uint256 amount);
    error InvalidAddress(address addr);
    error InvalidIssuanceId();
    error IssuanceAlreadyUsed(bytes32 issuanceId);
    error IssuanceNotFound(bytes32 issuanceId);
    error IssuanceProjectMismatch(bytes32 issuanceId, uint256 expectedProjectId, uint256 actualProjectId);
    error InvalidRetirementId();
    error RetirementAlreadyUsed(bytes32 retirementId);
    error RetirementAmountExceeded(bytes32 issuanceId, uint256 available, uint256 requested);
    error DoubleCountingPrevented();
    error FrozenAccount(address actor);
    error AccountAlreadyFrozen(address actor);
    error AccountNotFrozen(address actor);
    error UnauthorizedAuthority(address actor, address authority);

    modifier projectExists(uint256 projectId) {
        if (projects[projectId].id == 0) revert ProjectNotFound(projectId);
        _;
    }

    constructor() ERC20("Eco Nojin Carbon Credit", "ENCC") {
        chainId = block.chainid;
        contractAddress = address(this);
        _grantRole(ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
    }

    function registerProject(
        string memory projectId,
        string memory projectType,
        string memory location,
        string memory newProjectMetadataURI
    ) external onlyRole(MINTER_ROLE) whenNotPaused returns (uint256 id) {
        if (bytes(projectId).length == 0 || bytes(projectType).length == 0 || bytes(location).length == 0) {
            revert InvalidProjectData();
        }
        if (projectIdToNumber[projectId] != 0) revert ProjectAlreadyExists(projectId);

        id = ++_projectIdCounter;
        projects[id] = CarbonProject({
            id: id,
            projectId: projectId,
            projectType: projectType,
            location: location,
            owner: msg.sender,
            startDate: block.timestamp,
            verified: false,
            active: true,
            totalCreditsMinted: 0,
            metadataURI: newProjectMetadataURI,
            totalCreditsRetired: 0
        });
        projectIdToNumber[projectId] = id;
        emit ProjectRegistered(id, projectId, msg.sender);
    }

    function verifyProject(uint256 projectId) external onlyRole(VERIFIER_ROLE) projectExists(projectId) {
        _verifyProject(projectId);
    }

    function validateProject(uint256 projectId) external onlyRole(VERIFIER_ROLE) projectExists(projectId) {
        _verifyProject(projectId);
    }

    function mint(
        uint256 projectId,
        bytes32 issuanceId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        _mintIssuance(projectId, issuanceId, to, amount);
    }

    function mint(
        uint256 projectId,
        string calldata issuanceId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        _mintIssuance(projectId, keccak256(bytes(issuanceId)), to, amount);
    }

    function mint(
        uint256 projectId,
        uint256 issuanceId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        if (issuanceId == 0) revert InvalidIssuanceId();
        _mintIssuance(projectId, bytes32(issuanceId), to, amount);
    }

    function mint(
        uint256 projectId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        _mintIssuance(projectId, keccak256(abi.encode(projectId, to, amount)), to, amount);
    }

    function issueCredits(
        uint256 projectId,
        bytes32 issuanceId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        _mintIssuance(projectId, issuanceId, to, amount);
    }

    function issueCredits(
        uint256 projectId,
        string calldata issuanceId,
        address to,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused nonReentrant projectExists(projectId) {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        _mintIssuance(projectId, keccak256(bytes(issuanceId)), to, amount);
    }

    function retire(
        bytes32 retirementId,
        bytes32 issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        _retireIssuance(retirementId, issuanceId, msg.sender, amount, reason);
    }

    function retire(
        bytes32 retirementId,
        string calldata issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        _retireIssuance(retirementId, keccak256(bytes(issuanceId)), msg.sender, amount, reason);
    }

    function retire(
        bytes32 issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        bytes32 retirementId = _nextRetirementId(issuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, issuanceId, msg.sender, amount, reason);
    }

    function retire(
        string calldata issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        bytes32 hashedIssuanceId = keccak256(bytes(issuanceId));
        bytes32 retirementId = _nextRetirementId(hashedIssuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, hashedIssuanceId, msg.sender, amount, reason);
    }

    function retire(
        uint256 projectId,
        bytes32 issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant projectExists(projectId) {
        Issuance storage issuance = issuances[issuanceId];
        if (issuance.projectId != projectId) {
            revert IssuanceProjectMismatch(issuanceId, projectId, issuance.projectId);
        }
        bytes32 retirementId = _nextRetirementId(issuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, issuanceId, msg.sender, amount, reason);
    }

    function retire(
        uint256 projectId,
        string calldata issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant projectExists(projectId) {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        bytes32 hashedIssuanceId = keccak256(bytes(issuanceId));
        Issuance storage issuance = issuances[hashedIssuanceId];
        if (issuance.projectId != projectId) {
            revert IssuanceProjectMismatch(hashedIssuanceId, projectId, issuance.projectId);
        }
        bytes32 retirementId = _nextRetirementId(hashedIssuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, hashedIssuanceId, msg.sender, amount, reason);
    }

    function retire(
        uint256 projectId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant projectExists(projectId) {
        _retireProject(projectId, msg.sender, amount, reason);
    }

    function retire(
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        _retireGeneric(msg.sender, amount, reason);
    }

    function retireIssuance(
        bytes32 issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        bytes32 retirementId = _nextRetirementId(issuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, issuanceId, msg.sender, amount, reason);
    }

    function retireIssuance(
        string calldata issuanceId,
        uint256 amount,
        string calldata reason
    ) external whenNotPaused nonReentrant {
        if (bytes(issuanceId).length == 0) revert InvalidIssuanceId();
        bytes32 hashedIssuanceId = keccak256(bytes(issuanceId));
        bytes32 retirementId = _nextRetirementId(hashedIssuanceId, msg.sender, amount, reason);
        _retireIssuance(retirementId, hashedIssuanceId, msg.sender, amount, reason);
    }

    function freezeAccount(
        address actor,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        _freezeAccount(actor, msg.sender, reason);
    }

    function freezeAccount(
        address actor,
        address authority,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!hasRole(ADMIN_ROLE, authority)) {
            revert AccessControlUnauthorizedAccount(authority, ADMIN_ROLE);
        }
        _freezeAccount(actor, authority, reason);
    }

    function freeze(
        address actor,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        _freezeAccount(actor, msg.sender, reason);
    }

    function freeze(
        address actor,
        address authority,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!hasRole(ADMIN_ROLE, authority)) {
            revert AccessControlUnauthorizedAccount(authority, ADMIN_ROLE);
        }
        _freezeAccount(actor, authority, reason);
    }

    function unfreezeAccount(
        address actor,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!frozenAccounts[actor]) revert AccountNotFrozen(actor);
        if (msg.sender != freezeRecords[actor].authority) {
            revert UnauthorizedAuthority(actor, msg.sender);
        }
        _unfreezeAccount(actor, msg.sender, reason);
    }

    function unfreezeAccount(
        address actor,
        address authority,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!frozenAccounts[actor]) revert AccountNotFrozen(actor);
        if (authority != freezeRecords[actor].authority || msg.sender != authority) {
            revert UnauthorizedAuthority(actor, authority);
        }
        _unfreezeAccount(actor, authority, reason);
    }

    function unfreeze(
        address actor,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!frozenAccounts[actor]) revert AccountNotFrozen(actor);
        if (msg.sender != freezeRecords[actor].authority) {
            revert UnauthorizedAuthority(actor, msg.sender);
        }
        _unfreezeAccount(actor, msg.sender, reason);
    }

    function unfreeze(
        address actor,
        address authority,
        string calldata reason
    ) external onlyRole(ADMIN_ROLE) {
        if (!frozenAccounts[actor]) revert AccountNotFrozen(actor);
        if (authority != freezeRecords[actor].authority || msg.sender != authority) {
            revert UnauthorizedAuthority(actor, authority);
        }
        _unfreezeAccount(actor, authority, reason);
    }

    function setMetadataURI(string calldata newMetadataURI) external onlyRole(ADMIN_ROLE) {
        string memory previousURI = metadataURI;
        metadataURI = newMetadataURI;
        emit MetadataURIUpdated(previousURI, newMetadataURI);
    }

    function setProjectMetadataURI(
        uint256 projectId,
        string calldata newMetadataURI
    ) external onlyRole(ADMIN_ROLE) projectExists(projectId) {
        string memory previousURI = projects[projectId].metadataURI;
        projects[projectId].metadataURI = newMetadataURI;
        emit ProjectMetadataURIUpdated(projectId, previousURI, newMetadataURI);
    }

    function projectMetadataURI(
        uint256 projectId
    ) external view projectExists(projectId) returns (string memory) {
        return projects[projectId].metadataURI;
    }

    function issuanceExists(bytes32 issuanceId) external view returns (bool) {
        return issuanceUsed[issuanceId];
    }

    function issuanceBalanceOf(
        bytes32 issuanceId,
        address account
    ) external view returns (uint256) {
        return issuanceBalances[issuanceId][account];
    }

    function retirementExists(bytes32 retirementId) external view returns (bool) {
        return retirementUsed[retirementId];
    }

    function totalCreditsMinted() external view returns (uint256) {
        return totalCreditsIssued;
    }

    function totalCreditsRetired() external view returns (uint256) {
        return totalRetiredCredits;
    }

    function projectCount() external view returns (uint256) {
        return _projectIdCounter;
    }

    function getProjectId(
        string calldata projectId
    ) external view returns (uint256) {
        return projectIdToNumber[projectId];
    }

    function isFrozen(address actor) external view returns (bool) {
        return frozenAccounts[actor];
    }

    function getChainId() external view returns (uint256) {
        return chainId;
    }

    function chainID() external view returns (uint256) {
        return chainId;
    }

    function getContractAddress() external view returns (address) {
        return contractAddress;
    }

    function burn(uint256 amount) public override {
        if (frozenAccounts[msg.sender]) revert FrozenAccount(msg.sender);
        _burnWithLots(msg.sender, amount, false);
    }

    function burnFrom(address account, uint256 amount) public override {
        if (frozenAccounts[account]) revert FrozenAccount(account);
        _spendAllowance(account, msg.sender, amount);
        _burnWithLots(account, amount, false);
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function _verifyProject(uint256 projectId) private {
        if (projects[projectId].verified) revert ProjectAlreadyVerified(projectId);
        projects[projectId].verified = true;
        projects[projectId].active = true;
        emit ProjectVerified(projectId, msg.sender);
    }

    function _mintIssuance(
        uint256 projectId,
        bytes32 issuanceId,
        address to,
        uint256 amount
    ) private {
        if (issuanceId == bytes32(0)) revert InvalidIssuanceId();
        if (issuanceUsed[issuanceId]) revert IssuanceAlreadyUsed(issuanceId);
        if (to == address(0)) revert InvalidAddress(to);
        if (amount < MIN_MINT_AMOUNT) revert InvalidAmount(amount);
        if (!projects[projectId].verified) revert ProjectNotVerified(projectId);
        if (!projects[projectId].active) revert ProjectInactive(projectId);
        if (frozenAccounts[to]) revert FrozenAccount(to);
        if (totalSupply() + amount > MAX_SUPPLY) revert MaxSupplyExceeded();

        issuanceUsed[issuanceId] = true;
        if (!_issuanceKnownByAccount[to][issuanceId]) {
            _issuanceKnownByAccount[to][issuanceId] = true;
            _issuanceIdsByAccount[to].push(issuanceId);
        }
        issuanceBalances[issuanceId][to] += amount;
        issuances[issuanceId] = Issuance({
            id: issuanceId,
            projectId: projectId,
            recipient: to,
            amount: amount,
            retiredAmount: 0,
            createdAt: block.timestamp,
            exists: true
        });
        _mint(to, amount);
        projects[projectId].totalCreditsMinted += amount;
        totalCreditsIssued += amount;
        emit CreditsMinted(projectId, to, amount);
        emit CreditsIssued(projectId, issuanceId, to, amount);
    }

    function _retireIssuance(
        bytes32 retirementId,
        bytes32 issuanceId,
        address retiredBy,
        uint256 amount,
        string memory reason
    ) private {
        if (retirementId == bytes32(0)) revert InvalidRetirementId();
        if (retirementUsed[retirementId]) revert RetirementAlreadyUsed(retirementId);
        Issuance storage issuance = issuances[issuanceId];
        if (!issuance.exists) revert IssuanceNotFound(issuanceId);
        if (amount == 0) revert InvalidAmount(amount);
        if (frozenAccounts[retiredBy]) revert FrozenAccount(retiredBy);
        uint256 available = issuance.amount - issuance.retiredAmount;
        if (amount > available) revert RetirementAmountExceeded(issuanceId, available, amount);
        if (balanceOf(retiredBy) < amount) revert InvalidAmount(amount);
        if (issuanceBalances[issuanceId][retiredBy] < amount) revert InvalidAmount(amount);
        if (totalRetiredCredits + amount > totalCreditsIssued) revert DoubleCountingPrevented();

        CarbonProject storage project = projects[issuance.projectId];
        if (project.totalCreditsRetired + amount > project.totalCreditsMinted) {
            revert DoubleCountingPrevented();
        }

        retirementUsed[retirementId] = true;
        retirements[retirementId] = Retirement({
            id: retirementId,
            issuanceId: issuanceId,
            retiredBy: retiredBy,
            amount: amount,
            reason: reason,
            timestamp: block.timestamp,
            exists: true
        });
        issuanceBalances[issuanceId][retiredBy] -= amount;
        _burn(retiredBy, amount);
        issuance.retiredAmount += amount;
        projects[issuance.projectId].totalCreditsRetired += amount;
        totalRetiredCredits += amount;
        emit CreditsRetired(retiredBy, amount, reason);
        emit CreditsRetiredByIssuance(retiredBy, issuanceId, retirementId, amount, reason);
    }

    function _retireProject(
        uint256 projectId,
        address retiredBy,
        uint256 amount,
        string memory reason
    ) private {
        if (amount == 0) revert InvalidAmount(amount);
        if (frozenAccounts[retiredBy]) revert FrozenAccount(retiredBy);
        if (balanceOf(retiredBy) < amount) revert InvalidAmount(amount);
        CarbonProject storage project = projects[projectId];
        uint256 available = project.totalCreditsMinted - project.totalCreditsRetired;
        if (amount > available) revert DoubleCountingPrevented();
        if (totalRetiredCredits + amount > totalCreditsIssued) revert DoubleCountingPrevented();
        _burnProjectLots(retiredBy, projectId, amount);
        totalRetiredCredits += amount;
        emit CreditsRetired(retiredBy, amount, reason);
    }

    function _retireGeneric(
        address retiredBy,
        uint256 amount,
        string memory reason
    ) private {
        if (amount == 0) revert InvalidAmount(amount);
        if (frozenAccounts[retiredBy]) revert FrozenAccount(retiredBy);
        if (balanceOf(retiredBy) < amount) revert InvalidAmount(amount);
        if (totalRetiredCredits + amount > totalCreditsIssued) revert DoubleCountingPrevented();
        _burnWithLots(retiredBy, amount, true);
        totalRetiredCredits += amount;
        emit CreditsRetired(retiredBy, amount, reason);
    }

    function _moveIssuanceBalances(
        address from,
        address to,
        uint256 value
    ) private {
        if (value == 0 || from == to) return;
        uint256 remaining = value;
        bytes32[] storage issuanceIds = _issuanceIdsByAccount[from];
        for (uint256 i = 0; i < issuanceIds.length && remaining > 0; ++i) {
            bytes32 issuanceId = issuanceIds[i];
            uint256 available = issuanceBalances[issuanceId][from];
            uint256 moved = available < remaining ? available : remaining;
            if (moved == 0) continue;
            issuanceBalances[issuanceId][from] -= moved;
            if (!_issuanceKnownByAccount[to][issuanceId]) {
                _issuanceKnownByAccount[to][issuanceId] = true;
                _issuanceIdsByAccount[to].push(issuanceId);
            }
            issuanceBalances[issuanceId][to] += moved;
            remaining -= moved;
        }
        if (remaining != 0) revert InvalidAmount(value);
    }

    function _burnProjectLots(
        address account,
        uint256 projectId,
        uint256 amount
    ) private {
        uint256 remaining = amount;
        bytes32[] storage issuanceIds = _issuanceIdsByAccount[account];
        for (uint256 i = 0; i < issuanceIds.length && remaining > 0; ++i) {
            bytes32 issuanceId = issuanceIds[i];
            if (issuances[issuanceId].projectId != projectId) continue;
            uint256 available = issuanceBalances[issuanceId][account];
            uint256 burned = available < remaining ? available : remaining;
            if (burned == 0) continue;
            issuanceBalances[issuanceId][account] -= burned;
            issuances[issuanceId].retiredAmount += burned;
            projects[projectId].totalCreditsRetired += burned;
            remaining -= burned;
        }
        if (remaining != 0) revert InvalidAmount(amount);
        _burn(account, amount);
    }

    function _burnWithLots(
        address account,
        uint256 amount,
        bool recordRetirement
    ) private {
        uint256 remaining = amount;
        bytes32[] storage issuanceIds = _issuanceIdsByAccount[account];
        for (uint256 i = 0; i < issuanceIds.length && remaining > 0; ++i) {
            bytes32 issuanceId = issuanceIds[i];
            uint256 available = issuanceBalances[issuanceId][account];
            uint256 burned = available < remaining ? available : remaining;
            if (burned == 0) continue;
            issuanceBalances[issuanceId][account] -= burned;
            if (recordRetirement) {
                Issuance storage issuance = issuances[issuanceId];
                issuance.retiredAmount += burned;
                projects[issuance.projectId].totalCreditsRetired += burned;
            }
            remaining -= burned;
        }
        if (remaining != 0) revert InvalidAmount(amount);
        _burn(account, amount);
    }

    function _freezeAccount(
        address actor,
        address authority,
        string memory reason
    ) private {
        if (actor == address(0)) revert InvalidAddress(actor);
        if (frozenAccounts[actor]) revert AccountAlreadyFrozen(actor);
        frozenAccounts[actor] = true;
        freezeRecords[actor] = AccountFreeze({
            frozen: true,
            actor: actor,
            authority: authority,
            reason: reason,
            timestamp: block.timestamp
        });
        emit AccountFrozen(actor, authority, reason, block.timestamp);
    }

    function _unfreezeAccount(
        address actor,
        address authority,
        string memory reason
    ) private {
        if (actor == address(0)) revert InvalidAddress(actor);
        if (!frozenAccounts[actor]) revert AccountNotFrozen(actor);
        frozenAccounts[actor] = false;
        freezeRecords[actor] = AccountFreeze({
            frozen: false,
            actor: actor,
            authority: authority,
            reason: reason,
            timestamp: block.timestamp
        });
        emit AccountUnfrozen(actor, authority, reason, block.timestamp);
    }

    function _nextRetirementId(
        bytes32 issuanceId,
        address retiredBy,
        uint256 amount,
        string memory reason
    ) private returns (bytes32) {
        uint256 nonce = retirementCounter++;
        return keccak256(abi.encode(issuanceId, retiredBy, amount, reason, block.timestamp, nonce));
    }

    function _update(
        address from,
        address to,
        uint256 value
    ) internal override(ERC20, ERC20Pausable) {
        if (from != address(0) && to != address(0)) {
            if (frozenAccounts[from]) revert FrozenAccount(from);
            if (frozenAccounts[to]) revert FrozenAccount(to);
            _moveIssuanceBalances(from, to, value);
        }
        super._update(from, to, value);
    }
}
