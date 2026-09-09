"""
TraceRx AI - FastAPI Server & High-Performance Forensic Engine
Exposes REST and WebSocket endpoints on port 8080.
"""

from __future__ import annotations
import base64
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from backend.blockchain_ledger import CryptographicLedger, BatchStatus
from backend.vision_forensics import VisionForensicEngine
from backend.mock_data import seed_mock_scenarios
from backend.app.api.v1 import api_v1_router

# Instantiate core engines
ledger = CryptographicLedger()
forensic_engine = VisionForensicEngine()

# Seed initial blockchain state and 3 judge scenarios
scenarios_registry = seed_mock_scenarios(ledger)

app = FastAPI(
    title="TraceRx AI Enterprise — Autonomous Pharmaceutical Provenance Engine",
    description="Enterprise pharmaceutical vision forensics, GS1 EPCIS 2.0, and Polygon/Base L2 provenance ledger.",
    version="2.0.0-PROD"
)

# Enable CORS for local cross-origin tooling if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount enterprise v1 router
app.include_router(api_v1_router)

# Telemetry active WebSocket connections
connected_websockets: List[WebSocket] = []


class ScanRequest(BaseModel):
    image_base64: Optional[str] = None
    batch_id: Optional[str] = None
    simulated_text: Optional[str] = None
    force_tamper: Optional[bool] = False
    scanner_metadata: Optional[Dict[str, Any]] = None


class DispenseRequest(BaseModel):
    batch_id: str
    scanner_metadata: Optional[Dict[str, Any]] = None


async def broadcast_telemetry(event_type: str, data: Dict[str, Any]):
    """Broadcasts real-time events to all connected HUD telemetry clients."""
    payload = {
        "event": event_type,
        "timestamp": time.time(),
        "data": data
    }
    for ws in list(connected_websockets):
        try:
            await ws.send_json(payload)
        except Exception:
            if ws in connected_websockets:
                connected_websockets.remove(ws)


@app.get("/api/health")
def health_check():
    """Healthcheck endpoint for Docker container, CI runners, and load balancers."""
    return {
        "status": "HEALTHY",
        "service": "TraceRx-AI-Core",
        "timestamp": time.time(),
        "ledger_blocks": len(ledger.chain),
        "vision_engine": "ACTIVE_OPENCV_MULTI_SPECTRAL"
    }


@app.get("/api/scenarios")
def get_scenarios():
    """Returns the 3 pre-seeded judge evaluation scenarios."""
    return {
        "scenarios": scenarios_registry,
        "total": len(scenarios_registry)
    }


@app.post("/api/scan")
async def execute_forensic_scan(
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    batch_id: Optional[str] = Form(None),
    simulated_text: Optional[str] = Form(None),
    force_tamper: Optional[bool] = Form(False),
    scanner_id: Optional[str] = Form("TERMINAL-HUD-01"),
    location: Optional[str] = Form("Central Point-of-Care Dispensary, London")
):
    """
    Core forensic verification pipeline:
    1. Ingests packaging image (file upload, base64, or simulation).
    2. Runs multi-spectral vision forensics (microprint, hologram refraction, DPI).
    3. Cross-examines batch against immutable cryptographic Merkle ledger.
    4. Triggers anti-counterfeit double-dispense traps if reused.
    """
    t_start = time.perf_counter()

    # Normalize parameters if invoked directly
    actual_batch_id = batch_id if isinstance(batch_id, str) and batch_id else None
    actual_text = simulated_text if isinstance(simulated_text, str) and simulated_text else None
    actual_tamper = force_tamper if isinstance(force_tamper, bool) else (str(force_tamper).lower() == "true")

    # Process image input
    img_bgr = None
    if isinstance(image, UploadFile):
        raw_bytes = await image.read()
        img_bgr = forensic_engine.load_image_from_bytes(raw_bytes)
    elif isinstance(image_base64, str) and image_base64:
        img_bgr = forensic_engine.load_image_from_base64(image_base64)
    else:
        # Fallback to generating a pristine synthetic sample
        from backend.mock_data import generate_synthetic_packaging_image
        b64 = generate_synthetic_packaging_image(
            drug_name="Generic Test Drug",
            batch_id=actual_batch_id or "PZ-2026-X99",
            exp_date="2028-01",
            serial_no="SN-TEST-001",
            manufacturer="Global Pharma",
            is_tampered=actual_tamper
        )
        img_bgr = forensic_engine.load_image_from_base64(b64)

    # 1. Computer Vision Forensic Analysis
    vision_results = forensic_engine.evaluate_packaging(
        img=img_bgr,
        expected_batch_id=actual_batch_id,
        simulated_text=actual_text,
        force_tamper_flag=actual_tamper
    )

    # 2. Extract or infer batch ID
    resolved_batch_id = (
        actual_batch_id or
        vision_results["details"]["metadata"].get("batch_id") or
        "PZ-2026-X99"
    )

    # 3. Blockchain Ledger Cross-Verification
    batch_record = ledger.batches.get(resolved_batch_id)
    on_chain_status = batch_record.status.value if batch_record else "UNREGISTERED"

    blockchain_verification: Dict[str, Any] = {
        "batch_id": resolved_batch_id,
        "is_minted_on_chain": batch_record is not None,
        "current_status": on_chain_status,
        "custody_hops": len(batch_record.custody_chain) if batch_record else 0,
        "manufacturer_address": batch_record.manufacturer_address if batch_record else None,
        "double_spend_flag": False
    }

    alert_type = "NORMAL"
    alert_banner = None
    final_verdict = vision_results["verdict"]

    if not batch_record:
        alert_type = "COUNTERFEIT_UNREGISTERED"
        final_verdict = "UNREGISTERED_BATCH_COUNTERFEIT"
        alert_banner = f"CRITICAL: Batch '{resolved_batch_id}' has NO RECORD on the global cryptographic ledger!"
    elif batch_record.status == BatchStatus.DISPENSED:
        # CRITICAL REUSE TRAP!
        blockchain_verification["double_spend_flag"] = True
        blockchain_verification["first_dispensed_at"] = batch_record.dispensed_at
        blockchain_verification["first_dispensed_iso"] = batch_record.dispensed_iso
        blockchain_verification["first_dispensed_location"] = batch_record.dispensation_scanner.get("location") if batch_record.dispensation_scanner else "Unknown Location"
        alert_type = "DUPLICATE_QR_REUSE_ATTEMPT"
        final_verdict = "DUPLICATE_QR_REUSE_ATTEMPT"
        alert_banner = (
            f"FRAUD DETECTED: Cloned/Reused QR Code! "
            f"Original product already dispensed on {batch_record.dispensed_iso} "
            f"at {batch_record.dispensation_scanner.get('location', 'Unknown') if batch_record.dispensation_scanner else 'Dispensary'}."
        )
    elif force_tamper or vision_results["verdict"] == "COUNTERFEIT_PHYSICAL_TAMPER":
        alert_type = "PHYSICAL_TAMPER_INTERCEPTED"
        final_verdict = "COUNTERFEIT_PHYSICAL_TAMPER"
        alert_banner = "TAMPER DETECTED: Low-DPI print reproduction and altered expiry date detected on secondary packaging!"

    execution_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    response_payload = {
        "authenticity_score": vision_results["authenticity_score"],
        "verdict": final_verdict,
        "alert_type": alert_type,
        "alert_banner": alert_banner,
        "print_resolution_dpi": vision_results["print_resolution_dpi"],
        "tampering_index": vision_results["tampering_index"],
        "batch_match": vision_results["batch_match"],
        "latency_ms": execution_latency_ms,
        "vision_forensics": vision_results,
        "blockchain_provenance": blockchain_verification,
        "batch_details": batch_record.to_dict() if batch_record else None,
        "chain_height": len(ledger.chain)
    }

    # Broadcast to HUD via WebSocket
    await broadcast_telemetry("SCAN_COMPLETED", response_payload)

    return JSONResponse(content=response_payload)


@app.post("/api/scenarios/{scenario_id}/trigger")
async def trigger_scenario(scenario_id: str):
    """Instant one-click trigger for judges to test any of the 3 scenarios."""
    matched = next((s for s in scenarios_registry if s["id"] == scenario_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    return await execute_forensic_scan(
        image_base64=matched["image_data"],
        batch_id=matched["batch_id"],
        simulated_text=matched["simulated_text"],
        force_tamper=matched["force_tamper"]
    )


@app.get("/api/ledger/blocks")
def get_ledger_blocks():
    """Returns the live blockchain blocks, Merkle roots, and chain metrics."""
    return ledger.get_chain_state()


@app.post("/api/ledger/dispense")
async def dispense_batch(request: DispenseRequest):
    """Simulates on-chain status transition to DISPENSED."""
    result = ledger.verify_and_dispense(
        batch_id=request.batch_id,
        scanner_metadata=request.scanner_metadata
    )
    await broadcast_telemetry("LEDGER_UPDATED", {"chain_state": ledger.get_chain_state()})
    return result


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """WebSocket feed providing live telemetry of forensic scans and block arrivals."""
    await websocket.accept()
    connected_websockets.append(websocket)
    # Send initial snapshot
    await websocket.send_json({
        "event": "CONNECTED",
        "chain_state": ledger.get_chain_state(),
        "timestamp": time.time()
    })
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


# Mount static frontend directory
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=False)
