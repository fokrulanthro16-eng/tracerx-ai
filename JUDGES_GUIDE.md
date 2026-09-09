# TraceRx AI — 60-Second Judges' Evaluation Guide

Welcome Judges! This guide walks you through verifying **TraceRx AI** in under **60 seconds**, showcasing the dual-layer defense: **Multi-Spectral Vision Forensics** + **Cryptographic Merkle Provenance Ledger**.

---

## 🚀 1. Quick Launch (Zero Configuration)

### Option A: Local Python
```bash
cd tracerx-ai
python -m uvicorn backend.main:app --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

### Option B: Docker Compose
```bash
docker compose up --build
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🎯 2. The 3 One-Click Evaluation Scenarios

At the top of the HUD dashboard, click the **Judge Evaluation Suite** buttons:

### 🟢 Test 1: Click `[1: Genuine Pfizer Drug]`
- **What happens:** Ingests genuine Pfizer Remdesivir packaging (`PZ-2026-X99`).
- **Observe the Gauges:**
  - Authenticity Index: **~99.4% (Confidence: VERIFIED)**
  - Micro-Print DPI: **600 DPI (High-Resolution Crisp)**
  - Tampering Index: **0.02 (Tampering Clean)**
- **Observe Provenance Explorer (Right Side):**
  - Provenance Status: **RECEIVED_AT_PHARMACY**
  - Unbroken custody timeline: *Pfizer BioTech -> DHL Cryo Logistics -> St. Thomas Central Pharmacy*.
  - Click **[DISPENSE TO PATIENT]**: The transaction commits a new Merkle block and transitions status to **DISPENSED**.

---

### 🔴 Test 2: Click `[2: Counterfeit QR Reuse Trap]`
- **What happens:** Ingests GSK Amoxicillin (`GSK-8812-D`). The packaging visually appears authentic (cloned QR code).
- **The Interception:**
  - A flashing crimson alarm banner triggers across the top:
    > **FRAUD DETECTED: Cloned/Reused QR Code!**  
    > *Original product already dispensed on Sep 5, 2026 at Square Hospital Dispensary, Panthapath, Dhaka.*
  - **Verdict:** `DUPLICATE_QR_REUSE_ATTEMPT`
  - Demonstrates why computer vision alone is insufficient and how the immutable Merkle ledger prevents the double-spend of genuine serialization codes!

---

### 🟠 Test 3: Click `[3: Tampered Packaging Alert]`
- **What happens:** Ingests Sanofi Insulin (`SN-3310-F`). Counterfeiters relabeled an expired 2026 batch with an altered "2029-12" expiry sticker and photocopied packaging.
- **The Forensic Detection:**
  - Micro-Print DPI drops to **~210 DPI (Degraded Blur)**.
  - Hologram Refraction drops to **MATTE_FLAT_SURFACE** (photocopy detected).
  - Tampering Index jumps to **0.88**.
  - Authenticity Score crashes to **14.2%**.
  - **Verdict:** `COUNTERFEIT_PHYSICAL_TAMPER`.
  - Red alarm banner halts dispensation immediately.

---

## 🔬 3. Verify Live Blockchain & Latency Benchmarks

1. **Verify Live Blockchain Explorer (Bottom Right):**
   - Note the **Live Merkle Block Feed** continuously updating block hashes (`0x...`), Merkle roots, nonces, and gas consumed.
   - Live telemetry in the header displays **LATENCY: < 14ms**.

2. **Verify Automated Unit Tests (10/10 Green):**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Verify Concurrency Benchmark (500 Scans, Sub-20ms):**
   ```bash
   python tests/benchmark_suite.py
   ```
   Inspect `benchmark_results.json` showing mean latency of **~11.7 ms** and throughput of **> 160 scans/sec**.

---

## 🏅 Hackathon Track Alignment Check
| Criteria | TraceRx AI Implementation |
| :--- | :--- |
| **AI Innovation** | Multi-spectral OpenCV heuristics: Laplacian microprint variance, diffractive OVD saturation dispersion, morphological tamper detection. |
| **Blockchain Utility** | Deterministic SHA-256 Merkle trees, EVM-compatible addresses, audited custody chains, cryptographic anti-double-spend traps. |
| **Real-World Impact** | Solves the \$200B WHO counterfeit crisis and prevents fatal patient poisoning. |
| **Self-Contained** | Zero external paid APIs, runs 100% offline in hospital clinics. |
