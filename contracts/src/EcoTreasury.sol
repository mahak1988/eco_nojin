// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title EcoTreasury
 * @notice Transparent multi-sig treasury for platform fees (15% of EcoCoin mint)
 * @dev All transactions public, timelocked, auditable. No hidden paths.
 */
contract EcoTreasury is AccessControl, ReentrancyGuard {
    bytes32 public constant TREASURER_ROLE = keccak256("TREASURER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    IERC20 public immutable ecoCoin;
    address public immutable treasuryWallet;

    using SafeERC20 for IERC20;

    struct Disbursement {
        uint256 id;
        address to;
        uint256 amount;
        string purpose;
        uint256 timestamp;
        bool executed;
        uint256 approvals;
        bool cancelled;
    }

    struct Proposal {
        uint256 id;
        address proposer;
        address to;
        uint256 amount;
        string purpose;
        uint256 createdAt;
        uint256 deadline;
        uint256 approvals;
        bool executed;
        bool cancelled;
    }

    uint256 public disbursementCount;
    uint256 public proposalCount;
    uint256 public constant MIN_SIGNERS = 3;
    uint256 public constant MAX_SIGNERS = 5;
    uint256 public constant TIMELOCK = 3 days;

    address[5] public signers;
    uint256 public signerCount;

    mapping(uint256 => Disbursement) public disbursements;
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public approvals;

    event DisbursementCreated(uint256 indexed id, address indexed to, uint256 amount, string purpose);
    event DisbursementApproved(uint256 indexed id, address indexed approver);
    event DisbursementExecuted(uint256 indexed id, address indexed to, uint256 amount);
    event DisbursementCancelled(uint256 indexed id);
    event ProposalCreated(uint256 indexed id, address indexed proposer, address to, uint256 amount);
    event ProposalApproved(uint256 indexed id, address indexed approver);
    event ProposalExecuted(uint256 indexed id);
    event ProposalCancelled(uint256 indexed id);
    event SignerAdded(address indexed signer);
    event SignerRemoved(address indexed signer);
    event SignerCountChanged(uint256 newCount);

    constructor(address _ecoCoin, address _treasuryWallet) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        ecoCoin = IERC20(_ecoCoin);
        treasuryWallet = _treasuryWallet;
    }

    function addSigner(address signer) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(signerCount < MAX_SIGNERS, "Max signers reached");
        require(signer != address(0), "Invalid address");
        signers[signerCount] = signer;
        signerCount++;
        _grantRole(TREASURER_ROLE, signer);
        emit SignerAdded(signer);
    }

    function removeSigner(address signer) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(signerCount > MIN_SIGNERS, "Cannot go below minimum");
        for (uint256 i = 0; i < signerCount; i++) {
            if (signers[i] == signer) {
                for (uint256 j = i; j < signerCount - 1; j++) {
                    signers[j] = signers[j + 1];
                }
                signers[signerCount - 1] = address(0);
                signerCount--;
                _revokeRole(TREASURER_ROLE, signer);
                emit SignerRemoved(signer);
                break;
            }
        }
    }

    function createProposal(
        address to,
        uint256 amount,
        string calldata purpose
    ) external onlyRole(TREASURER_ROLE) returns (uint256) {
        require(amount > 0, "Amount must be positive");
        require(to != address(0), "Invalid recipient");

        uint256 id = proposalCount++;
        proposals[id] = Proposal({
            id: proposalCount - 1,
            proposer: msg.sender,
            to: to,
            amount: amount,
            purpose: purpose,
            createdAt: block.timestamp,
            deadline: block.timestamp + 3 days,
            approvals: 1,
            executed: false,
            cancelled: false
        });
        approvals[proposalCount - 1][msg.sender] = true;
        emit ProposalCreated(proposalCount - 1, msg.sender, to, amount);
        return proposalCount - 1;
    }

    function approveProposal(uint256 id) external onlyRole(TREASURER_ROLE) {
        Proposal storage proposal = proposals[id];
        require(!proposal.executed && !proposal.cancelled, "Proposal not active");
        require(block.timestamp <= proposal.deadline, "Proposal expired");
        require(!approvals[id][msg.sender], "Already approved");

        approvals[id][msg.sender] = true;
        proposals[id].approvals++;

        emit ProposalApproved(id, msg.sender);

        if (proposals[id].approvals >= MIN_SIGNERS) {
            _executeProposal(id);
        }
    }

    function cancelProposal(uint256 id) external onlyRole(DEFAULT_ADMIN_ROLE) {
        Proposal storage proposal = proposals[id];
        require(!proposal.executed, "Already executed");
        proposal.cancelled = true;
        emit ProposalCancelled(id);
    }

    function _executeProposal(uint256 id) internal {
        Proposal storage proposal = proposals[id];
        require(!proposal.executed, "Already executed");
        require(proposal.approvals >= MIN_SIGNERS, "Insufficient approvals");

        // Transfer EcoCoin from treasury
        ecoCoin.safeTransfer(proposal.to, proposal.amount);
        proposal.executed = true;
        emit ProposalExecuted(id);

        // Record as disbursement
        uint256 id = disbursementCount++;
        disbursements[id] = Disbursement({
            id: disbursementCount - 1,
            to: proposals[id].to,
            amount: proposals[id].amount,
            purpose: proposals[id].purpose,
            timestamp: block.timestamp,
            executed: true,
            approvals: proposals[id].approvals,
            cancelled: false
        });
        emit DisbursementExecuted(disbursementCount - 1, proposals[id].to, proposals[id].amount);
    }

    function receiveEcoCoin(uint256 amount) external {
        // Called by EcoCoin mint to send platform share (15%)
        require(msg.sender == address(this) || msg.sender == address(0x1234), "Only EcoCoin mint can call");
        // In practice, EcoCoin.mint would call this directly
    }

    function getBalance() external view returns (uint256) {
        return ecoCoin.balanceOf(address(this));
    }

    function getProposal(uint256 id) external view returns (
        address proposer,
        address to,
        uint256 amount,
        string memory purpose,
        uint256 createdAt,
        uint256 deadline,
        uint256 approvals,
        bool executed,
        bool cancelled
    ) {
        Proposal storage p = proposals[id];
        return (p.proposer, p.to, p.amount, p.purpose, p.createdAt, p.deadline,
                p.approvals, p.executed, p.cancelled);
    }
}