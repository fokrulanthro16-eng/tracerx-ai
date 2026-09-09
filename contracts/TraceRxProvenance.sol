// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title TraceRxProvenance
 * @notice Enterprise pharmaceutical batch provenance and anti-counterfeit ledger.
 * Deployed to Polygon Amoy / Base Sepolia L2 for sub-cent gas transactions.
 */
contract TraceRxProvenance is AccessControl, ERC1155 {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    bytes32 public constant MANUFACTURER_ROLE = keccak256("MANUFACTURER_ROLE");
    bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");
    bytes32 public constant PHARMACY_ROLE = keccak256("PHARMACY_ROLE");
    bytes32 public constant REGULATOR_ROLE = keccak256("REGULATOR_ROLE");

    enum BatchStatus {
        Active,
        Dispensed,
        Recalled
    }

    struct Batch {
        uint256 id;
        string gtin;              // GS1 Global Trade Item Number (14 digits)
        string batchLot;          // GS1 AI(10) Batch / Lot
        uint256 expiryDate;       // Unix timestamp of expiration
        bytes32 merkleRoot;       // Merkle root of itemized packaging serialization
        BatchStatus status;
        address currentCustodian;
        address manufacturer;
        uint256 mintedAt;
        uint256 firstDispensedAt;
        bytes32 firstDispenserScanner;
    }

    // Mapping from batchId to Batch metadata
    mapping(uint256 => Batch) public batches;
    // Custody history checkpoint hashes
    mapping(uint256 => bytes32[]) public custodyHistory;
    // GTIN + BatchLot mapping to batchId for fast lookup
    mapping(bytes32 => uint256) public batchLookup;

    uint256 public totalBatchesMinted;

    // Custom errors for gas efficiency
    error BatchNotFound(uint256 batchId);
    error AlreadyDispensed(uint256 batchId, uint256 timestamp, bytes32 originalScanner);
    error BatchRecalled(uint256 batchId);
    error InvalidCustodian(address expected, address actual);
    error InvalidSignature(address signer);

    // Standardized enterprise events
    event BatchMinted(
        uint256 indexed batchId,
        string gtin,
        string batchLot,
        uint256 expiryDate,
        bytes32 merkleRoot,
        address indexed manufacturer
    );

    event CustodyTransferred(
        uint256 indexed batchId,
        address indexed from,
        address indexed to,
        uint256 timestamp,
        bytes32 checkpointHash
    );

    event BatchDispensed(
        uint256 indexed batchId,
        address indexed dispenser,
        bytes32 scannerHash,
        uint256 timestamp
    );

    event FraudulentReuseFlagged(
        uint256 indexed batchId,
        bytes32 attemptedScanner,
        address indexed caller,
        uint256 timestamp,
        uint256 originalDispensedAt
    );

    event BatchRecalledEvent(
        uint256 indexed batchId,
        string reason,
        address indexed regulator
    );

    constructor(string memory uri_) ERC1155(uri_) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MANUFACTURER_ROLE, msg.sender);
        _grantRole(REGULATOR_ROLE, msg.sender);
    }

    /**
     * @notice Registers and mints a verified pharmaceutical batch on-chain.
     * @param gtin GS1 Global Trade Item Number
     * @param batchLot Manufacturer Lot number
     * @param expiryDate Expiration timestamp
     * @param merkleRoot Cryptographic packaging Merkle root
     * @param units Quantity of serialized units in batch
     */
    function mintBatch(
        string calldata gtin,
        string calldata batchLot,
        uint256 expiryDate,
        bytes32 merkleRoot,
        uint256 units
    ) external onlyRole(MANUFACTURER_ROLE) returns (uint256) {
        totalBatchesMinted++;
        uint256 newBatchId = totalBatchesMinted;

        bytes32 lookupKey = keccak256(abi.encodePacked(gtin, batchLot));

        batches[newBatchId] = Batch({
            id: newBatchId,
            gtin: gtin,
            batchLot: batchLot,
            expiryDate: expiryDate,
            merkleRoot: merkleRoot,
            status: BatchStatus.Active,
            currentCustodian: msg.sender,
            manufacturer: msg.sender,
            mintedAt: block.timestamp,
            firstDispensedAt: 0,
            firstDispenserScanner: bytes32(0)
        });

        batchLookup[lookupKey] = newBatchId;

        // Record initial custody checkpoint
        bytes32 initialHash = keccak256(
            abi.encodePacked(newBatchId, msg.sender, block.timestamp)
        );
        custodyHistory[newBatchId].push(initialHash);

        // Mint ERC1155 supply token representing verifiable ownership
        _mint(msg.sender, newBatchId, units, "");

        emit BatchMinted(
            newBatchId,
            gtin,
            batchLot,
            expiryDate,
            merkleRoot,
            msg.sender
        );

        return newBatchId;
    }

    /**
     * @notice Transfers batch custody along the supply chain with cryptographic non-repudiation.
     * @param batchId Unique batch identifier
     * @param to Receiving supply chain entity
     * @param signature Cryptographic digital signature of the transfer authorization
     */
    function transferCustody(
        uint256 batchId,
        address to,
        bytes calldata signature
    ) external {
        Batch storage batch = batches[batchId];
        if (batch.id == 0) revert BatchNotFound(batchId);
        if (batch.status == BatchStatus.Dispensed) {
            revert AlreadyDispensed(batchId, batch.firstDispensedAt, batch.firstDispenserScanner);
        }
        if (batch.status == BatchStatus.Recalled) revert BatchRecalled(batchId);

        address current = batch.currentCustodian;
        if (msg.sender != current && !hasRole(DEFAULT_ADMIN_ROLE, msg.sender)) {
            revert InvalidCustodian(current, msg.sender);
        }

        // Verify non-repudiation signature if provided
        if (signature.length == 65) {
            bytes32 messageHash = keccak256(
                abi.encodePacked(batchId, current, to, block.chainid)
            );
            bytes32 ethSigned = messageHash.toEthSignedMessageHash();
            address recovered = ethSigned.recover(signature);
            if (recovered != current) revert InvalidSignature(recovered);
        }

        batch.currentCustodian = to;

        bytes32 checkpointHash = keccak256(
            abi.encodePacked(batchId, current, to, block.timestamp)
        );
        custodyHistory[batchId].push(checkpointHash);

        emit CustodyTransferred(batchId, current, to, block.timestamp, checkpointHash);
    }

    /**
     * @notice Validates point-of-care patient dispensation.
     * CRITICAL: Halts and flags duplicate QR double-dispense fraud attempts.
     * @param batchId Unique batch identifier
     * @param scannerHash Hash of the optical inspection scanner ID and location
     */
    function dispenseToPatient(
        uint256 batchId,
        bytes32 scannerHash
    ) external returns (bool) {
        Batch storage batch = batches[batchId];
        if (batch.id == 0) revert BatchNotFound(batchId);

        // Anti-counterfeit double-spend detection
        if (batch.status == BatchStatus.Dispensed) {
            emit FraudulentReuseFlagged(
                batchId,
                scannerHash,
                msg.sender,
                block.timestamp,
                batch.firstDispensedAt
            );
            revert AlreadyDispensed(batchId, batch.firstDispensedAt, batch.firstDispenserScanner);
        }

        if (batch.status == BatchStatus.Recalled) {
            revert BatchRecalled(batchId);
        }

        batch.status = BatchStatus.Dispensed;
        batch.firstDispensedAt = block.timestamp;
        batch.firstDispenserScanner = scannerHash;
        batch.currentCustodian = address(0); // Burned from active custody

        emit BatchDispensed(batchId, msg.sender, scannerHash, block.timestamp);
        return true;
    }

    /**
     * @notice Allows a regulator or manufacturer to recall a compromised batch.
     */
    function recallBatch(uint256 batchId, string calldata reason) external {
        Batch storage batch = batches[batchId];
        if (batch.id == 0) revert BatchNotFound(batchId);
        if (!hasRole(REGULATOR_ROLE, msg.sender) && msg.sender != batch.manufacturer) {
            revert AccessControlUnauthorizedAccount(msg.sender, REGULATOR_ROLE);
        }

        batch.status = BatchStatus.Recalled;
        emit BatchRecalledEvent(batchId, reason, msg.sender);
    }

    /**
     * @notice Returns complete custody checkpoints for a batch.
     */
    function getCustodyCheckpoints(uint256 batchId) external view returns (bytes32[] memory) {
        return custodyHistory[batchId];
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(AccessControl, ERC1155)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
