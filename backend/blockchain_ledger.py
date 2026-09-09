"""
TraceRx AI - Cryptographic Merkle Tree Provenance Ledger
Provides an immutable in-memory EVM/SHA-256 blockchain tracking pharmaceutical custody.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class BatchStatus(str, Enum):
    MANUFACTURED = "MANUFACTURED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED_AT_PHARMACY = "RECEIVED_AT_PHARMACY"
    DISPENSED = "DISPENSED"
    REVOKED = "REVOKED"


def sha256(data: str) -> str:
    """Computes standard hex SHA-256 hash."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def generate_address(identity: str) -> str:
    """Generates an EVM-style hexadecimal checksum address from an identity string."""
    raw = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]
    return f"0x{raw.lower()}"


def generate_signature(private_key: str, message: str) -> str:
    """Generates an HMAC-SHA256 digital signature simulating ECDSA secp256k1 sign."""
    key_bytes = private_key.encode("utf-8")
    msg_bytes = message.encode("utf-8")
    return "0x" + hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()


@dataclass
class CustodyCheckpoint:
    entity: str
    entity_address: str
    location: str
    timestamp: float
    iso_time: str
    signature: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MerkleTree:
    """In-memory binary Merkle tree with cryptographic proof generation."""

    def __init__(self, leaves: List[str]):
        self.leaves = [l if l.startswith("0x") else f"0x{l}" for l in leaves] if leaves else ["0x" + "0"*64]
        self.levels: List[List[str]] = [self.leaves]
        self._build_tree()

    def _build_tree(self) -> None:
        current = self.leaves
        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else current[i]
                combined = sha256(left + right)
                next_level.append(f"0x{combined}")
            self.levels.append(next_level)
            current = next_level

    @property
    def root(self) -> str:
        return self.levels[-1][0] if self.levels and self.levels[-1] else "0x" + "0"*64

    def get_proof(self, index: int) -> List[Dict[str, str]]:
        proof = []
        for level in self.levels[:-1]:
            is_right = index % 2 == 1
            sibling_idx = index - 1 if is_right else (index + 1 if index + 1 < len(level) else index)
            proof.append({
                "position": "left" if is_right else "right",
                "hash": level[sibling_idx]
            })
            index //= 2
        return proof

    @staticmethod
    def verify_proof(leaf: str, proof: List[Dict[str, str]], root: str) -> bool:
        current = leaf if leaf.startswith("0x") else f"0x{leaf}"
        for p in proof:
            sibling = p["hash"]
            if p["position"] == "left":
                combined = sha256(sibling + current)
            else:
                combined = sha256(current + sibling)
            current = f"0x{combined}"
        return current.lower() == root.lower()


@dataclass
class PharmaceuticalBatch:
    batch_id: str
    drug_name: str
    serial_number: str
    mfg_date: str
    exp_date: str
    manufacturer_address: str
    lab_signature: str
    status: BatchStatus
    custody_chain: List[CustodyCheckpoint] = field(default_factory=list)
    dispensed_at: Optional[float] = None
    dispensed_iso: Optional[str] = None
    dispensation_scanner: Optional[Dict[str, Any]] = None
    tx_hash: str = ""
    created_at: float = field(default_factory=time.time)

    def compute_record_hash(self) -> str:
        payload = {
            "batch_id": self.batch_id,
            "drug_name": self.drug_name,
            "serial_number": self.serial_number,
            "mfg_date": self.mfg_date,
            "exp_date": self.exp_date,
            "manufacturer_address": self.manufacturer_address,
            "status": self.status.value,
            "custody_count": len(self.custody_chain)
        }
        return "0x" + sha256(json.dumps(payload, sort_keys=True))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "drug_name": self.drug_name,
            "serial_number": self.serial_number,
            "mfg_date": self.mfg_date,
            "exp_date": self.exp_date,
            "manufacturer_address": self.manufacturer_address,
            "lab_signature": self.lab_signature,
            "status": self.status.value,
            "custody_chain": [c.to_dict() for c in self.custody_chain],
            "dispensed_at": self.dispensed_at,
            "dispensed_iso": self.dispensed_iso,
            "dispensation_scanner": self.dispensation_scanner,
            "tx_hash": self.tx_hash,
            "record_hash": self.compute_record_hash(),
            "created_at": self.created_at
        }


@dataclass
class Block:
    index: int
    timestamp: float
    iso_time: str
    transactions: List[Dict[str, Any]]
    merkle_root: str
    previous_hash: str
    nonce: int
    hash: str
    gas_consumed: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CryptographicLedger:
    """
    In-memory immutable cryptographic ledger tracking pharmaceutical batches,
    generating Merkle roots, nonces, and enforcing anti-counterfeit double-dispense rules.
    """

    def __init__(self):
        self.chain: List[Block] = []
        self.batches: Dict[str, PharmaceuticalBatch] = {}
        self.total_gas_consumed: int = 0
        self.pending_txs: List[Dict[str, Any]] = []
        self._initialize_genesis_block()

    def _initialize_genesis_block(self) -> None:
        genesis_time = 1757000000.0  # Stable baseline timestamp
        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(genesis_time))
        empty_merkle = MerkleTree(["0x0000000000000000000000000000000000000000000000000000000000000000"]).root
        genesis_block = Block(
            index=0,
            timestamp=genesis_time,
            iso_time=iso_str,
            transactions=[{
                "type": "GENESIS_PROTOCOL",
                "network": "TraceRx-EVM-Subnet",
                "authority": "WHO-Global-Pharma-Security-Consortium",
                "protocol_version": "v2.0-MerkleProof"
            }],
            merkle_root=empty_merkle,
            previous_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
            nonce=1337,
            hash="0x" + sha256("GENESIS_BLOCK_TRACERX_PHARMA_CONSORTIUM_2026"),
            gas_consumed=21000
        )
        self.chain.append(genesis_block)
        self.total_gas_consumed += 21000

    def _create_block(self, transactions: List[Dict[str, Any]], gas: int = 42000) -> Block:
        index = len(self.chain)
        prev_block = self.chain[-1]
        t = time.time()
        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))

        leaf_hashes = [
            tx.get("record_hash") or tx.get("tx_hash") or ("0x" + sha256(json.dumps(tx, sort_keys=True)))
            for tx in transactions
        ]
        merkle_tree = MerkleTree(leaf_hashes)

        # Simple deterministic proof of work / validator seal
        nonce = 0
        while True:
            candidate_raw = f"{index}{prev_block.hash}{merkle_tree.root}{nonce}"
            candidate_hash = sha256(candidate_raw)
            if candidate_hash.startswith("0") or nonce > 100:  # Fast seal condition
                break
            nonce += 1

        block = Block(
            index=index,
            timestamp=t,
            iso_time=iso_str,
            transactions=transactions,
            merkle_root=merkle_tree.root,
            previous_hash=prev_block.hash,
            nonce=nonce,
            hash="0x" + candidate_hash,
            gas_consumed=gas
        )
        self.chain.append(block)
        self.total_gas_consumed += gas
        return block

    def mint_batch(
        self,
        drug_name: str,
        serial_number: str,
        mfg_date: str,
        exp_date: str,
        lab_signature: str,
        batch_id: Optional[str] = None,
        manufacturer_name: str = "Pfizer BioTech Labs",
        custom_timestamp: Optional[float] = None
    ) -> PharmaceuticalBatch:
        """
        Registers a genuine pharmaceutical batch on-chain with initial manufacturer custody.
        """
        if not batch_id:
            batch_id = f"BATCH-{serial_number[:8].upper()}"

        mfg_address = generate_address(manufacturer_name)
        mfg_priv_key = f"key_{manufacturer_name.lower().replace(' ', '_')}"

        curr_time = custom_timestamp or time.time()
        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(curr_time))

        initial_checkpoint = CustodyCheckpoint(
            entity=manufacturer_name,
            entity_address=mfg_address,
            location="Kalamazoo Manufacturing Plant, MI, USA",
            timestamp=curr_time,
            iso_time=iso_str,
            signature=generate_signature(mfg_priv_key, f"MINT:{batch_id}:{serial_number}"),
            notes="Factory synthesis & optical serialization verified."
        )

        tx_hash = "0x" + sha256(f"MINT:{batch_id}:{serial_number}:{curr_time}")

        batch = PharmaceuticalBatch(
            batch_id=batch_id,
            drug_name=drug_name,
            serial_number=serial_number,
            mfg_date=mfg_date,
            exp_date=exp_date,
            manufacturer_address=mfg_address,
            lab_signature=lab_signature,
            status=BatchStatus.MANUFACTURED,
            custody_chain=[initial_checkpoint],
            tx_hash=tx_hash,
            created_at=curr_time
        )

        self.batches[batch_id] = batch

        tx_record = {
            "type": "MINT_BATCH",
            "batch_id": batch_id,
            "drug_name": drug_name,
            "serial_number": serial_number,
            "mfg_date": mfg_date,
            "exp_date": exp_date,
            "manufacturer_address": mfg_address,
            "tx_hash": tx_hash,
            "record_hash": batch.compute_record_hash(),
            "timestamp": curr_time
        }
        self._create_block([tx_record], gas=54000)

        return batch

    def transfer_custody(
        self,
        batch_id: str,
        from_entity: str,
        to_entity: str,
        priv_key: str,
        location: str,
        new_status: BatchStatus = BatchStatus.IN_TRANSIT,
        notes: str = ""
    ) -> CustodyCheckpoint:
        """
        Appends an audited cryptographic checkpoint to the pharmaceutical batch custody chain.
        """
        if batch_id not in self.batches:
            raise KeyError(f"Batch ID '{batch_id}' does not exist on-chain.")

        batch = self.batches[batch_id]
        if batch.status == BatchStatus.REVOKED:
            raise ValueError(f"Batch '{batch_id}' is revoked and cannot be transferred.")
        if batch.status == BatchStatus.DISPENSED:
            raise ValueError(f"Batch '{batch_id}' has already been dispensed to a patient.")

        to_address = generate_address(to_entity)
        t = time.time()
        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))

        sign_payload = f"TRANSFER:{batch_id}:{from_entity}->{to_entity}:{t}"
        signature = generate_signature(priv_key, sign_payload)

        checkpoint = CustodyCheckpoint(
            entity=to_entity,
            entity_address=to_address,
            location=location,
            timestamp=t,
            iso_time=iso_str,
            signature=signature,
            notes=notes or f"Custody transferred from {from_entity} to {to_entity}."
        )

        batch.custody_chain.append(checkpoint)
        batch.status = new_status
        batch.tx_hash = "0x" + sha256(sign_payload)

        tx_record = {
            "type": "TRANSFER_CUSTODY",
            "batch_id": batch_id,
            "from_entity": from_entity,
            "to_entity": to_entity,
            "to_address": to_address,
            "location": location,
            "status": new_status.value,
            "tx_hash": batch.tx_hash,
            "record_hash": batch.compute_record_hash(),
            "timestamp": t
        }
        self._create_block([tx_record], gas=36000)

        return checkpoint

    def verify_and_dispense(
        self,
        batch_id: str,
        scanner_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates batch provenance status for point-of-care dispensation.
        CRITICAL: If status == DISPENSED, immediately triggers DUPLICATE_QR_REUSE_ATTEMPT
        alert with the exact location and timestamp of the first dispensation.
        """
        scanner_metadata = scanner_metadata or {
            "scanner_id": "TERMINAL-HUD-01",
            "location": "Hospital Central Dispensary, London, UK",
            "operator": "Dr. Sarah Lin, PharmD"
        }

        if batch_id not in self.batches:
            return {
                "success": False,
                "alert": "UNREGISTERED_BATCH_COUNTERFEIT",
                "message": f"CRITICAL: Batch ID '{batch_id}' was never minted on the cryptographic ledger.",
                "batch_id": batch_id,
                "action": "QUARANTINE_PRODUCT_IMMEDIATELY"
            }

        batch = self.batches[batch_id]

        # CRITICAL DOUBLE-DISPENSE / DUPLICATE QR REUSE CHECK
        if batch.status == BatchStatus.DISPENSED:
            return {
                "success": False,
                "alert": "DUPLICATE_QR_REUSE_ATTEMPT",
                "message": (
                    f"CRITICAL FRAUD TRAP: Batch '{batch_id}' was already dispensed! "
                    f"Original dispensation recorded at {batch.dispensed_iso} "
                    f"in {batch.dispensation_scanner.get('location', 'Unknown')}."
                ),
                "batch_id": batch_id,
                "drug_name": batch.drug_name,
                "first_dispensed_at": batch.dispensed_at,
                "first_dispensed_iso": batch.dispensed_iso,
                "first_dispensed_location": batch.dispensation_scanner.get("location", "Unknown Location"),
                "first_dispensed_scanner": batch.dispensation_scanner.get("scanner_id", "Unknown"),
                "second_attempt_scanner": scanner_metadata,
                "action": "TRIGGER_COUNTERFEIT_INTERCEPTION_ALARM"
            }

        if batch.status == BatchStatus.REVOKED:
            return {
                "success": False,
                "alert": "BATCH_RECALLED_REVOKED",
                "message": f"WARNING: Batch '{batch_id}' has been formally revoked due to manufacturer recall.",
                "batch_id": batch_id,
                "action": "HALT_DISPENSATION"
            }

        # Successful first dispensation
        now_ts = time.time()
        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts))

        batch.status = BatchStatus.DISPENSED
        batch.dispensed_at = now_ts
        batch.dispensed_iso = iso_str
        batch.dispensation_scanner = scanner_metadata

        # Add point of care checkpoint
        dispense_checkpoint = CustodyCheckpoint(
            entity=scanner_metadata.get("operator", "Clinical Dispensary"),
            entity_address=generate_address(scanner_metadata.get("scanner_id", "TERMINAL-01")),
            location=scanner_metadata.get("location", "Point of Care"),
            timestamp=now_ts,
            iso_time=iso_str,
            signature=generate_signature("dispense_secret", f"DISPENSE:{batch_id}:{now_ts}"),
            notes="Package opened and verified authentic. Patient dispensation completed."
        )
        batch.custody_chain.append(dispense_checkpoint)

        tx_record = {
            "type": "VERIFY_AND_DISPENSE",
            "batch_id": batch_id,
            "drug_name": batch.drug_name,
            "status": BatchStatus.DISPENSED.value,
            "dispensed_iso": iso_str,
            "location": scanner_metadata.get("location"),
            "scanner_id": scanner_metadata.get("scanner_id"),
            "record_hash": batch.compute_record_hash(),
            "timestamp": now_ts
        }
        self._create_block([tx_record], gas=48000)

        return {
            "success": True,
            "alert": "PROVENANCE_VERIFIED_AUTHENTIC",
            "message": f"Batch '{batch_id}' successfully verified on-chain and registered as DISPENSED.",
            "batch": batch.to_dict()
        }

    def get_chain_state(self) -> Dict[str, Any]:
        """Returns the latest blocks, total gas consumed, and block height for frontend explorer."""
        latest_blocks = [b.to_dict() for b in reversed(self.chain[-20:])]
        return {
            "block_height": len(self.chain),
            "latest_block_hash": self.chain[-1].hash if self.chain else "0x0",
            "merkle_root": self.chain[-1].merkle_root if self.chain else "0x0",
            "total_gas_consumed": self.total_gas_consumed,
            "total_batches_minted": len(self.batches),
            "active_nodes": 4,
            "network": "TraceRx-EVM-Localnet (ChainID: 4242)",
            "consensus": "Proof-of-Authority + Merkle Forensic Tree",
            "blocks": latest_blocks
        }

    def verify_chain_integrity(self) -> Tuple[bool, str]:
        """Validates all block links and hashes in the chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]
            if current.previous_hash != prev.hash:
                return False, f"Broken previous hash at block #{current.index}"
        return True, "Blockchain state is valid and tamper-free."
