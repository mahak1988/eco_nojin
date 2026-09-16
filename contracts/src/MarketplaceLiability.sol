// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title MarketplaceLiability - accountability of village/tribal marketplaces
 * @notice Per-marketplace insurance fund, dispute statistics, accountability
 *         score (0-100) and suspension. The contract owner is the platform.
 */
contract MarketplaceLiability is Ownable, ReentrancyGuard {
    struct Account {
        uint256 insuranceFund;
        uint256 totalDisputes;
        uint256 totalResolved;
        uint256 accountabilityScore; // 0..100
        bool active;
        uint256 lastUpdate;
    }

    mapping(address => Account) public accounts;
    uint256 public minInsuranceFund = 0.1 ether;

    event MarketplaceRegistered(address indexed marketplace, uint256 fund);
    event InsuranceDeposited(address indexed marketplace, uint256 amount);
    event InsuranceUsed(address indexed marketplace, uint256 amount, uint256 indexed orderId);
    event ScoreUpdated(address indexed marketplace, uint256 score);
    event MarketplaceSuspended(address indexed marketplace, string reason);
    event MarketplaceReactivated(address indexed marketplace);

    error InsufficientFund();
    error NotRegistered();
    error AlreadyRegistered();
    error Inactive();
    error BadScore();
    error TransferFailed();

    constructor() Ownable(msg.sender) ReentrancyGuard() {}

    modifier registeredAndActive(address marketplace) {
        if (accounts[marketplace].lastUpdate == 0) revert NotRegistered();
        if (!accounts[marketplace].active) revert Inactive();
        _;
    }

    function registerMarketplace(address marketplace) external payable {
        if (msg.value < minInsuranceFund) revert InsufficientFund();
        if (accounts[marketplace].lastUpdate != 0) revert AlreadyRegistered();
        accounts[marketplace] = Account({
            insuranceFund: msg.value,
            totalDisputes: 0,
            totalResolved: 0,
            accountabilityScore: 100,
            active: true,
            lastUpdate: block.timestamp
        });
        emit MarketplaceRegistered(marketplace, msg.value);
    }

    function depositInsuranceFund(address marketplace) external payable registeredAndActive(marketplace) {
        if (msg.value == 0) revert InsufficientFund();
        accounts[marketplace].insuranceFund += msg.value;
        accounts[marketplace].lastUpdate = block.timestamp;
        emit InsuranceDeposited(marketplace, msg.value);
    }

    /// @notice Pay compensation to a buyer from the marketplace insurance fund.
    function useInsuranceFund(address marketplace, address payable buyer, uint256 amount, uint256 orderId)
        external
        onlyOwner
        nonReentrant
        registeredAndActive(marketplace)
    {
        Account storage a = accounts[marketplace];
        if (a.insuranceFund < amount) revert InsufficientFund();
        a.insuranceFund -= amount;
        (bool ok, ) = buyer.call{value: amount}("");
        if (!ok) revert TransferFailed();
        emit InsuranceUsed(marketplace, amount, orderId);
    }

    function recordDisputeHandling(address marketplace, bool resolved)
        external
        onlyOwner
        registeredAndActive(marketplace)
    {
        Account storage a = accounts[marketplace];
        a.totalDisputes += 1;
        if (resolved) a.totalResolved += 1;
        a.lastUpdate = block.timestamp;
    }

    function updateAccountabilityScore(address marketplace, uint256 score)
        external
        onlyOwner
        registeredAndActive(marketplace)
    {
        if (score > 100) revert BadScore();
        accounts[marketplace].accountabilityScore = score;
        accounts[marketplace].lastUpdate = block.timestamp;
        emit ScoreUpdated(marketplace, score);
    }

    function suspendMarketplace(address marketplace, string calldata reason) external onlyOwner {
        if (accounts[marketplace].lastUpdate == 0) revert NotRegistered();
        accounts[marketplace].active = false;
        emit MarketplaceSuspended(marketplace, reason);
    }

    function reactivateMarketplace(address marketplace) external onlyOwner {
        if (accounts[marketplace].lastUpdate == 0) revert NotRegistered();
        accounts[marketplace].active = true;
        emit MarketplaceReactivated(marketplace);
    }
}
