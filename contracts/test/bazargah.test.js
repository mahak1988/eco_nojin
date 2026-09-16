const { expect } = require("chai");
const { ethers } = require("hardhat");

const HOUR = 3600;
const AMOUNT = ethers.parseEther("1.0");
const MC = ethers.parseEther("0.03"); // marketplace commission 3%
const PC = ethers.parseEther("0.01"); // platform commission 1%

describe("Bazargah plan-v2.0 contracts", function () {
  async function deployFixture() {
    const [platform, marketplace, seller, buyer, other] = await ethers.getSigners();

    const IdentitySBT = await ethers.getContractFactory("IdentitySBT");
    const sbt = await IdentitySBT.deploy();
    await sbt.waitForDeployment();

    const Liability = await ethers.getContractFactory("MarketplaceLiability");
    const liability = await Liability.deploy();
    await liability.waitForDeployment();

    const Escrow = await ethers.getContractFactory("EscrowWithDispute");
    const escrow = await Escrow.deploy();
    await escrow.waitForDeployment();

    const BrandLicense = await ethers.getContractFactory("BrandLicense");
    const brand = await BrandLicense.deploy();
    await brand.waitForDeployment();

    const Splitter = await ethers.getContractFactory("PaymentSplitter");
    const splitter = await Splitter.deploy();
    await splitter.waitForDeployment();

    return { platform, marketplace, seller, buyer, other, sbt, liability, escrow, brand, splitter };
  }

  // --- IdentitySBT -----------------------------------------------------------
  it("SBT: platform authorizes marketplace, identity is issued and verified", async function () {
    const { platform, sbt, marketplace, seller } = await deployFixture();
    await sbt.connect(platform).authorizeMarketplace(marketplace.address, true);
    await sbt.connect(marketplace).issueIdentity(seller.address, 1, "resident");
    expect(await sbt.isMemberOfMarketplace(seller.address, 1)).to.equal(true);
  });

  it("SBT: unauthorized marketplace cannot issue", async function () {
    const { platform, sbt, marketplace, seller } = await deployFixture();
    await expect(sbt.connect(marketplace).issueIdentity(seller.address, 1, "resident"))
      .to.be.revertedWithCustomError(sbt, "NotAuthorizedMarketplace");
  });

  it("SBT: tokens are non-transferable (soulbound)", async function () {
    const { platform, sbt, marketplace, seller, buyer } = await deployFixture();
    await sbt.connect(platform).authorizeMarketplace(marketplace.address, true);
    await sbt.connect(marketplace).issueIdentity(seller.address, 1, "resident");
    const tokenId = 1;
    // The contract intentionally exposes no transferFrom/transfer functions.
    expect(sbt.interface.hasFunction("transferFrom")).to.equal(false);
    // Low-level call to the ERC-721 transferFrom selector must revert.
    const from = seller.address.slice(2).toLowerCase().padStart(64, "0");
    const to = buyer.address.slice(2).toLowerCase().padStart(64, "0");
    const id = tokenId.toString(16).padStart(64, "0");
    const data = "0x23b872dd" + from + to + id; // transferFrom(address,address,uint256)
    await expect(seller.sendTransaction({ to: await sbt.getAddress(), data })).to.be.reverted;
  });

  it("SBT: revocation removes membership", async function () {
    const { platform, sbt, marketplace, seller } = await deployFixture();
    await sbt.connect(platform).authorizeMarketplace(marketplace.address, true);
    await sbt.connect(marketplace).issueIdentity(seller.address, 1, "tribal_member");
    await sbt.connect(marketplace).revokeIdentity(1);
    expect(await sbt.isMemberOfMarketplace(seller.address, 1)).to.equal(false);
  });

  // --- EscrowWithDispute ------------------------------------------------------
  async function paidOrderFixture() {
    const base = await deployFixture();
    const tx = await base.escrow.connect(base.buyer).createOrder(
      base.seller.address, base.marketplace.address, MC, PC, 7 * 24 * HOUR,
      { value: AMOUNT }
    );
    const receipt = await tx.wait();
    const ev = receipt.logs.map((l) => { try { return base.escrow.interface.parseLog(l); } catch { return null; } })
      .filter(Boolean).find((p) => p.name === "OrderCreated");
    base.orderId = ev.args.orderId;
    await base.escrow.connect(base.seller).markAsShipped(base.orderId, "TRACK-123");
    return base;
  }

  it("Escrow: reject commission >= amount", async function () {
    const { escrow, seller, marketplace, buyer } = await deployFixture();
    const bad = AMOUNT; // commission equals amount
    await expect(escrow.connect(buyer).createOrder(seller.address, marketplace.address, bad, 0, 24 * HOUR, { value: AMOUNT }))
      .to.be.revertedWithCustomError(escrow, "CommissionTooHigh");
  });

  it("Escrow: delivery releases seller/marketplace/platform split", async function () {
    const { escrow, seller, marketplace, platform, buyer, orderId } = await paidOrderFixture();
    const sellerAmt = AMOUNT - MC - PC;
    await expect(escrow.connect(buyer).confirmDelivery(orderId))
      .to.changeEtherBalances(
        [buyer, seller, marketplace, platform],
        [0n, sellerAmt, MC, PC]
      );
  });

  it("Escrow: seller accepts refund -> buyer fully refunded", async function () {
    const { escrow, seller, buyer, orderId } = await paidOrderFixture();
    const dId = await escrow.connect(buyer).openDispute.staticCall(orderId, "bad quality", "ipfs://evidence");
    await escrow.connect(buyer).openDispute(orderId, "bad quality", "ipfs://evidence");
    await expect(escrow.connect(seller).sellerRespondToDispute(dId, true))
      .to.changeEtherBalances([buyer, seller], [AMOUNT, 0n]);
    const d = await escrow.disputes(dId);
    expect(d.resolved).to.equal(true);
  });

  it("Escrow: marketplace resolves in favor of buyer + insurance penalty", async function () {
    const { escrow, seller, marketplace, buyer, orderId } = await paidOrderFixture();
    await escrow.connect(marketplace).depositInsuranceFund({ value: ethers.parseEther("0.5") });
    const dId = await escrow.connect(buyer).openDispute.staticCall(orderId, "damaged", "ipfs://x");
    await escrow.connect(buyer).openDispute(orderId, "damaged", "ipfs://x");
    await escrow.connect(seller).sellerRespondToDispute(dId, false); // escalate
    await expect(escrow.connect(marketplace).marketplaceResolveDispute(dId, true))
      .to.changeEtherBalances([buyer], [AMOUNT]);
    expect(await escrow.insuranceFunds(marketplace.address))
      .to.equal(ethers.parseEther("0.5") - MC);
  });

  it("Escrow: marketplace cannot act after deadline; platform arbitrates", async function () {
    const { escrow, seller, marketplace, buyer, orderId } = await paidOrderFixture();
    const dId = await escrow.connect(buyer).openDispute.staticCall(orderId, "never answered", "ipfs://y");
    await escrow.connect(buyer).openDispute(orderId, "never answered", "ipfs://y");
    await escrow.connect(seller).sellerRespondToDispute(dId, false);
    // jump past seller(48h) + marketplace(72h) windows
    await ethers.provider.send("evm_increaseTime", [121 * HOUR]);
    await ethers.provider.send("evm_mine");
    await expect(escrow.connect(marketplace).marketplaceResolveDispute(dId, true))
      .to.be.revertedWithCustomError(escrow, "DeadlinePassed");
    await expect(escrow.connect(buyer).platformArbitrate(dId, true)).to.be.reverted; // only owner
    await escrow.platformArbitrate(dId, true); // platform = owner
    const o = await escrow.orders(orderId);
    expect(o.status).to.equal(4n); // Refunded
  });

  it("Escrow: only buyer can open dispute", async function () {
    const { escrow, other, orderId } = await paidOrderFixture();
    await expect(escrow.connect(other).openDispute(orderId, "x", "ipfs://z"))
      .to.be.revertedWithCustomError(escrow, "OnlyBuyer");
  });

  // --- MarketplaceLiability ---------------------------------------------------
  it("Liability: register requires minimum insurance fund", async function () {
    const { liability, marketplace } = await deployFixture();
    await expect(liability.connect(marketplace).registerMarketplace(marketplace.address, { value: ethers.parseEther("0.05") }))
      .to.be.revertedWithCustomError(liability, "InsufficientFund");
    await liability.connect(marketplace).registerMarketplace(marketplace.address, { value: ethers.parseEther("0.1") });
    const acc = await liability.accounts(marketplace.address);
    expect(acc.accountabilityScore).to.equal(100n);
    expect(acc.active).to.equal(true);
  });

  it("Liability: platform pays buyer from insurance fund and updates score", async function () {
    const { liability, marketplace, buyer, platform } = await deployFixture();
    await liability.connect(marketplace).registerMarketplace(marketplace.address, { value: ethers.parseEther("0.2") });
    await expect(liability.connect(platform).useInsuranceFund(marketplace.address, buyer.address, ethers.parseEther("0.1"), 1))
      .to.changeEtherBalances([buyer], [ethers.parseEther("0.1")]);
    await liability.connect(platform).recordDisputeHandling(marketplace.address, true);
    await liability.connect(platform).updateAccountabilityScore(marketplace.address, 90);
    const acc = await liability.accounts(marketplace.address);
    expect(acc.totalResolved).to.equal(1n);
    expect(acc.accountabilityScore).to.equal(90n);
  });

  it("Liability: suspended marketplace cannot use fund", async function () {
    const { liability, marketplace, buyer, platform } = await deployFixture();
    await liability.connect(marketplace).registerMarketplace(marketplace.address, { value: ethers.parseEther("0.2") });
    await liability.connect(platform).suspendMarketplace(marketplace.address, "repeated unresolved disputes");
    await expect(liability.connect(platform).useInsuranceFund(marketplace.address, buyer.address, 1, 2))
      .to.be.revertedWithCustomError(liability, "Inactive");
  });

  // --- BrandLicense -----------------------------------------------------------
  it("BrandLicense: issue -> valid -> revoke -> invalid", async function () {
    const { brand, platform, seller } = await deployFixture();
    await brand.connect(platform).issueLicense(seller.address, 1, "ipfs://terms", 365);
    expect(await brand.isValid(1)).to.equal(true);
    await brand.connect(platform).revokeLicense(1);
    expect(await brand.isValid(1)).to.equal(false);
  });

  it("BrandLicense: only platform issues", async function () {
    const { brand, seller } = await deployFixture();
    await expect(brand.connect(seller).issueLicense(seller.address, 1, "ipfs://x", 30))
      .to.be.revertedWithCustomError(brand, "OwnableUnauthorizedAccount");
  });

  // --- PaymentSplitter --------------------------------------------------------
  it("Splitter: proportional release (96/3/1)", async function () {
    const { splitter, seller, marketplace, platform } = await deployFixture();
    await splitter.addPayee(seller.address, 96);
    await splitter.addPayee(marketplace.address, 3);
    await splitter.addPayee(platform.address, 1);
    await marketplace.sendTransaction({ to: await splitter.getAddress(), value: ethers.parseEther("1.0") });
    await expect(splitter.connect(seller).release())
      .to.changeEtherBalances([seller], [ethers.parseEther("0.96")]);
    await expect(splitter.connect(marketplace).release())
      .to.changeEtherBalances([marketplace], [ethers.parseEther("0.03")]);
    await expect(splitter.connect(platform).release())
      .to.changeEtherBalances([platform], [ethers.parseEther("0.01")]);
  });

  it("Splitter: non-payee cannot release", async function () {
    const { splitter, other, seller } = await deployFixture();
    await splitter.addPayee(seller.address, 100);
    await expect(splitter.connect(other).release()).to.be.revertedWithCustomError(splitter, "ZeroShares");
  });
});
