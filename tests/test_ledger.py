"""
TraceRx AI - Blockchain Consensus & Immutability Test Suite
Validates Merkle tree proofs, batch lifecycle states, hash chaining,
and anti-counterfeit duplicate QR reuse interception traps.
"""

import pytest
from backend.blockchain_ledger import (
    CryptographicLedger,
    BatchStatus,
    MerkleTree,
    sha256,
    generate_address,
    generate_signature
)


def test_genesis_block_creation():
    ledger = CryptographicLedger()
    assert len(ledger.chain) >= 1
    genesis = ledger.chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash.startswith("0x0000")
    assert genesis.hash.startswith("0x")
    assert genesis.merkle_root.startswith("0x")


def test_mint_batch_lifecycle():
    ledger = CryptographicLedger()
    batch = ledger.mint_batch(
        drug_name="Remdesivir 100mg",
        serial_number="SN-TEST-9999",
        mfg_date="2026-01-01",
        exp_date="2028-01-01",
        lab_signature="0xabcdef1234567890",
        batch_id="TEST-BATCH-01",
        manufacturer_name="Pfizer BioTech"
    )

    assert batch.batch_id == "TEST-BATCH-01"
    assert batch.status == BatchStatus.MANUFACTURED
    assert len(batch.custody_chain) == 1
    assert batch.custody_chain[0].entity == "Pfizer BioTech"
    assert batch.tx_hash.startswith("0x")
    assert len(ledger.chain) == 2  # Genesis + Mint


def test_custody_transfer_immutability():
    ledger = CryptographicLedger()
    batch = ledger.mint_batch(
        drug_name="Paxlovid 150mg",
        serial_number="SN-PAX-001",
        mfg_date="2026-02-01",
        exp_date="2028-02-01",
        lab_signature="0x9988776655443322",
        batch_id="PAX-001",
        manufacturer_name="Pfizer Labs"
    )

    checkpoint = ledger.transfer_custody(
        batch_id="PAX-001",
        from_entity="Pfizer Labs",
        to_entity="DHL Express Logistics",
        priv_key="secret_key_1",
        location="Brussels Airport Cargo Hub, Belgium",
        new_status=BatchStatus.IN_TRANSIT,
        notes="Cryo-monitored shipment verified."
    )

    assert len(batch.custody_chain) == 2
    assert batch.status == BatchStatus.IN_TRANSIT
    assert checkpoint.entity == "DHL Express Logistics"
    assert checkpoint.location == "Brussels Airport Cargo Hub, Belgium"
    assert checkpoint.signature.startswith("0x")


def test_duplicate_qr_reuse_interception():
    """
    CRITICAL: Validates that once a batch is DISPENSED at point-of-care,
    any subsequent dispensation attempt triggers DUPLICATE_QR_REUSE_ATTEMPT
    with the exact timestamp and location of the original dispensation.
    """
    ledger = CryptographicLedger()
    batch_id = "AMOX-REUSE-TEST"
    ledger.mint_batch(
        drug_name="Amoxicillin 500mg",
        serial_number="SN-AMOX-888",
        mfg_date="2026-01-15",
        exp_date="2027-06-15",
        lab_signature="0x12344321",
        batch_id=batch_id,
        manufacturer_name="GSK Pharmaceuticals"
    )

    # First dispensation (Legitimate point-of-care)
    dispense_1 = ledger.verify_and_dispense(
        batch_id=batch_id,
        scanner_metadata={
            "scanner_id": "DHAKA-DISPENSARY-01",
            "location": "Square Hospital, Dhaka, Bangladesh",
            "operator": "Dr. Farhan Ahmed"
        }
    )

    assert dispense_1["success"] is True
    assert dispense_1["alert"] == "PROVENANCE_VERIFIED_AUTHENTIC"
    assert ledger.batches[batch_id].status == BatchStatus.DISPENSED

    # Second dispensation attempt (Counterfeit cloned QR reuse!)
    dispense_2 = ledger.verify_and_dispense(
        batch_id=batch_id,
        scanner_metadata={
            "scanner_id": "LONDON-CLINIC-99",
            "location": "St. Thomas Hospital, London, UK",
            "operator": "Dr. Sarah Lin"
        }
    )

    assert dispense_2["success"] is False
    assert dispense_2["alert"] == "DUPLICATE_QR_REUSE_ATTEMPT"
    assert "Square Hospital, Dhaka" in dispense_2["message"]
    assert dispense_2["first_dispensed_location"] == "Square Hospital, Dhaka, Bangladesh"
    assert dispense_2["action"] == "TRIGGER_COUNTERFEIT_INTERCEPTION_ALARM"


def test_merkle_tree_proof_verification():
    leaves = [
        sha256("RECORD_LEAF_1"),
        sha256("RECORD_LEAF_2"),
        sha256("RECORD_LEAF_3"),
        sha256("RECORD_LEAF_4")
    ]
    tree = MerkleTree(leaves)
    assert tree.root.startswith("0x")

    for i in range(len(leaves)):
        proof = tree.get_proof(i)
        is_valid = MerkleTree.verify_proof(leaves[i], proof, tree.root)
        assert is_valid is True


def test_chain_integrity():
    ledger = CryptographicLedger()
    ledger.mint_batch("Drug A", "SN-A", "2026-01-01", "2027-01-01", "0x11", "B-A")
    ledger.mint_batch("Drug B", "SN-B", "2026-01-01", "2027-01-01", "0x22", "B-B")

    valid, msg = ledger.verify_chain_integrity()
    assert valid is True

    # Tamper test
    ledger.chain[1].hash = "0xBAD_TAMPERED_HASH"
    tampered_valid, tampered_msg = ledger.verify_chain_integrity()
    assert tampered_valid is False
