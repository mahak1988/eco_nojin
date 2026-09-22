// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title ImpactCertificate
 * @notice Soulbound ERC-721 for verified ecosystem restoration activities
 * @dev Non-transferable, stores commitment hash and verification status on-chain
 */
contract ImpactCertificate is ERC721, ERC721URIStorage, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant REVOKER_ROLE = keccak256("REVOKER_ROLE");

    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct ActivityData {
        bytes32 commitment;      // hash of off-chain evidence
        uint8 status;            // 0=pending, 1=provisional, 2=verified, 3=disputed, 4=revoked
        uint8 confidence;        // 0-100
        uint256 timestamp;
        uint16 methodologyVersion;
        bytes32 impactHash;      // hash of impact data (species, area, survival, etc.)
    }

    mapping(uint256 => ActivityData) public activityData;
    mapping(address => uint256[]) public userCertificates;
    mapping(bytes32 => uint256) public commitmentToTokenId;

    event CertificateMinted(uint256 indexed tokenId, address indexed to, bytes32 commitment, uint8 confidence, uint256 timestamp);
    event CertificateStatusUpdated(uint256 indexed tokenId, uint8 oldStatus, uint8 newStatus);
    event DisputeRaised(uint256 indexed tokenId, address indexed reporter);
    event DisputeResolved(uint256 indexed tokenId, bool upheld);

    constructor() ERC721("Eco Nojin Impact Certificate", "ENIC") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender); // will transfer to ImpactOracle
        _grantRole(REVOKER_ROLE, msg.sender); // will transfer to Governance
    }

    function mintCertificate(
        address to,
        bytes32 commitment,
        uint8 confidence,
        uint16 methodologyVersion,
        bytes32 impactHash,
        string memory uri
    ) external onlyRole(MINTER_ROLE) returns (uint256) {
        require(commitmentToTokenId[commitment] == 0, "Commitment already exists");

        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();

        _safeMint(to, tokenId, abi.encode(commitment));
        _setTokenURI(tokenId, uri);

        ActivityData memory data = ActivityData({
            commitment: commitment,
            status: 1, // provisional
            confidence: confidence,
            timestamp: block.timestamp,
            methodologyVersion: methodologyVersion,
            impactHash: _computeImpactHash(msg.sender, commitment)
        });

        activityData[tokenId] = data;
        userCertificates[to].push(tokenId);
        commitmentToTokenId[commitment] = tokenId;

        emit CertificateMinted(tokenId, to, commitment, confidence, block.timestamp);
        return tokenId;
    }

    function updateStatus(uint256 tokenId, uint8 newStatus) external onlyRole(REVOKER_ROLE) {
        ActivityData storage data = _getActivityData(tokenId);
        uint8 oldStatus = data.status;
        require(newStatus != oldStatus, "Status unchanged");
        require(newStatus <= 4, "Invalid status");
        data.status = newStatus;
        _storeActivityData(tokenId, data);
        emit CertificateStatusUpdated(tokenId, oldStatus, newStatus);
    }

    function dispute(uint256 tokenId) external {
        ActivityData storage data = _getActivityData(tokenId);
        require(data.status == 2, "Only verified certificates can be disputed");
        data.status = 3; // disputed
        _storeActivityData(tokenId, data);
        emit DisputeRaised(tokenId, msg.sender);
    }

    function resolveDispute(uint256 tokenId, bool upheld) external onlyRole(DEFAULT_ADMIN_ROLE) {
        ActivityData storage data = _getActivityData(tokenId);
        require(data.status == 3, "Not disputed");
        data.status = upheld ? 2 : 4; // verified or revoked
        _storeActivityData(tokenId, data);
        emit DisputeResolved(tokenId, upheld);
    }

    function getActivityData(uint256 tokenId) external view returns (
        bytes32 commitment,
        uint8 status,
        uint8 confidence,
        uint256 timestamp,
        uint16 methodologyVersion,
        bytes32 impactHash
    ) {
        ActivityData storage data = _getActivityData(tokenId);
        return (data.commitment, data.status, data.confidence, data.timestamp, data.methodologyVersion, data.impactHash);
    }

    function _packActivityData(ActivityData memory data) internal pure returns (uint256) {
        return uint256(data.confidence) |
               (uint256(data.status) << 8) |
               (uint256(data.methodologyVersion) << 16) |
               (uint256(data.timestamp) << 32);
    }

    function _unpackActivityData(uint256 packed) internal pure returns (ActivityData memory) {
        ActivityData memory data;
        data.confidence = uint8(packed & 0xFF);
        data.status = uint8((packed >> 8) & 0xFF);
        data.methodologyVersion = uint16((packed >> 16) & 0xFFFF);
        data.timestamp = (packed >> 32) & 0xFFFFFFFFFFFFFFFF;
        // commitment and impactHash stored separately
        return data;
    }

    function _storeActivityData(uint256 tokenId, ActivityData memory data) internal {
        ActivityData storage storageData = activityData[tokenId];
        storageData.status = data.status;
        storageData.confidence = data.confidence;
        storageData.timestamp = data.timestamp;
        storageData.methodologyVersion = data.methodologyVersion;
    }

    function _getActivityData(uint256 tokenId) internal view returns (ActivityData storage) {
        return activityData[tokenId];
    }

    function _computeImpactHash(address owner, bytes32 commitment) internal view returns (bytes32) {
        return keccak256(abi.encodePacked(owner, commitment, block.chainid));
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    // Override _burn to make it work with ERC721URIStorage
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    // Prevent transfers - soulbound
    function _beforeTokenTransfer(address from, address to, uint256 tokenId) internal {
        if (from != address(0) && to != address(0)) {
            revert("ImpactCertificate: non-transferable");
        }
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}