"""
TraceRx AI - Computer Vision Forensic Verification Test Suite
Validates micro-print analysis, hologram reflection checks, and packaging tampering detection.
"""

import pytest
import numpy as np
from backend.vision_forensics import VisionForensicEngine
from backend.mock_data import generate_synthetic_packaging_image


@pytest.fixture
def vision_engine():
    return VisionForensicEngine()


def test_microprint_analysis_genuine(vision_engine):
    # Generate high resolution authentic packaging
    b64 = generate_synthetic_packaging_image(
        drug_name="Remdesivir",
        batch_id="PZ-2026-X99",
        exp_date="2028-03",
        serial_no="SN-001",
        manufacturer="Pfizer",
        is_tampered=False,
        is_counterfeit_print=False
    )
    img = vision_engine.load_image_from_base64(b64)
    result = vision_engine.analyze_microprint_integrity(img)

    assert result["estimated_dpi"] >= 450
    assert result["sharpness_score"] > 30.0
    assert result["microprint_status"] == "HIGH_RESOLUTION_CRISP"


def test_microprint_analysis_counterfeit_blur(vision_engine):
    # Generate low DPI blurred packaging
    b64 = generate_synthetic_packaging_image(
        drug_name="Fake Remdesivir",
        batch_id="PZ-FAKE",
        exp_date="2028-03",
        serial_no="SN-FAKE",
        manufacturer="Counterfeit Lab",
        is_tampered=True,
        is_counterfeit_print=True
    )
    img = vision_engine.load_image_from_base64(b64)
    result = vision_engine.analyze_microprint_integrity(img)

    assert result["estimated_dpi"] < 400
    assert result["blur_factor"] > 0.3


def test_hologram_diffraction_vs_matte(vision_engine):
    genuine_b64 = generate_synthetic_packaging_image(
        drug_name="Genuine Drug",
        batch_id="GEN-01",
        exp_date="2028-01",
        serial_no="SN-GEN",
        manufacturer="Pfizer",
        is_counterfeit_print=False
    )
    img_genuine = vision_engine.load_image_from_base64(genuine_b64)
    holo_genuine = vision_engine.analyze_hologram_reflection(img_genuine)

    fake_b64 = generate_synthetic_packaging_image(
        drug_name="Fake Drug",
        batch_id="FAKE-01",
        exp_date="2028-01",
        serial_no="SN-FAKE",
        manufacturer="Fake",
        is_counterfeit_print=True
    )
    img_fake = vision_engine.load_image_from_base64(fake_b64)
    holo_fake = vision_engine.analyze_hologram_reflection(img_fake)

    assert holo_genuine["hologram_score"] > holo_fake["hologram_score"]
    assert holo_genuine["refraction_verdict"] == "DIFFRACTIVE_OVD_AUTHENTIC"


def test_full_packaging_evaluation(vision_engine):
    # Test Genuine
    genuine_b64 = generate_synthetic_packaging_image(
        drug_name="Remdesivir",
        batch_id="PZ-2026-X99",
        exp_date="2028-03-01",
        serial_no="SN-999",
        manufacturer="Pfizer",
        is_tampered=False
    )
    img_genuine = vision_engine.load_image_from_base64(genuine_b64)
    eval_genuine = vision_engine.evaluate_packaging(
        img_genuine,
        expected_batch_id="PZ-2026-X99",
        simulated_text="BATCH: PZ-2026-X99 EXP: 2028-03 SN: SN-999"
    )

    assert eval_genuine["authenticity_score"] >= 88.0
    assert eval_genuine["verdict"] == "GENUINE_AUTHENTIC"
    assert eval_genuine["tampering_index"] < 0.25
    assert eval_genuine["batch_match"] is True

    # Test Tampered
    tampered_b64 = generate_synthetic_packaging_image(
        drug_name="Insulin",
        batch_id="SN-3310-F",
        exp_date="2029-12",
        serial_no="SN-110",
        manufacturer="Sanofi",
        is_tampered=True,
        is_counterfeit_print=True
    )
    img_tampered = vision_engine.load_image_from_base64(tampered_b64)
    eval_tampered = vision_engine.evaluate_packaging(
        img_tampered,
        expected_batch_id="SN-3310-F",
        force_tamper_flag=True
    )

    assert eval_tampered["authenticity_score"] < 50.0
    assert eval_tampered["verdict"] == "COUNTERFEIT_PHYSICAL_TAMPER"
    assert eval_tampered["tampering_index"] > 0.50
