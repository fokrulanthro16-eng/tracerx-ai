"""
TraceRx AI - Enterprise Test Suite
Validates GS1 DataMatrix decoding, 2D FFT micro-texture analysis,
EPCIS 2.0 JSON-LD document generation, and Role-Based Access Control (RBAC).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.vision_service import production_vision
from backend.app.models.epcis_schema import (
    ObjectEvent,
    AggregationEvent,
    EPCISDocument,
    EPCISAction,
    BizStep,
    Disposition
)
from backend.mock_data import generate_synthetic_packaging_image


@pytest.fixture
def client():
    return TestClient(app)


def test_gs1_datamatrix_parser():
    sample_string = "(01)00300019920148(21)SN990142(17)280301(10)PZ-2026-X99"
    img = production_vision.load_image(
        generate_synthetic_packaging_image("Remdesivir", "PZ-2026-X99", "2028-03-01", "SN-990142", "Pfizer")
    )
    parsed = production_vision.parse_gs1_datamatrix(img, simulated_raw_string=sample_string)

    assert parsed["gtin"] == "00300019920148"
    assert parsed["serial_number"] == "SN990142"
    assert parsed["expiry_date"] == "2028-03-01"
    assert parsed["batch_lot"] == "PZ-2026-X99"
    assert parsed["is_gs1_compliant"] is True


def test_fft_micro_texture_analysis():
    # Authentic offset packaging
    img_genuine = production_vision.load_image(
        generate_synthetic_packaging_image("Remdesivir", "PZ", "2028", "SN", "Pfizer", is_counterfeit_print=False)
    )
    fft_gen = production_vision.analyze_fft_micro_texture(img_genuine)
    assert fft_gen["spectral_ratio"] > 0.45
    assert fft_gen["estimated_dpi"] >= 450

    # Low frequency counterfeit
    img_fake = production_vision.load_image(
        generate_synthetic_packaging_image("Fake", "PZ", "2028", "SN", "Fake", is_counterfeit_print=True)
    )
    fft_fake = production_vision.analyze_fft_micro_texture(img_fake)
    assert fft_gen["spectral_ratio"] >= fft_fake["spectral_ratio"]


def test_epcis_2_document_generation():
    obj_event = ObjectEvent(
        action=EPCISAction.ADD,
        bizStep=BizStep.COMMISSIONING,
        disposition=Disposition.ACTIVE,
        epcList=["urn:epc:id:sgtin:0030001.012345.SN1001", "urn:epc:id:sgtin:0030001.012345.SN1002"]
    )
    agg_event = AggregationEvent(
        parentID="urn:epc:id:sscc:0030001.0000000012",
        childEPCs=["urn:epc:id:sgtin:0030001.012345.SN1001", "urn:epc:id:sgtin:0030001.012345.SN1002"]
    )

    doc = EPCISDocument.create([obj_event, agg_event])
    doc_json = doc.model_dump(by_alias=True)

    assert "@context" in doc_json
    assert doc_json["type"] == "EPCISDocument"
    assert doc_json["schemaVersion"] == "2.0"
    assert len(doc_json["epcisBody"]["eventList"]) == 2


def test_v1_api_scan_endpoint(client):
    res = client.post(
        "/api/v1/scan",
        data={
            "expected_batch_id": "PZ-2026-X99",
            "simulated_gs1": "(01)00300019920148(21)SN990142(17)280301(10)PZ-2026-X99"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "GENUINE_AUTHENTIC"
    assert data["authenticity_index"] >= 88.0
    assert data["gs1_metadata"]["gtin"] == "00300019920148"
    assert "spectral_texture" in data


def test_v1_api_rbac_restrictions(client):
    # Attempting to mint without manufacturer role should fail with 403
    unauthorized_res = client.post(
        "/api/v1/batches/mint",
        json={
            "gtin": "00300019920148",
            "batch_lot": "LOT-99",
            "drug_name": "Test",
            "expiry_timestamp": 1789000000,
            "merkle_root": "0x0"
        },
        headers={"x-api-key": "pharm_pharmacy_key"}
    )
    assert unauthorized_res.status_code == 403

    # With verified manufacturer role
    authorized_res = client.post(
        "/api/v1/batches/mint",
        json={
            "gtin": "00300019920148",
            "batch_lot": "LOT-99",
            "drug_name": "Test",
            "expiry_timestamp": 1789000000,
            "merkle_root": "0x0"
        },
        headers={"x-api-key": "mfg_pfizer_key"}
    )
    assert authorized_res.status_code == 201


def test_v1_epcis_export_endpoint(client):
    res = client.get("/api/v1/epcis/document/PZ-2026-X99")
    assert res.status_code == 200
    doc = res.json()
    assert doc["schemaVersion"] == "2.0"
    assert "@context" in doc
    assert len(doc["epcisBody"]["eventList"]) >= 1
