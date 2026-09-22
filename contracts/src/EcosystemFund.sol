// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title EcosystemFund
 * @notice 10% allocation for ecosystem restoration projects
 * @dev Funds allocated to verified restoration projects, transparent and auditable
 */
contract EcosystemFund is AccessControl, ReentrancyGuard {
    bytes32 public constant GRANT_MANAGER_ROLE = keccak256("GRANT_MANAGER_ROLE");
    bytes32 public constant REVIEWER_ROLE = keccak256("REVIEWER_ROLE");

    IERC20 public immutable ecoCoin;

    using SafeERC20 for IERC20;

    struct Grant {
        uint256 id;
        address recipient;
        uint256 amount;
        string projectType;      // "reforestation", "soil_restoration", "water", "biodiversity"
        string description;
        string region;
        uint256 createdAt;
        uint256 deadline;
        uint256 milestones;
        uint256 completedMilestones;
        uint256 disbursed;
        uint8 status; // 0=pending, 1=approved, 2=active, 3=completed, 4=rejected, 5=paused
        bool cancelled;
    }

    struct Milestone {
        uint256 grantId;
        uint256 index;
        string description;
        uint256 amount;
        uint256 deadline;
        bool completed;
        bool verified;
        bytes32 evidenceHash;
    }

    uint256 public grantCount;
    uint256 public totalAllocated;
    uint256 public totalDisbursed;

    mapping(uint256 => Grant) public grants;
    mapping(uint256 => Milestone[]) public milestones;
    mapping(uint256 => mapping(uint256 => bool)) public milestoneVerified;

    event GrantCreated(uint256 indexed id, address indexed recipient, uint256 amount, string projectType);
    event GrantApproved(uint256 indexed id);
    event GrantRejected(uint256 indexed id);
    event GrantPaused(uint256 indexed id);
    event GrantCompleted(uint256 indexed grantId);
    event MilestoneCreated(uint256 indexed grantId, uint256 milestoneIndex, uint256 amount);
    event MilestoneVerified(uint256 indexed grantId, uint256 milestoneIndex);
    event FundsDisbursed(uint256 indexed grantId, uint256 amount);

    constructor(address _ecoCoin) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(GRANT_MANAGER_ROLE, msg.sender);
        _grantRole(REVIEWER_ROLE, msg.sender);
        ecoCoin = IERC20(_ecoCoin);
    }

    function createGrant(
        address recipient,
        uint256 amount,
        string calldata projectType,
        string calldata description,
        string calldata region,
        uint256 deadline,
        uint256 milestonesCount
    ) external onlyRole(GRANT_MANAGER_ROLE) returns (uint256) {
        require(amount > 0, "Amount must be positive");
        require(recipient != address(0), "Invalid recipient");
        require(deadline > block.timestamp, "Deadline must be future");
        require(milestonesCount > 0, "At least one milestone required");

uint256 id = grantCount;
        grants[id] = Grant({
            id: grantCount,
            recipient: recipient,
            amount: amount,
            projectType: projectType,
            description: description,
            region: region,
            createdAt: block.timestamp,
            deadline: deadline,
            milestones: milestonesCount,
            completedMilestones: 0,
            disbursed: 0,
            status: 0, // pending
            cancelled: false
        });
        grantCount++;
        emit GrantCreated(id, recipient, amount, projectType);
        return id;
    }

    function approveGrant(uint256 grantId) external onlyRole(GRANT_MANAGER_ROLE) {
        Grant storage grant = grants[grantId];
        require(grant.status == 0, "Not pending");
        grant.status = 1; // approved
        totalAllocated += grant.amount;
        emit GrantApproved(grantId);
    }

    function rejectGrant(uint256 grantId) external onlyRole(GRANT_MANAGER_ROLE) {
        Grant storage grant = grants[grantId];
        require(grant.status == 0, "Not pending");
        grant.status = 4; // rejected
        emit GrantRejected(grantId);
    }

    function addMilestone(
        uint256 grantId,
        string calldata description,
        uint256 amount,
        uint256 deadline
    ) external onlyRole(GRANT_MANAGER_ROLE) {
        Grant storage grant = grants[grantId];
        require(grant.status == 1, "Grant not approved");
        require(milestones[grantId].length < grant.milestones, "Max milestones reached");
        require(amount > 0, "Amount must be positive");
        require(deadline > block.timestamp, "Deadline must be future");

        uint256 index = milestones[grantId].length;
        milestones[grantId].push(Milestone({
            grantId: grantId,
            index: index,
            description: description,
            amount: amount,
            deadline: deadline,
            completed: false,
            verified: false,
            evidenceHash: bytes32(0)
        }));
        emit MilestoneCreated(grantId, index, amount);
    }

    function verifyMilestone(uint256 grantId, uint256 milestoneIndex, bytes32 evidenceHash) external onlyRole(REVIEWER_ROLE) {
        Milestone storage ms = milestones[grantId][milestoneIndex];
        require(!ms.completed, "Already completed");
        require(!ms.verified, "Already verified");
        require(block.timestamp <= ms.deadline, "Deadline passed");

        ms.verified = true;
        ms.evidenceHash = evidenceHash;
        milestoneVerified[grantId][milestoneIndex] = true;
        emit MilestoneVerified(grantId, milestoneIndex);
    }

    function disburseMilestone(uint256 grantId, uint256 milestoneIndex) external onlyRole(GRANT_MANAGER_ROLE) {
        Milestone storage ms = milestones[grantId][milestoneIndex];
        Grant storage grant = grants[grantId];
        require(ms.verified, "Not verified");
        require(!ms.completed, "Already disbursed");
        require(grant.status == 1, "Grant not active");

        ms.completed = true;
        grant.disbursed += ms.amount;
        grant.completedMilestones++;
        totalDisbursed += ms.amount;

        // Transfer EcoCoin from this contract (funded by EcoTreasury 10% share)
        IERC20(ecoCoin).safeTransfer(grants[grantId].recipient, ms.amount);

        emit FundsDisbursed(grantId, ms.amount);

        if (grant.completedMilestones == grant.milestones) {
            grant.status = 3; // completed
            emit GrantCompleted(grantId);
        }
    }

    function pauseGrant(uint256 grantId) external onlyRole(GRANT_MANAGER_ROLE) {
        grants[grantId].status = 5; // paused
        emit GrantPaused(grantId);
    }

    function cancelGrant(uint256 grantId) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grants[grantId].cancelled = true;
    }

    function getGrant(uint256 grantId) external view returns (
        address recipient,
        uint256 amount,
        string memory projectType,
        string memory description,
        string memory region,
        uint256 createdAt,
        uint256 deadline,
        uint256 milestones,
        uint256 completedMilestones,
        uint256 disbursed,
        uint8 status,
        bool cancelled
    ) {
        Grant storage g = grants[grantId];
        return (g.recipient, g.amount, g.projectType, g.description, g.region,
                g.createdAt, g.deadline, g.milestones, g.completedMilestones,
                g.disbursed, g.status, g.cancelled);
    }

    function getMilestone(uint256 grantId, uint256 index) external view returns (
        string memory description,
        uint256 amount,
        uint256 deadline,
        bool completed,
        bool verified,
        bytes32 evidenceHash
    ) {
        Milestone storage ms = milestones[grantId][index];
        return (ms.description, ms.amount, ms.deadline, ms.completed, ms.verified, ms.evidenceHash);
    }

    function totalStats() external view returns (uint256 totalGrants, uint256 totalAllocated, uint256 totalDisbursed) {
        return (grantCount, totalAllocated, totalDisbursed);
    }
}