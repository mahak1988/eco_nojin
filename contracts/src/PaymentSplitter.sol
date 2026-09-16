// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title PaymentSplitter - splits order value between seller, marketplace
 *         (commission) and the platform Landscape Fund (fee), proportional
 *         to configured shares.
 */
contract PaymentSplitter is Ownable, ReentrancyGuard {
    address[] public payees;
    mapping(address => uint256) public shares;
    mapping(address => uint256) public released;
    uint256 public totalShares;
    uint256 public totalReleased;

    event PayeeAdded(address indexed payee, uint256 shares);
    event PaymentReleased(address indexed to, uint256 amount);

    error ZeroShares();
    error DuplicatePayee();
    error NothingDue();
    error TransferFailed();

    constructor() Ownable(msg.sender) ReentrancyGuard() {}

    function addPayee(address payee, uint256 sharesAmount) external onlyOwner {
        if (sharesAmount == 0) revert ZeroShares();
        if (shares[payee] != 0) revert DuplicatePayee();
        payees.push(payee);
        shares[payee] = sharesAmount;
        totalShares += sharesAmount;
        emit PayeeAdded(payee, sharesAmount);
    }

    receive() external payable {}

    /// @notice Release the caller's proportional share of currently held funds.
    function release() external nonReentrant {
        uint256 share = shares[msg.sender];
        if (share == 0) revert ZeroShares();
        uint256 totalReceived = address(this).balance + totalReleased;
        uint256 due = (totalReceived * share) / totalShares - released[msg.sender];
        if (due == 0) revert NothingDue();
        released[msg.sender] += due;
        totalReleased += due;
        (bool ok, ) = payable(msg.sender).call{value: due}("");
        if (!ok) revert TransferFailed();
        emit PaymentReleased(msg.sender, due);
    }
}
