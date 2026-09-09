"""
TraceRx AI - Pre-Seeded Pharmaceutical Batch Registry & Test Scenarios
Generates the 3 hackathon evaluation scenarios with on-chain records and synthetic packaging images.
"""

from __future__ import annotations
import base64
import io
import time
from typing import Dict, Any, List
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from backend.blockchain_ledger import CryptographicLedger, BatchStatus, generate_address


def generate_synthetic_packaging_image(
    drug_name: str,
    batch_id: str,
    exp_date: str,
    serial_no: str,
    manufacturer: str,
    is_tampered: bool = False,
    is_counterfeit_print: bool = False
) -> str:
    """
    Generates a realistic pharmaceutical packaging blister/box image with security microprint,
    hologram strip, QR/DataMatrix simulation, and returns it as a base64 data URI string.
    """
    width, height = 640, 420
    # Background color: clean pharma matte white or suspicious off-white
    bg_color = (235, 230, 225) if is_tampered else (248, 250, 252)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Subtle security guilloche pattern / micro-print background grid
    step = 8 if not is_counterfeit_print else 24
    grid_color = (220, 226, 235) if not is_tampered else (200, 200, 190)
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # 2. Manufacturer Branding Banner
    banner_color = (14, 116, 144) if "Pfizer" in manufacturer else ((180, 83, 9) if "GSK" in manufacturer else (159, 18, 57))
    draw.rectangle([(0, 0), (width, 70)], fill=banner_color)

    # Text headers
    draw.text((25, 18), f"{manufacturer.upper()} PHARMACEUTICALS", fill=(255, 255, 255))
    draw.text((width - 170, 22), "GLOBAL SECURE RX", fill=(200, 240, 255))

    # 3. Main Drug Title
    draw.text((35, 95), drug_name, fill=(15, 23, 42))
    draw.text((35, 125), "Sterile Lyophilized Formulation | 100 mg / Vial", fill=(100, 116, 139))

    # 4. Security Hologram Strip (Right side)
    holo_x = width - 110
    if not is_counterfeit_print:
        # Iridescent holographic spectrum simulation
        for i in range(120):
            # Rainbow gradient
            hue_r = int(128 + 127 * np.sin(i * 0.15))
            hue_g = int(128 + 127 * np.sin(i * 0.15 + 2.0))
            hue_b = int(128 + 127 * np.sin(i * 0.15 + 4.0))
            draw.line([(holo_x, 90 + i * 2), (holo_x + 80, 90 + i * 2)], fill=(hue_r, hue_g, hue_b), width=2)
        draw.rectangle([(holo_x, 90), (holo_x + 80, 330)], outline=(255, 255, 255), width=2)
        draw.text((holo_x + 8, 200), "ORIGINAL", fill=(255, 255, 255))
    else:
        # Dull matte fake print (photocopied flat gray)
        draw.rectangle([(holo_x, 90), (holo_x + 80, 330)], fill=(180, 180, 180), outline=(100, 100, 100), width=2)
        draw.text((holo_x + 12, 200), "COPIED", fill=(90, 90, 90))

    # 5. Packaging Metadata Box
    box_top = 170
    draw.rectangle([(30, box_top), (480, box_top + 160)], fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    # Simulated Data Matrix QR block
    matrix_size = 90
    draw.rectangle([(45, box_top + 35), (45 + matrix_size, box_top + 35 + matrix_size)], fill=(20, 20, 20))
    # Inner random QR-like pattern
    np.random.seed(42 if not is_tampered else 137)
    for qx in range(6):
        for qy in range(6):
            if np.random.rand() > 0.45:
                draw.rectangle([
                    (45 + qx * 15, box_top + 35 + qy * 15),
                    (45 + (qx + 1) * 15, box_top + 35 + (qy + 1) * 15)
                ], fill=(255, 255, 255))

    # Metadata Labels
    info_x = 160
    draw.text((info_x, box_top + 20), f"BATCH NO:  {batch_id}", fill=(15, 23, 42))
    draw.text((info_x, box_top + 50), f"SERIAL NO: {serial_no}", fill=(51, 65, 85))
    draw.text((info_x, box_top + 80), f"EXPIRY:    {exp_date}", fill=(15, 23, 42) if not is_tampered else (220, 38, 38))
    draw.text((info_x, box_top + 110), f"MFG LIC:   FDA-US-992014B", fill=(100, 116, 139))

    # 6. Physical Tampering Artifacts if enabled
    if is_tampered:
        # Blurred smudge or sticker overlay on expiry date
        draw.rectangle([(info_x + 80, box_top + 75), (info_x + 230, box_top + 102)], fill=(254, 240, 138), outline=(239, 68, 68), width=2)
        draw.text((info_x + 85, box_top + 80), "EXP: 2029-12 [ALTERED]", fill=(185, 28, 28))
        # Scratch across package
        draw.line([(60, box_top + 10), (320, box_top + 140)], fill=(120, 120, 120), width=3)
        draw.line([(280, 50), (450, 220)], fill=(200, 50, 50), width=2)

    # Convert to OpenCV format to apply blur or sharpness effects
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    if is_counterfeit_print:
        # Simulate low-DPI 150-200 DPI inkjet print via downsampling and edge blur
        h, w = cv_img.shape[:2]
        low = cv2.resize(cv_img, (w // 4, h // 4), interpolation=cv2.INTER_LINEAR)
        cv_img = cv2.resize(low, (w, h), interpolation=cv2.INTER_LINEAR)
        cv_img = cv2.GaussianBlur(cv_img, (7, 7), 2.0)
    else:
        # Authentic 600 DPI crisp packaging
        kernel = np.array([[0, -0.2, 0], [-0.2, 1.8, -0.2], [0, -0.2, 0]])
        cv_img = cv2.filter2D(cv_img, -1, kernel)

    # Encode to JPEG in-memory
    _, buffer = cv2.imencode(".jpg", cv_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def seed_mock_scenarios(ledger: CryptographicLedger) -> List[Dict[str, Any]]:
    """
    Pre-populates the CryptographicLedger with the 3 canonical judge scenarios
    and generates visual assets and metadata.
    """
    scenarios: List[Dict[str, Any]] = []

    # =========================================================================
    # Scenario 1: Authentic Pfizer Remdesivir (PZ-2026-X99)
    # Genuine packaging, intact chain, pristine micro-print, 99.4% verified.
    # =========================================================================
    batch_1_id = "PZ-2026-X99"
    sn_1 = "SN-PFZ-990142"
    mfg_time_1 = 1757010000.0  # Stable recent timestamp
    b1 = ledger.mint_batch(
        drug_name="Remdesivir (Veklury) 100mg",
        serial_number=sn_1,
        mfg_date="2026-03-01",
        exp_date="2028-03-01",
        lab_signature="0x9a8f4c2e71b5d6a89c0e3f2187b5a3c9e120f4b8",
        batch_id=batch_1_id,
        manufacturer_name="Pfizer BioTech Global",
        custom_timestamp=mfg_time_1
    )
    # Transit checkpoint: Antwerp International Port Hub
    ledger.transfer_custody(
        batch_id=batch_1_id,
        from_entity="Pfizer BioTech Global",
        to_entity="DHL Pharma ColdChain Logistics",
        priv_key="key_pfizer_logistics",
        location="Antwerp Port Cargo Terminal 4, Belgium",
        new_status=BatchStatus.IN_TRANSIT,
        notes="Cryo-monitored pallet #418 sealed at 2.4°C."
    )
    # Pharmacy arrival checkpoint
    ledger.transfer_custody(
        batch_id=batch_1_id,
        from_entity="DHL Pharma ColdChain Logistics",
        to_entity="St. Thomas Hospital Pharmacy",
        priv_key="key_dhl_freight",
        location="St. Thomas Central Pharmacy, London, UK",
        new_status=BatchStatus.RECEIVED_AT_PHARMACY,
        notes="Package intact, tamper seal verified by pharmacy staff."
    )

    img_b64_1 = generate_synthetic_packaging_image(
        drug_name="Remdesivir (Veklury) 100mg",
        batch_id=batch_1_id,
        exp_date="2028-03-01",
        serial_no=sn_1,
        manufacturer="Pfizer BioTech Global",
        is_tampered=False,
        is_counterfeit_print=False
    )

    scenarios.append({
        "id": "scenario-1",
        "name": "Scenario 1: Authentic Pfizer Drug",
        "badge": "GENUINE VERIFIED (99.4%)",
        "badge_color": "emerald",
        "drug_name": "Remdesivir (Veklury) 100mg",
        "batch_id": batch_1_id,
        "serial_number": sn_1,
        "manufacturer": "Pfizer BioTech Global",
        "expected_verdict": "GENUINE_AUTHENTIC",
        "expected_status": "RECEIVED_AT_PHARMACY",
        "expected_score": 99.4,
        "description": "Pristine packaging, 600 DPI microprint, iridescent diffraction OVD hologram intact. Full unbroken cold-chain provenance from Kalamazoo to London.",
        "simulated_text": f"BATCH: {batch_1_id} EXP: 2028-03 SN: {sn_1}",
        "force_tamper": False,
        "image_data": img_b64_1
    })

    # =========================================================================
    # Scenario 2: Counterfeit Reuse Trap: GSK Amoxicillin (GSK-8812-D)
    # Packaging visually authentic (cloned QR), but already dispensed in Dhaka!
    # =========================================================================
    batch_2_id = "GSK-8812-D"
    sn_2 = "SN-GSK-448201"
    mfg_time_2 = 1756500000.0
    b2 = ledger.mint_batch(
        drug_name="Amoxicillin & Clavulanate 625mg",
        serial_number=sn_2,
        mfg_date="2026-01-10",
        exp_date="2027-06-15",
        lab_signature="0x77c2b09a4d3f18e9a2b5c87e1f40d2a938c11e74",
        batch_id=batch_2_id,
        manufacturer_name="GSK Pharmaceuticals UK",
        custom_timestamp=mfg_time_2
    )
    # Delivered to Bangladesh distributor
    ledger.transfer_custody(
        batch_id=batch_2_id,
        from_entity="GSK Pharmaceuticals UK",
        to_entity="MediCare National Distributors",
        priv_key="key_gsk_pharma",
        location="Hazrat Shahjalal Cargo Hub, Dhaka, Bangladesh",
        new_status=BatchStatus.RECEIVED_AT_PHARMACY,
        notes="Customs clearance completed, cold storage verified."
    )
    # Already dispensed on Sep 5, 2026 in Dhaka!
    ledger.verify_and_dispense(
        batch_id=batch_2_id,
        scanner_metadata={
            "scanner_id": "DHAKA-CENTRAL-CLINIC-POS-04",
            "location": "Square Hospital Dispensary, Panthapath, Dhaka",
            "operator": "Dr. Farhan Ahmed, RPh",
            "patient_receipt": "RX-DHK-2026-0905-88"
        }
    )

    img_b64_2 = generate_synthetic_packaging_image(
        drug_name="Amoxicillin & Clavulanate 625mg",
        batch_id=batch_2_id,
        exp_date="2027-06-15",
        serial_no=sn_2,
        manufacturer="GSK Pharmaceuticals",
        is_tampered=False,
        is_counterfeit_print=False
    )

    scenarios.append({
        "id": "scenario-2",
        "name": "Scenario 2: Counterfeit QR Reuse Trap",
        "badge": "DOUBLE-SPEND QR FRAUD DETECTED",
        "badge_color": "crimson",
        "drug_name": "Amoxicillin & Clavulanate 625mg",
        "batch_id": batch_2_id,
        "serial_number": sn_2,
        "manufacturer": "GSK Pharmaceuticals",
        "expected_verdict": "DUPLICATE_QR_REUSE_ATTEMPT",
        "expected_status": "DISPENSED",
        "expected_score": 92.0,  # Physical package looks ok, but ledger halts transaction!
        "description": "CRITICAL REUSE TRAP: Physical packaging seems authentic, but the on-chain Merkle ledger halts dispensation — this exact serial number was already dispensed on Sep 5, 2026 at Square Hospital, Dhaka.",
        "simulated_text": f"BATCH: {batch_2_id} EXP: 2027-06 SN: {sn_2}",
        "force_tamper": False,
        "image_data": img_b64_2
    })

    # =========================================================================
    # Scenario 3: Physical Tamper Alert: Sanofi Insulin (SN-3310-F)
    # Tampered packaging detected: altered expiry sticker, low-DPI micro-print,
    # and matte photocopy reflection.
    # =========================================================================
    batch_3_id = "SN-3310-F"
    sn_3 = "SN-SNF-110293"
    mfg_time_3 = 1756000000.0
    b3 = ledger.mint_batch(
        drug_name="Lantus Insulin Glargine 100 U/mL",
        serial_number=sn_3,
        mfg_date="2025-08-01",
        exp_date="2026-08-01",  # Legit expiry was 2026-08 (EXPIRED!)
        lab_signature="0x11223344556677889900aabbccddeeff00112233",
        batch_id=batch_3_id,
        manufacturer_name="Sanofi Pasteur BioTech",
        custom_timestamp=mfg_time_3
    )

    img_b64_3 = generate_synthetic_packaging_image(
        drug_name="Lantus Insulin Glargine 100 U/mL",
        batch_id=batch_3_id,
        exp_date="2029-12",  # Fraudulent altered expiry date!
        serial_no=sn_3,
        manufacturer="Sanofi Pasteur BioTech",
        is_tampered=True,
        is_counterfeit_print=True
    )

    scenarios.append({
        "id": "scenario-3",
        "name": "Scenario 3: Physical Tamper Alert",
        "badge": "COUNTERFEIT PACKAGING INTERCEPTED",
        "badge_color": "crimson",
        "drug_name": "Lantus Insulin Glargine 100 U/mL",
        "batch_id": batch_3_id,
        "serial_number": sn_3,
        "manufacturer": "Sanofi Pasteur BioTech",
        "expected_verdict": "COUNTERFEIT_PHYSICAL_TAMPER",
        "expected_status": "MANUFACTURED",
        "expected_score": 14.2,
        "description": "Severe physical tampering: Expiry date re-printed/relabeled from expired 2026-08 to fake 2029-12. Degraded 190 DPI edge blur, non-reflective matte hologram photocopy, high tamper index.",
        "simulated_text": f"BATCH: {batch_3_id} EXP: 2029-12 SN: {sn_3}",
        "force_tamper": True,
        "image_data": img_b64_3
    })

    return scenarios
