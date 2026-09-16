// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title EscrowWithDispute - escrow with the 3-stage dispute flow
 * @notice buyer -> escrow -> (shipped -> delivered | dispute:
 *         seller 48h -> marketplace 72h -> platform arbitration).
 *         Commissions are absolute wei amounts validated against the paid
 *         amount. Payouts use call{value} (no fixed-gas transfer).
 */
contract EscrowWithDispute is ReentrancyGuard, Ownable {
    enum OrderStatus { Paid, Shipped, Disputed, Delivered, Refunded }
    enum DisputeStage { None, SellerResponse, MarketplaceReview, Resolved }

    struct Order {
        address buyer;
        address seller;
        address marketplace;
        uint256 amount;
        uint256 marketplaceCommission;
        uint256 platformCommission;
        OrderStatus status;
        uint256 deliveryDeadline;
        string trackingNumber;
    }

    struct Dispute {
        uint256 orderId;
        address initiator;
        string reason;
        string evidenceURI;
        uint256 createdAt;
        DisputeStage stage;
        bool resolved;
        uint256 sellerDeadline;
        uint256 marketplaceDeadline;
    }

    uint256 public orderCounter;
    uint256 public disputeCounter;
    mapping(uint256 => Order) public orders;
    mapping(uint256 => Dispute) public disputes;
    mapping(address => uint256) public insuranceFunds;

    event OrderCreated(uint256 indexed orderId, address buyer, address seller, uint256 amount);
    event OrderShipped(uint256 indexed orderId, string trackingNumber);
    event OrderDelivered(uint256 indexed orderId);
    event DisputeOpened(uint256 indexed disputeId, uint256 indexed orderId, address initiator);
    event DisputeEscalated(uint256 indexed disputeId, DisputeStage stage);
    event DisputeResolved(uint256 indexed disputeId, bool refundedBuyer, uint256 amount);
    event InsuranceDeposited(address indexed marketplace, uint256 amount);
    event InsurancePenalty(address indexed marketplace, uint256 amount);

    uint256 public constant SELLER_RESPONSE_WINDOW = 48 hours;
    uint256 public constant MARKETPLACE_WINDOW = 72 hours;

    error PaymentRequired();
    error CommissionTooHigh();
    error OnlySeller();
    error OnlyBuyer();
    error OnlyMarketplace();
    error WrongStatus();
    error NotInStage();
    error DeadlinePassed();
    error DeadlineNotPassed();

    constructor() Ownable(msg.sender) ReentrancyGuard() {}

    function depositInsuranceFund() external payable {
        require(msg.value > 0, "no value");
        insuranceFunds[msg.sender] += msg.value;
        emit InsuranceDeposited(msg.sender, msg.value);
    }

    function createOrder(
        address seller,
        address marketplace,
        uint256 marketplaceCommission,
        uint256 platformCommission,
        uint256 deliveryDeadlineSeconds
    ) external payable returns (uint256 orderId) {
        if (msg.value == 0) revert PaymentRequired();
        if (marketplaceCommission + platformCommission >= msg.value) revert CommissionTooHigh();
        orderId = ++orderCounter;
        orders[orderId] = Order({
            buyer: msg.sender,
            seller: seller,
            marketplace: marketplace,
            amount: msg.value,
            marketplaceCommission: marketplaceCommission,
            platformCommission: platformCommission,
            status: OrderStatus.Paid,
            deliveryDeadline: block.timestamp + deliveryDeadlineSeconds,
            trackingNumber: ""
        });
        emit OrderCreated(orderId, msg.sender, seller, msg.value);
    }

    function markAsShipped(uint256 orderId, string calldata trackingNumber) external {
        Order storage o = orders[orderId];
        if (msg.sender != o.seller) revert OnlySeller();
        if (o.status != OrderStatus.Paid) revert WrongStatus();
        o.status = OrderStatus.Shipped;
        o.trackingNumber = trackingNumber;
        emit OrderShipped(orderId, trackingNumber);
    }

    function confirmDelivery(uint256 orderId) external nonReentrant {
        Order storage o = orders[orderId];
        if (msg.sender != o.buyer) revert OnlyBuyer();
        if (o.status != OrderStatus.Shipped) revert WrongStatus();
        o.status = OrderStatus.Delivered;
        _releasePayment(orderId);
        emit OrderDelivered(orderId);
    }

    function openDispute(uint256 orderId, string calldata reason, string calldata evidenceURI)
        external
        returns (uint256 disputeId)
    {
        Order storage o = orders[orderId];
        if (msg.sender != o.buyer) revert OnlyBuyer();
        if (o.status != OrderStatus.Shipped) revert WrongStatus();
        o.status = OrderStatus.Disputed;
        disputeId = ++disputeCounter;
        disputes[disputeId] = Dispute({
            orderId: orderId,
            initiator: msg.sender,
            reason: reason,
            evidenceURI: evidenceURI,
            createdAt: block.timestamp,
            stage: DisputeStage.SellerResponse,
            resolved: false,
            sellerDeadline: block.timestamp + SELLER_RESPONSE_WINDOW,
            marketplaceDeadline: block.timestamp + SELLER_RESPONSE_WINDOW + MARKETPLACE_WINDOW
        });
        emit DisputeOpened(disputeId, orderId, msg.sender);
    }

    function sellerRespondToDispute(uint256 disputeId, bool acceptRefund) external {
        Dispute storage d = disputes[disputeId];
        Order storage o = orders[d.orderId];
        if (msg.sender != o.seller) revert OnlySeller();
        if (d.stage != DisputeStage.SellerResponse) revert NotInStage();
        if (block.timestamp > d.sellerDeadline) revert DeadlinePassed();
        if (acceptRefund) {
            o.status = OrderStatus.Refunded;
            d.resolved = true;
            d.stage = DisputeStage.Resolved;
            _refundBuyer(d.orderId);
            emit DisputeResolved(disputeId, true, o.amount);
        } else {
            d.stage = DisputeStage.MarketplaceReview;
            emit DisputeEscalated(disputeId, DisputeStage.MarketplaceReview);
        }
    }

    function marketplaceResolveDispute(uint256 disputeId, bool refundToBuyer) external nonReentrant {
        Dispute storage d = disputes[disputeId];
        Order storage o = orders[d.orderId];
        if (msg.sender != o.marketplace) revert OnlyMarketplace();
        if (d.stage != DisputeStage.MarketplaceReview) revert NotInStage();
        if (block.timestamp > d.marketplaceDeadline) revert DeadlinePassed();
        d.resolved = true;
        d.stage = DisputeStage.Resolved;
        if (refundToBuyer) {
            o.status = OrderStatus.Refunded;
            _refundBuyer(d.orderId);
            _penalizeMarketplace(o.marketplace, o.marketplaceCommission);
        } else {
            o.status = OrderStatus.Delivered;
            _releasePayment(d.orderId);
        }
        emit DisputeResolved(disputeId, refundToBuyer, o.amount);
    }

    /// @notice Platform arbitration — only after the marketplace window lapsed.
    function platformArbitrate(uint256 disputeId, bool refundToBuyer) external onlyOwner nonReentrant {
        Dispute storage d = disputes[disputeId];
        Order storage o = orders[d.orderId];
        if (d.stage != DisputeStage.MarketplaceReview) revert NotInStage();
        if (block.timestamp <= d.marketplaceDeadline) revert DeadlineNotPassed();
        d.resolved = true;
        d.stage = DisputeStage.Resolved;
        if (refundToBuyer) {
            o.status = OrderStatus.Refunded;
            _refundBuyer(d.orderId);
            _penalizeMarketplace(o.marketplace, o.marketplaceCommission);
        } else {
            o.status = OrderStatus.Delivered;
            _releasePayment(d.orderId);
        }
        emit DisputeResolved(disputeId, refundToBuyer, o.amount);
    }

    function _releasePayment(uint256 orderId) internal {
        Order storage o = orders[orderId];
        uint256 sellerAmount = o.amount - o.marketplaceCommission - o.platformCommission;
        _send(payable(o.seller), sellerAmount);
        _send(payable(o.marketplace), o.marketplaceCommission);
        _send(payable(owner()), o.platformCommission);
    }

    function _refundBuyer(uint256 orderId) internal {
        Order storage o = orders[orderId];
        _send(payable(o.buyer), o.amount);
    }

    function _penalizeMarketplace(address marketplace, uint256 penalty) internal {
        if (penalty > 0 && insuranceFunds[marketplace] >= penalty) {
            insuranceFunds[marketplace] -= penalty;
            emit InsurancePenalty(marketplace, penalty);
        }
    }

    function _send(address payable to, uint256 value) internal {
        (bool ok, ) = to.call{value: value}("");
        require(ok, "eth transfer failed");
    }
}
