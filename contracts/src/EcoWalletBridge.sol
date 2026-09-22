// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "./EcoCoin.sol";

/**
 * @title EcoWalletBridge
 * @notice Bridge contract for migrating centralized EcoWallet balances to ERC-20 EcoCoin
 * @dev Uses Merkle tree proofs for batch verification of off-chain balances
 *      Supports KYC verification and self-custody migration
 */
contract EcoWalletBridge is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("DEFAULT_ADMIN_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant MIGRATOR_ROLE = keccak256("MIGRATOR_ROLE");

    IERC20 public immutable ecoCoin;
    address public immutable kycVerifier;

    // Merkle root of user balances (updated by off-chain process)
    bytes32 public merkleRoot;
    uint256 public merkleRootTimestamp;

    // Migration state
    mapping(address => uint256) public claimedAmount;
    mapping(address => bool) public kycVerified;
    mapping(address => address) public externalWallet; // self-custody wallet address

    // Migration limits
    uint256 public maxClaimPerTx;
    uint256 public totalMigrated;
    uint256 public migrationStartTime;
    uint256 public migrationEndTime;

    // Events
    event MerkleRootUpdated(bytes32 indexed root, uint256 timestamp);
    event MigrationClaimed(address indexed user, uint256 amount, address indexed to);
    event KYCVerified(address indexed user, bool verified);
    event SelfCustodyEnabled(address indexed user, address wallet);
    event MigrationConfigUpdated(uint256 maxClaim, uint256 startTime, uint256 endTime);

    constructor(
        address _ecoCoin,
        address _kycVerifier,
        uint256 _maxClaimPerTx,
        uint256 _migrationStartTime,
        uint256 _migrationEndTime
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
        _grantRole(MIGRATOR_ROLE, msg.sender);

        ecoCoin = IERC20(_ecoCoin);
        kycVerifier = _kycVerifier;
        maxClaimPerTx = _maxClaimPerTx;
        migrationStartTime = _migrationStartTime;
        migrationEndTime = _migrationEndTime;

        // Disable until merkle root is set
        migrationStartTime = 0;
        migrationEndTime = 0;
    }

    /**
     * @notice Update Merkle root for batch balance verification
     * @dev Called by off-chain process after computing user balances
     */
    function updateMerkleRoot(bytes32 _merkleRoot) external onlyRole(VERIFIER_ROLE) {
        require(_merkleRoot != bytes32(0), "Invalid merkle root");
        merkleRoot = _merkleRoot;
        merkleRootTimestamp = block.timestamp;
        emit MerkleRootUpdated(_merkleRoot, block.timestamp);
    }

    /**
     * @notice Verify KYC for a user (called by KYC verifier)
     */
    function verifyKYC(address user, bool verified) external onlyRole(VERIFIER_ROLE) {
        kycVerified[user] = verified;
        emit KYCVerified(user, verified);
    }

    /**
     * @notice Enable self-custody for a user
     */
    function enableSelfCustody(address wallet) external onlyRole(MIGRATOR_ROLE) {
        require(wallet != address(0), "Invalid wallet");
        externalWallet[msg.sender] = wallet;
        emit SelfCustodyEnabled(msg.sender, wallet);
    }

    /**
     * @notice Claim migrated ECO tokens using Merkle proof
     * @param _amount Amount to claim
     * @param _proof Merkle proof for user's balance
     * @param _to Destination address (self-custody wallet or same address)
     */
    function claim(
        uint256 _amount,
        bytes32[] calldata _proof,
        address _to
    ) external {
        require(block.timestamp >= migrationStartTime, "Migration not started");
        require(block.timestamp <= migrationEndTime, "Migration ended");
        require(merkleRoot != bytes32(0), "Merkle root not set");
        require(_amount > 0, "Amount must be positive");
        require(_amount <= maxClaimPerTx, "Exceeds max claim per transaction");
        require(claimedAmount[msg.sender] + _amount <= maxClaimPerTx, "User claim limit exceeded");

        // Verify Merkle proof
        bytes32 leaf = keccak256(abi.encodePacked(msg.sender, _amount));
        require(MerkleProof.verify(_proof, merkleRoot, leaf), "Invalid Merkle proof");

        // KYC required for claims
        require(kycVerified[msg.sender] || _amount <= 1000 * 10**18, "KYC required for large claims");

        // Determine destination
        address destination = _to != address(0) ? _to : msg.sender;
        if (_to == address(0) && externalWallet[msg.sender] != address(0)) {
            destination = externalWallet[msg.sender];
        }

        // Update claimed amount
        claimedAmount[msg.sender] += _amount;
        totalMigrated += _amount;

        // Mint tokens to destination
        // Note: This requires MINTER_ROLE on EcoCoin
        // In practice, this would call EcoCoin.mint() via MintController
        // For now, we assume the bridge has MINTER_ROLE or uses a different mechanism

        emit MigrationClaimed(msg.sender, _amount, destination);
    }

    /**
     * @notice Batch claim for multiple users (gas efficient)
     */
    function batchClaim(
        address[] calldata _users,
        uint256[] calldata _amounts,
        bytes32[][] calldata _proofs,
        address[] calldata _destinations
    ) external onlyRole(MIGRATOR_ROLE) {
        require(_users.length == _amounts.length, "Length mismatch");
        require(_users.length == _proofs.length, "Length mismatch");
        require(_users.length == _destinations.length, "Length mismatch");

        for (uint256 i = 0; i < _users.length; i++) {
            address user = _users[i];
            uint256 amount = _amounts[i];
            address destination = _destinations[i];

            require(amount > 0, "Amount must be positive");
            require(amount <= maxClaimPerTx, "Exceeds max claim");
            require(claimedAmount[user] + amount <= maxClaimPerTx, "User limit exceeded");

            bytes32 leaf = keccak256(abi.encodePacked(user, amount));
            require(MerkleProof.verify(_proofs[i], merkleRoot, leaf), "Invalid proof");

            require(kycVerified[user] || amount <= 1000 * 10**18, "KYC required");

            claimedAmount[user] += amount;
            totalMigrated += amount;

            emit MigrationClaimed(user, amount, destination);
        }
    }

    /**
     * @notice Set migration configuration
     */
    function setMigrationConfig(
        uint256 _maxClaimPerTx,
        uint256 _migrationStartTime,
        uint256 _migrationEndTime
    ) external onlyRole(ADMIN_ROLE) {
        require(_migrationStartTime < _migrationEndTime, "Invalid time range");
        maxClaimPerTx = _maxClaimPerTx;
        migrationStartTime = _migrationStartTime;
        migrationEndTime = _migrationEndTime;
        emit MigrationConfigUpdated(_maxClaimPerTx, _migrationStartTime, _migrationEndTime);
    }

    /**
     * @notice Emergency withdrawal for admin
     */
    function emergencyWithdraw(address token, address to, uint256 amount) external onlyRole(ADMIN_ROLE) {
        IERC20(token).safeTransfer(to, amount);
    }

    /**
     * @notice Get user's migration status
     */
    function getMigrationStatus(address user) external view returns (
        uint256 claimed,
        bool kyc,
        address extWallet,
        bool canClaim
    ) {
        return (
            claimedAmount[user],
            kycVerified[user],
            externalWallet[user],
            block.timestamp >= migrationStartTime && block.timestamp <= migrationEndTime
        );
    }

    function supportsInterface(bytes4 interfaceId) public view override(AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}