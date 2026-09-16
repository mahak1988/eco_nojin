const { expect } = require("chai");
const { ethers } = require("hardhat");

const ONE = ethers.parseEther("1.0");
const TWO = ethers.parseEther("2.0");

describe("CarbonCredit", function () {
  async function deployFixture() {
    const [admin, minter, verifier, pauser, projectOwner, holder, receiver, other] =
      await ethers.getSigners();
    const CarbonCredit = await ethers.getContractFactory("CarbonCredit");
    const carbon = await CarbonCredit.deploy();
    await carbon.waitForDeployment();

    await carbon.grantRole(await carbon.MINTER_ROLE(), minter.address);
    await carbon.grantRole(await carbon.VERIFIER_ROLE(), verifier.address);
    await carbon.grantRole(await carbon.PAUSER_ROLE(), pauser.address);

    return {
      admin,
      minter,
      verifier,
      pauser,
      projectOwner,
      holder,
      receiver,
      other,
      carbon
    };
  }

  async function registerVerifiedProject(fixture, projectId) {
    const { carbon, minter, verifier, projectOwner } = fixture;
    await carbon
      .connect(minter)
      .registerProject(
        projectId,
        "afforestation",
        "test-location",
        `ipfs://${projectId}/metadata`
      );
    const numericProjectId = await carbon.projectIdToNumber(projectId);
    await carbon.connect(verifier).verifyProject(numericProjectId);
    return numericProjectId;
  }

  it("exposes roles, chain id, contract address, and metadata URI", async function () {
    const { admin, minter, verifier, pauser, carbon } = await deployFixture();
    const address = await carbon.getAddress();
    const network = await ethers.provider.getNetwork();

    expect(await carbon.ADMIN_ROLE()).to.equal(await carbon.DEFAULT_ADMIN_ROLE());
    expect(await carbon.hasRole(await carbon.ADMIN_ROLE(), admin.address)).to.equal(true);
    expect(await carbon.hasRole(await carbon.MINTER_ROLE(), minter.address)).to.equal(true);
    expect(await carbon.hasRole(await carbon.VERIFIER_ROLE(), verifier.address)).to.equal(true);
    expect(await carbon.hasRole(await carbon.PAUSER_ROLE(), pauser.address)).to.equal(true);
    expect(await carbon.chainId()).to.equal(network.chainId);
    expect(await carbon.getChainId()).to.equal(network.chainId);
    expect(await carbon.contractAddress()).to.equal(address);
    expect(await carbon.getContractAddress()).to.equal(address);

    await carbon.connect(admin).setMetadataURI("ipfs://contract-metadata");
    expect(await carbon.metadataURI()).to.equal("ipfs://contract-metadata");
  });

  it("registers and validates a project before issuance", async function () {
    const { carbon, minter, verifier, holder, other } = await deployFixture();
    await carbon
      .connect(minter)
      .registerProject("project-1", "soil", "location", "ipfs://project-1");
    const projectId = await carbon.projectIdToNumber("project-1");
    const project = await carbon.projects(projectId);

    expect(project.id).to.equal(1n);
    expect(project.projectId).to.equal("project-1");
    expect(project.owner).to.equal(minter.address);
    expect(project.verified).to.equal(false);
    expect(project.metadataURI).to.equal("ipfs://project-1");
    expect(await carbon.projectMetadataURI(projectId)).to.equal("ipfs://project-1");

    await expect(
      carbon
        .connect(minter)
        ["mint(uint256,bytes32,address,uint256)"](
          projectId,
          ethers.id("issuance-before-verification"),
          holder.address,
          ONE
        )
    ).to.be.revertedWithCustomError(carbon, "ProjectNotVerified");

    await carbon.connect(verifier).validateProject(projectId);
    await expect(
      carbon.connect(verifier).validateProject(projectId)
    ).to.be.revertedWithCustomError(carbon, "ProjectAlreadyVerified");
    await expect(
      carbon
        .connect(minter)
        .registerProject("project-1", "soil", "location", "ipfs://duplicate")
    ).to.be.revertedWithCustomError(carbon, "ProjectAlreadyExists");
    await expect(
      carbon
        .connect(other)
        .registerProject("project-2", "soil", "location", "ipfs://project-2")
    ).to.be.revertedWithCustomError(carbon, "AccessControlUnauthorizedAccount");
  });

  it("rejects duplicate issuance IDs and records issuance accounting", async function () {
    const { carbon, minter, verifier, holder } = await deployFixture();
    const projectId = await registerVerifiedProject({ carbon, minter, verifier, holder }, "project-2");
    const issuanceId = ethers.id("issuance-2");

    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, ONE);

    const issuance = await carbon.issuances(issuanceId);
    expect(issuance.id).to.equal(issuanceId);
    expect(issuance.projectId).to.equal(projectId);
    expect(issuance.recipient).to.equal(holder.address);
    expect(issuance.amount).to.equal(ONE);
    expect(issuance.retiredAmount).to.equal(0n);
    expect(issuance.exists).to.equal(true);
    expect(await carbon.issuanceUsed(issuanceId)).to.equal(true);
    expect(await carbon.totalCreditsIssued()).to.equal(ONE);

    await expect(
      carbon
        .connect(minter)
        ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, ONE)
    ).to.be.revertedWithCustomError(carbon, "IssuanceAlreadyUsed");
  });

  it("retires by issuance ID and prevents double counting", async function () {
    const { carbon, minter, verifier, holder, other } = await deployFixture();
    await carbon
      .connect(minter)
      .registerProject("project-3", "biochar", "location", "ipfs://project-3");
    const projectId = await carbon.projectIdToNumber("project-3");
    await carbon.connect(verifier).verifyProject(projectId);
    const issuanceId = ethers.id("issuance-3");
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, TWO);

    await carbon
      .connect(holder)
      ["retire(bytes32,uint256,string)"](issuanceId, ONE, "offset");
    const issuance = await carbon.issuances(issuanceId);
    const project = await carbon.projects(projectId);
    expect(issuance.retiredAmount).to.equal(ONE);
    expect(project.totalCreditsRetired).to.equal(ONE);
    expect(await carbon.totalRetiredCredits()).to.equal(ONE);
    expect(await carbon.balanceOf(holder.address)).to.equal(ONE);

    await expect(
      carbon
        .connect(holder)
        ["retire(bytes32,uint256,string)"](issuanceId, TWO, "offset again")
    ).to.be.revertedWithCustomError(carbon, "RetirementAmountExceeded");
    await expect(
      carbon
        .connect(other)
        ["retire(bytes32,uint256,string)"](issuanceId, ONE, "no balance")
    ).to.be.revertedWithCustomError(carbon, "InvalidAmount");
  });

  it("keeps retirement attribution isolated after transfers", async function () {
    const { carbon, minter, verifier, holder, receiver, other } = await deployFixture();
    await carbon
      .connect(minter)
      .registerProject("project-8", "mixed", "location", "ipfs://project-8");
    const projectId = await carbon.projectIdToNumber("project-8");
    await carbon.connect(verifier).verifyProject(projectId);
    const firstIssuanceId = ethers.id("issuance-8a");
    const secondIssuanceId = ethers.id("issuance-8b");
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, firstIssuanceId, holder.address, ONE);
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, secondIssuanceId, other.address, ONE);
    await carbon.connect(other).transfer(receiver.address, ONE);

    expect(await carbon.issuanceBalanceOf(secondIssuanceId, receiver.address)).to.equal(ONE);
    await expect(
      carbon
        .connect(receiver)
        ["retire(bytes32,uint256,string)"](firstIssuanceId, ONE, "wrong lot")
    ).to.be.revertedWithCustomError(carbon, "InvalidAmount");
    await carbon
      .connect(holder)
      ["retire(bytes32,uint256,string)"](firstIssuanceId, ONE, "correct lot");
    expect((await carbon.issuances(firstIssuanceId)).retiredAmount).to.equal(ONE);
  });

  it("records explicit retirement IDs and rejects replay", async function () {
    const { carbon, minter, verifier, holder } = await deployFixture();
    const projectId = await registerVerifiedProject({ carbon, minter, verifier, holder }, "project-4");
    const issuanceId = ethers.id("issuance-4");
    const retirementId = ethers.id("retirement-4");
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, ONE);

    await carbon
      .connect(holder)
      ["retire(bytes32,bytes32,uint256,string)"](
        retirementId,
        issuanceId,
        ONE,
        "retired once"
      );
    expect((await carbon.retirements(retirementId)).exists).to.equal(true);
    expect(await carbon.retirementUsed(retirementId)).to.equal(true);
    await expect(
      carbon
        .connect(holder)
        ["retire(bytes32,bytes32,uint256,string)"](
          retirementId,
          issuanceId,
          ONE,
          "replay"
        )
    ).to.be.revertedWithCustomError(carbon, "RetirementAlreadyUsed");
  });

  it("freezes and unfreezes actors with authority and reason", async function () {
    const { carbon, admin, minter, verifier, holder, receiver } = await deployFixture();
    const projectId = await registerVerifiedProject({ carbon, minter, verifier, holder }, "project-5");
    const issuanceId = ethers.id("issuance-5");
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, ONE);

    await carbon.connect(admin).freezeAccount(holder.address, "compliance review");
    expect(await carbon.frozenAccounts(holder.address)).to.equal(true);
    const freeze = await carbon.freezeRecords(holder.address);
    expect(freeze.frozen).to.equal(true);
    expect(freeze.actor).to.equal(holder.address);
    expect(freeze.authority).to.equal(admin.address);
    expect(freeze.reason).to.equal("compliance review");

    await expect(
      carbon.connect(holder).transfer(receiver.address, ONE)
    ).to.be.revertedWithCustomError(carbon, "FrozenAccount");
    await expect(
      carbon.connect(receiver).transfer(holder.address, ONE)
    ).to.be.revertedWithCustomError(carbon, "FrozenAccount");

    await carbon.connect(admin).unfreezeAccount(holder.address, "review complete");
    expect(await carbon.frozenAccounts(holder.address)).to.equal(false);
    await carbon.connect(holder).transfer(receiver.address, ONE);
    expect(await carbon.balanceOf(receiver.address)).to.equal(ONE);
  });

  it("pauses and unpauses all token movement", async function () {
    const { carbon, minter, verifier, pauser, holder, receiver } = await deployFixture();
    const projectId = await registerVerifiedProject({ carbon, minter, verifier, holder }, "project-6");
    const issuanceId = ethers.id("issuance-6");
    await carbon
      .connect(minter)
      ["mint(uint256,bytes32,address,uint256)"](projectId, issuanceId, holder.address, ONE);

    await carbon.connect(pauser).pause();
    expect(await carbon.paused()).to.equal(true);
    await expect(
      carbon.connect(holder).transfer(receiver.address, ONE)
    ).to.be.revertedWithCustomError(carbon, "EnforcedPause");
    await expect(
      carbon
        .connect(minter)
        ["mint(uint256,bytes32,address,uint256)"](
          projectId,
          ethers.id("issuance-paused"),
          receiver.address,
          ONE
        )
    ).to.be.revertedWithCustomError(carbon, "EnforcedPause");

    await carbon.connect(pauser).unpause();
    await carbon.connect(holder).transfer(receiver.address, ONE);
    expect(await carbon.balanceOf(receiver.address)).to.equal(ONE);
  });

  it("supports string issuance IDs and project-scoped retirement", async function () {
    const { carbon, minter, verifier, holder } = await deployFixture();
    await carbon
      .connect(minter)
      .registerProject("project-7", "renewable", "location", "ipfs://project-7");
    const projectId = await carbon.projectIdToNumber("project-7");
    await carbon.connect(verifier).verifyProject(projectId);

    await carbon
      .connect(minter)
      ["mint(uint256,string,address,uint256)"](
        projectId,
        "issuance-string-7",
        holder.address,
        ONE
      );
    await carbon
      .connect(holder)
      ["retire(uint256,uint256,string)"](projectId, ONE, "project retirement");
    const project = await carbon.projects(projectId);
    expect(project.totalCreditsRetired).to.equal(ONE);
    expect(await carbon.totalRetiredCredits()).to.equal(ONE);
  });
});
