# TraceRx AI — Autonomous Pharmaceutical Vision Forensics & Cryptographic Provenance Engine

> **UPAI-Hackdays 2026 Submission**  
> **Track:** AI + Blockchain  
> **Tagline:** Dual-layered defense against the \$200B counterfeit pharmaceutical crisis combining multi-spectral computer vision heuristics with an immutable SHA-256 Merkle provenance ledger.

---

## 💡 The Problem: A Fatal \$200B Global Threat
According to the World Health Organization (WHO), over **1 in 10 medical products** in low- and middle-income countries are substandard or falsified, causing an estimated **1,000,000 preventable deaths annually** and exceeding **\$200 billion in illicit trade**. 

Current anti-counterfeit measures fail due to two fundamental architectural vulnerabilities:
1. **Blind Serialization & QR Reuse (Double-Spend Fraud):** Counterfeit cartels purchase genuine drug packages, duplicate the packaging QR code onto thousands of fake chalk pills or diluted vials, and distribute them. Standard scanners read the QR code, verify it exists in a database, and deem it "authentic".
2. **Physical Packaging Alteration:** Re-labeling expired drugs with fake expiration dates and poor deskjet printing goes undetected by human pharmacists under heavy clinic workloads.

---

## ⚡ The Solution: TraceRx AI
**TraceRx AI** solves this through a unified **AI + Cryptographic Provenance Engine** operating 100% locally with zero external API dependencies:

1. **Multi-Spectral Vision Forensics (Computer Vision Layer):**
   - **Micro-Print Integrity Analysis:** Uses Laplacian gradient variance and high-frequency edge transition density to determine packaging resolution (distinguishing 600+ DPI factory packaging from degraded 150-200 DPI inkjet counterfeits).
   - **Diffractive OVD Hologram Refraction:** Analyzes chromatic saturation dispersion and specular highlight reflections to differentiate iridescent diffraction security coatings from flat photocopies.
   - **Contour & Tampering Heuristics:** Detects morphological anomalies, altered expiry date stickers, and packaging scratches.

2. **Immutable EVM/SHA-256 Merkle Provenance Ledger (Blockchain Layer):**
   - Tracks pharmaceutical batches across an audited chain of custody: `MANUFACTURED -> IN_TRANSIT -> RECEIVED_AT_PHARMACY -> DISPENSED -> REVOKED`.
   - Generates deterministic Merkle trees with cryptographic proofs for every transaction block.
   - **Anti-Counterfeit Double-Dispense Trap:** Once a batch is dispensed to a patient, any future scan of that cloned QR code instantly trips an alarm (`DUPLICATE_QR_REUSE_ATTEMPT`), displaying the exact timestamp, scanner ID, and hospital location of the original dispensation.

---

## 🖥️ Cyber-Medical Dark HUD Dashboard
TraceRx AI delivers a military-grade Cyber-Medical Telemetry HUD designed for high-stress hospital dispensaries, customs checkpoints, and field clinics:
- **Real-Time Forensic Gauges:** Radial dials for Authenticity Score (0-100%), Micro-Print DPI, and Tampering Index.
- **Visual Viewport Canvas:** Interactive bounding box overlays showing detected security zones.
- **Webcam & Drag-and-Drop Ingestion:** Support for live optical scanning or high-res file uploads.
- **Live Merkle Block Feed:** Real-time visualization of block creation, Merkle roots, gas consumed, and custody checkpoints.
- **Threat Interception Alarm:** Flashing crimson HUD banner that halts dispensation when fraud or tampering is caught.

---

## 🏆 3 Pre-Seeded Judge Scenarios
Judges can evaluate the system in under 60 seconds using the quick-trigger scenario buttons:
1. **Scenario 1 (Genuine):** Pfizer Remdesivir (`PZ-2026-X99`) — Genuine packaging, 600 DPI microprint, iridescent diffraction OVD, active custody chain. **Verdict: GENUINE_AUTHENTIC (99.4%)**.
2. **Scenario 2 (Counterfeit QR Reuse):** GSK Amoxicillin (`GSK-8812-D`) — Authentic packaging, but on-chain ledger halts dispensation: intercepted as already dispensed on Sep 5, 2026 at Square Hospital, Dhaka! **Verdict: DUPLICATE_QR_REUSE_ATTEMPT**.
3. **Scenario 3 (Physical Tampering):** Sanofi Insulin (`SN-3310-F`) — Altered expiry sticker (2026-08 changed to 2029-12), degraded 190 DPI edge blur, non-reflective matte photocopy. **Verdict: COUNTERFEIT_PHYSICAL_TAMPER (14.2%)**.

---

## 🚀 Performance Benchmarks
Tested over **500 concurrent scans** (`tests/benchmark_suite.py`):
- **Mean Pipeline Latency:** **11.73 ms** (Well below the sub-20ms target!)
- **95th Percentile (p95):** **12.91 ms**
- **Throughput:** **169.8 scans/second** on standard commodity CPU.
- **Cloud Dependency:** **0%** (100% self-hosted, offline-ready).

---

## 🛠️ How We Built It
- **Backend:** FastAPI (Python 3.11/3.14), Uvicorn ASGI, WebSockets, Pydantic v2.
- **Vision Engine:** OpenCV Headless, Pillow, NumPy.
- **Cryptographic Ledger:** Python SHA-256 Merkle Tree, HMAC-SHA256 digital signatures, Proof-of-Authority consensus emulator.
- **Frontend HUD:** HTML5 Canvas, Tailwind CSS, Lucide Icons, Cyberpunk tactical medical styling.
- **Testing & Quality:** Pytest, GitHub Actions CI, Docker, Docker Compose.

---

## 👥 What's Next for TraceRx AI
- Integration with mobile edge devices (Android/iOS offline SDK).
- Zero-Knowledge proofs (zk-SNARKs) allowing manufacturers to prove batch authenticity without revealing sensitive supply chain trade secrets.
- Integration with GS1 Digital Link standards and national pharmaceutical serialization registries.
