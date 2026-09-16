// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title BrandLicense - collective village/tribal brand licenses for shops
 * @notice Individual shops operate as sub-brands of a marketplace brand;
 *         the platform issues, renews and revokes the licenses.
 */
contract BrandLicense is Ownable {
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

    event LicenseIssued(uint256 indexed licenseId, address indexed shop, uint256 marketplaceId, uint64 validUntil);
    event LicenseRevoked(uint256 indexed licenseId);

    error NotPlatform();

    constructor() Ownable(msg.sender) {}

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
