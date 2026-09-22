// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title IdentitySBT - Soulbound identity for rural/tribal marketplace members
 * @notice Self-contained non-transferable identity token (deliberately NOT
 *         inheriting OZ ERC721: its metadata chain pulls utility libraries
 *         that require a newer solc than the one available offline).
 *         Implements the ERC-721 ownership surface (ownerOf/balanceOf/events
 *         + ERC-165) minus transfer hooks, which is the correct shape for a
 *         soulbound asset: tokens can only be minted and revoked (burned).
 */
contract IdentitySBT is Ownable {
    string public constant NAME = "EcoNojin Identity SBT";
    string public constant SYMBOL = "ENID";

    uint256 private _nextTokenId = 1;
    uint256 private _mintedCount;

    struct IdentityInfo {
        uint256 marketplaceId;
        string memberRole; // "resident" | "tribal_member" | "council"
        uint64 issuedAt;
        bool isActive;
    }

    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => IdentityInfo) public identityInfo;
    mapping(address => uint256[]) private _userTokens;
    mapping(address => bool) public authorizedMarketplaces;

    event IdentityIssued(address indexed member, uint256 indexed tokenId, uint256 marketplaceId, string role);
    event IdentityRevoked(address indexed member, uint256 indexed tokenId);
    event MarketplaceAuthorized(address indexed marketplace, bool authorized);
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);

    error SBTNonTransferable();
    error NotAuthorizedMarketplace();
    error AlreadyRevoked();
    error TokenNotFound();

    constructor() {}

    function authorizeMarketplace(address marketplace, bool authorized) external onlyOwner {
        authorizedMarketplaces[marketplace] = authorized;
        emit MarketplaceAuthorized(marketplace, authorized);
    }

    function issueIdentity(address member, uint256 marketplaceId, string calldata memberRole)
        external
        returns (uint256 tokenId)
    {
        if (!authorizedMarketplaces[msg.sender]) revert NotAuthorizedMarketplace();
        tokenId = _nextTokenId++;
        _owners[tokenId] = member;
        _balances[member] += 1;
        _mintedCount += 1;
        _userTokens[member].push(tokenId);
        identityInfo[tokenId] = IdentityInfo({
            marketplaceId: marketplaceId,
            memberRole: memberRole,
            issuedAt: uint64(block.timestamp),
            isActive: true
        });
        emit Transfer(address(0), member, tokenId);
        emit IdentityIssued(member, tokenId, marketplaceId, memberRole);
    }

    function revokeIdentity(uint256 tokenId) external {
        if (!authorizedMarketplaces[msg.sender]) revert NotAuthorizedMarketplace();
        if (!identityInfo[tokenId].isActive) revert AlreadyRevoked();
        identityInfo[tokenId].isActive = false;
        address member = _owners[tokenId];
        _balances[member] -= 1;
        delete _owners[tokenId];
        emit IdentityRevoked(member, tokenId);
        emit Transfer(member, address(0), tokenId);
    }

    function isMemberOfMarketplace(address user, uint256 marketplaceId) public view returns (bool) {
        uint256[] storage tokens = _userTokens[user];
        for (uint256 i = 0; i < tokens.length; i++) {
            IdentityInfo storage info = identityInfo[tokens[i]];
            if (info.marketplaceId == marketplaceId && info.isActive) return true;
        }
        return false;
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = _owners[tokenId];
        if (owner == address(0)) revert TokenNotFound();
        return owner;
    }

    function balanceOf(address member) public view returns (uint256) {
        return _balances[member];
    }

    function totalIssued() public view returns (uint256) {
        return _mintedCount;
    }

    function supportsInterface(bytes4 interfaceId) public pure returns (bool) {
        return interfaceId == 0x01ffc9a7 // ERC-165
            || interfaceId == 0x80ac58cd; // ERC-721 (ownership surface; transfers disabled by design)
    }
}
