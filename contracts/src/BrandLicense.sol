// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title BrandLicense - collective village/tribal brand licenses for shops
 * @notice Individual shops operate as sub-brands of a marketplace brand;
 *         the platform issues, renews and revokes the licenses.
 */
contract BrandLicense {
    struct License {
        address shop;
        uint256 marketplaceId;
        string termsURI;
        uint64 validUntil;
        bool revoked;
    }

    uint256 private _nextId = 1;
    mapping(uint256 => License) public licenses;
    mapping(address => uint256[]) public shopLicenses;

    address public owner;

    event LicenseIssued(uint256 indexed licenseId, address indexed shop, uint256 marketplaceId, uint64 validUntil);
    event LicenseRevoked(uint256 indexed licenseId);

    error NotPlatform();
    error OwnableUnauthorizedAccount(address account);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert OwnableUnauthorizedAccount(msg.sender);
        }
        _;
    }

    function issueLicense(address shop, uint256 marketplaceId, string calldata termsURI, uint64 durationDays)
        external
        onlyOwner
        returns (uint256 licenseId)
    {
        licenseId = _nextId++;
        uint64 validUntil = uint64(block.timestamp + durationDays * 1 days);
        licenses[licenseId] = License({shop: shop, marketplaceId: marketplaceId, termsURI: termsURI, validUntil: validUntil, revoked: false});
        shopLicenses[shop].push(licenseId);
        emit LicenseIssued(licenseId, shop, marketplaceId, validUntil);
    }

    function revokeLicense(uint256 licenseId) external onlyOwner {
        licenses[licenseId].revoked = true;
        emit LicenseRevoked(licenseId);
    }

    function isValid(uint256 licenseId) public view returns (bool) {
        License storage l = licenses[licenseId];
        return !l.revoked && block.timestamp <= l.validUntil;
    }
}