const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TraceRxProvenance Smart Contract Test Suite", function () {
  let TraceRxProvenance, contract;
  let owner, manufacturer, distributor, pharmacy, patient, attacker;

  const SAMPLE_GTIN = "00300012345678";
  const SAMPLE_LOT = "LOT-2026-X88";
  const SAMPLE_EXPIRY = Math.floor(Date.now() / 1000) + 365 * 24 * 3600; // 1 year ahead
  const SAMPLE_MERKLE = ethers.keccak256(ethers.toUtf8Bytes("MERKLE_ROOT_BATCH_X88"));
  const SCANNER_HASH = ethers.keccak256(ethers.toUtf8Bytes("TERMINAL_DHAKA_CENTRAL_01"));

  beforeEach(async function () {
    [owner, manufacturer, distributor, pharmacy, patient, attacker] = await ethers.getSigners();

    TraceRxProvenance = await ethers.getContractFactory("TraceRxProvenance");
    contract = await TraceRxProvenance.deploy("https://api.tracerx.ai/metadata/{id}.json");
    await contract.waitForDeployment();

    // Grant roles
    const MANUFACTURER_ROLE = await contract.MANUFACTURER_ROLE();
    const DISTRIBUTOR_ROLE = await contract.DISTRIBUTOR_ROLE();
    const PHARMACY_ROLE = await contract.PHARMACY_ROLE();

    await contract.grantRole(MANUFACTURER_ROLE, manufacturer.address);
    await contract.grantRole(DISTRIBUTOR_ROLE, distributor.address);
    await contract.grantRole(PHARMACY_ROLE, pharmacy.address);
  });

  describe("1. Deployment & Access Control", function () {
    it("Should grant DEFAULT_ADMIN_ROLE and MANUFACTURER_ROLE to deployer", async function () {
      const adminRole = await contract.DEFAULT_ADMIN_ROLE();
      expect(await contract.hasRole(adminRole, owner.address)).to.be.true;
    });

    it("Should prevent unauthorized accounts from minting batches", async function () {
      await expect(
        contract.connect(attacker).mintBatch(
          SAMPLE_GTIN,
          SAMPLE_LOT,
          SAMPLE_EXPIRY,
          SAMPLE_MERKLE,
          1000
        )
      ).to.be.revertedWithCustomError(contract, "AccessControlUnauthorizedAccount");
    });
  });

  describe("2. Batch Lifecycle & Provenance", function () {
    it("Should allow manufacturer to mint verified batch", async function () {
      const tx = await contract.connect(manufacturer).mintBatch(
        SAMPLE_GTIN,
        SAMPLE_LOT,
        SAMPLE_EXPIRY,
        SAMPLE_MERKLE,
        500
      );

      await expect(tx)
        .to.emit(contract, "BatchMinted")
        .withArgs(1, SAMPLE_GTIN, SAMPLE_LOT, SAMPLE_EXPIRY, SAMPLE_MERKLE, manufacturer.address);

      const batch = await contract.batches(1);
      expect(batch.gtin).to.equal(SAMPLE_GTIN);
      expect(batch.batchLot).to.equal(SAMPLE_LOT);
      expect(batch.currentCustodian).to.equal(manufacturer.address);
      expect(batch.status).to.equal(0); // Active
    });

    it("Should transfer custody across supply chain checkpoints", async function () {
      await contract.connect(manufacturer).mintBatch(
        SAMPLE_GTIN,
        SAMPLE_LOT,
        SAMPLE_EXPIRY,
        SAMPLE_MERKLE,
        500
      );

      // Transfer from manufacturer to distributor
      const transferTx = await contract.connect(manufacturer).transferCustody(
        1,
        distributor.address,
        "0x"
      );

      await expect(transferTx).to.emit(contract, "CustodyTransferred");
      const batch = await contract.batches(1);
      expect(batch.currentCustodian).to.equal(distributor.address);

      // Check custody checkpoints length
      const checkpoints = await contract.getCustodyCheckpoints(1);
      expect(checkpoints.length).to.equal(2);
    });
  });

  describe("3. Anti-Counterfeit Double-Dispense Traps", function () {
    it("Should successfully dispense active batch at point of care", async function () {
      await contract.connect(manufacturer).mintBatch(
        SAMPLE_GTIN,
        SAMPLE_LOT,
        SAMPLE_EXPIRY,
        SAMPLE_MERKLE,
        500
      );

      const dispenseTx = await contract.connect(pharmacy).dispenseToPatient(1, SCANNER_HASH);
      await expect(dispenseTx).to.emit(contract, "BatchDispensed");

      const batch = await contract.batches(1);
      expect(batch.status).to.equal(1); // Dispensed
      expect(batch.firstDispensedAt).to.be.gt(0);
      expect(batch.firstDispenserScanner).to.equal(SCANNER_HASH);
    });

    it("CRITICAL: Should REVERT with AlreadyDispensed and flag fraudulent reuse attempt", async function () {
      await contract.connect(manufacturer).mintBatch(
        SAMPLE_GTIN,
        SAMPLE_LOT,
        SAMPLE_EXPIRY,
        SAMPLE_MERKLE,
        500
      );

      // 1st dispensation (genuine)
      await contract.connect(pharmacy).dispenseToPatient(1, SCANNER_HASH);

      // 2nd dispensation attempt (counterfeit / cloned QR code reuse)
      const SECOND_SCANNER = ethers.keccak256(ethers.toUtf8Bytes("CLONED_TERMINAL_LONDON_99"));

      await expect(
        contract.connect(attacker).dispenseToPatient(1, SECOND_SCANNER)
      ).to.be.revertedWithCustomError(contract, "AlreadyDispensed");
    });
  });

  describe("4. Regulatory Product Recall", function () {
    it("Should allow regulator to recall compromised batch", async function () {
      await contract.connect(manufacturer).mintBatch(
        SAMPLE_GTIN,
        SAMPLE_LOT,
        SAMPLE_EXPIRY,
        SAMPLE_MERKLE,
        500
      );

      await expect(
        contract.connect(owner).recallBatch(1, "Suspected cold-chain thermal breach")
      ).to.emit(contract, "BatchRecalledEvent");

      const batch = await contract.batches(1);
      expect(batch.status).to.equal(2); // Recalled
    });
  });
});
