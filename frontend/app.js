/**
 * TraceRx AI - Cyber-Medical HUD Front-End Application Logic
 * Manages video streaming, canvas bounding boxes, scenario switches, and live blockchain sync.
 */

// State
let currentScenarios = [];
let activeScenarioId = "scenario-1";
let currentImageData = null;
let isWebcamRunning = false;
let webcamStream = null;
let telemetrySocket = null;

// DOM Elements
const previewImage = document.getElementById("preview-image");
const dropzonePlaceholder = document.getElementById("dropzone-placeholder");
const fileInput = document.getElementById("file-input");
const overlayCanvas = document.getElementById("overlay-canvas");
const scannerLaser = document.getElementById("scanner-laser");
const webcamVideo = document.getElementById("webcam-video");
const toggleCameraBtn = document.getElementById("toggle-camera-btn");
const scanNowBtn = document.getElementById("scan-now-btn");
const inputBatchId = document.getElementById("input-batch-id");
const inputOcrText = document.getElementById("input-ocr-text");
const checkForceTamper = document.getElementById("check-force-tamper");

// Telemetry & Gauges
const valAuthenticity = document.getElementById("val-authenticity");
const valDpi = document.getElementById("val-dpi");
const valTamper = document.getElementById("val-tamper");
const verdictPill = document.getElementById("verdict-pill");
const itemMicroprint = document.getElementById("item-microprint");
const itemHologram = document.getElementById("item-hologram");
const itemBatchMatch = document.getElementById("item-batch-match");
const itemLatency = document.getElementById("item-latency");

// Ledger Dossier
const dossierDrug = document.getElementById("dossier-drug");
const dossierBatch = document.getElementById("dossier-batch");
const dossierStatus = document.getElementById("dossier-status");
const dossierMfgAddr = document.getElementById("dossier-mfg-addr");
const dossierRecordHash = document.getElementById("dossier-record-hash");
const custodyTimeline = document.getElementById("custody-timeline");
const blocksStream = document.getElementById("blocks-stream");
const totalGasEl = document.getElementById("total-gas");
const telemetryBlockHeight = document.getElementById("telemetry-block-height");
const telemetryLatency = document.getElementById("telemetry-latency");
const btnDispenseAction = document.getElementById("btn-dispense-action");

// Alarm Banner
const alarmBanner = document.getElementById("alarm-banner");
const alarmTitle = document.getElementById("alarm-title");
const alarmMessage = document.getElementById("alarm-message");

// Initialize icons and load initial scenarios
window.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
  setupEventListeners();
  initGauges(99.4, 600, 0.02);
  await fetchScenarios();
  await refreshLedgerBlocks();
  initWebSocket();
});

// Setup UI Event Listeners
function setupEventListeners() {
  // Scenario Buttons
  document.getElementById("btn-scenario-1").addEventListener("click", () => activateScenario("scenario-1"));
  document.getElementById("btn-scenario-2").addEventListener("click", () => activateScenario("scenario-2"));
  document.getElementById("btn-scenario-3").addEventListener("click", () => activateScenario("scenario-3"));

  // File Upload & Drag-and-Drop
  dropzonePlaceholder.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", handleFileSelect);

  const dropArea = previewImage.parentElement;
  ['dragenter', 'dragover'].forEach(name => {
    dropArea.addEventListener(name, (e) => {
      e.preventDefault();
      dropArea.classList.add("border-cyan-400");
    }, false);
  });
  ['dragleave', 'drop'].forEach(name => {
    dropArea.addEventListener(name, (e) => {
      e.preventDefault();
      dropArea.classList.remove("border-cyan-400");
    }, false);
  });
  dropArea.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      loadCustomFile(files[0]);
    }
  });

  // Camera Toggle
  toggleCameraBtn.addEventListener("click", toggleWebcam);

  // Manual Scan
  scanNowBtn.addEventListener("click", () => triggerActiveScan());

  // Dispense Button
  btnDispenseAction.addEventListener("click", async () => {
    const batchId = inputBatchId.value.trim();
    if (!batchId) return;
    try {
      const res = await fetch("/api/ledger/dispense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batch_id: batchId })
      });
      const data = await res.json();
      if (!data.success && data.alert === "DUPLICATE_QR_REUSE_ATTEMPT") {
        showAlarm("DUPLICATE QR REUSE ATTEMPT DETECTED", data.message);
      } else if (data.success) {
        dismissAlarm();
      }
      await refreshLedgerBlocks();
      await triggerActiveScan();
    } catch (err) {
      console.error("Dispense error:", err);
    }
  });
}

// Fetch Pre-seeded Scenarios from Backend
async function fetchScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    const json = await res.json();
    currentScenarios = json.scenarios || [];
    if (currentScenarios.length > 0) {
      activateScenario("scenario-1");
    }
  } catch (err) {
    console.error("Failed to load scenarios:", err);
  }
}

// Activate one of the 3 canonical judge scenarios
async function activateScenario(scenarioId) {
  activeScenarioId = scenarioId;
  const s = currentScenarios.find(sc => sc.id === scenarioId);
  if (!s) return;

  // Stop camera if running
  if (isWebcamRunning) stopWebcam();

  // Populate inputs
  inputBatchId.value = s.batch_id;
  inputOcrText.value = s.simulated_text || `BATCH: ${s.batch_id} EXP: 2028-03`;
  checkForceTamper.checked = s.force_tamper || false;

  // Update Preview Image
  currentImageData = s.image_data;
  previewImage.src = s.image_data;
  previewImage.classList.remove("hidden");
  dropzonePlaceholder.classList.add("hidden");

  // Run immediate scan on this scenario
  await triggerActiveScan();
}

// Handle File Selection
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) {
    loadCustomFile(file);
  }
}

function loadCustomFile(file) {
  if (isWebcamRunning) stopWebcam();
  const reader = new FileReader();
  reader.onload = (event) => {
    currentImageData = event.target.result;
    previewImage.src = currentImageData;
    previewImage.classList.remove("hidden");
    dropzonePlaceholder.classList.add("hidden");
    triggerActiveScan();
  };
  reader.readAsDataURL(file);
}

// Webcam Toggle
async function toggleWebcam() {
  if (isWebcamRunning) {
    stopWebcam();
  } else {
    try {
      webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      webcamVideo.srcObject = webcamStream;
      webcamVideo.classList.remove("hidden");
      previewImage.classList.add("hidden");
      dropzonePlaceholder.classList.add("hidden");
      document.getElementById("camera-btn-text").textContent = "Stop Camera";
      isWebcamRunning = true;
    } catch (err) {
      alert("Unable to access camera: " + err.message + "\nUsing synthetic test scans.");
    }
  }
}

function stopWebcam() {
  if (webcamStream) {
    webcamStream.getTracks().forEach(t => t.stop());
    webcamStream = null;
  }
  webcamVideo.classList.add("hidden");
  previewImage.classList.remove("hidden");
  document.getElementById("camera-btn-text").textContent = "Webcam Feed";
  isWebcamRunning = false;
}

// Capture Snapshot from Camera if Active
function captureSnapshot() {
  if (!isWebcamRunning) return currentImageData;
  const offscreen = document.createElement("canvas");
  offscreen.width = webcamVideo.videoWidth || 640;
  offscreen.height = webcamVideo.videoHeight || 480;
  const ctx = offscreen.getContext("2d");
  ctx.drawImage(webcamVideo, 0, 0, offscreen.width, offscreen.height);
  return offscreen.toDataURL("image/jpeg", 0.9);
}

// Trigger Forensic Scan
async function triggerActiveScan() {
  scannerLaser.classList.remove("hidden");
  const t0 = performance.now();

  const imgData = captureSnapshot() || currentImageData;
  const batchId = inputBatchId.value.trim();
  const simulatedText = inputOcrText.value.trim();
  const forceTamper = checkForceTamper.checked;

  const formData = new FormData();
  if (imgData) formData.append("image_base64", imgData);
  formData.append("batch_id", batchId);
  formData.append("simulated_text", simulatedText);
  formData.append("force_tamper", forceTamper ? "true" : "false");

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    const elapsed = Math.round(performance.now() - t0);

    applyScanResults(result, elapsed);
  } catch (err) {
    console.error("Scan error:", err);
  } finally {
    setTimeout(() => {
      scannerLaser.classList.add("hidden");
    }, 400);
  }
}

// Apply and Render Scan Results
function applyScanResults(result, localLatency) {
  const authScore = result.authenticity_score;
  const dpi = result.print_resolution_dpi;
  const tamperIdx = result.tampering_index;
  const verdict = result.verdict;

  // Update Gauges
  updateGauges(authScore, dpi, tamperIdx);

  // Verdict Pill
  verdictPill.textContent = verdict;
  if (verdict === "GENUINE_AUTHENTIC") {
    verdictPill.className = "px-2.5 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
  } else if (verdict.includes("REUSE") || verdict.includes("COUNTERFEIT") || verdict.includes("TAMPER")) {
    verdictPill.className = "px-2.5 py-0.5 rounded text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40";
  } else {
    verdictPill.className = "px-2.5 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40";
  }

  // Itemized Metrics
  const micro = result.vision_forensics?.details?.microprint;
  const holo = result.vision_forensics?.details?.hologram;
  itemMicroprint.textContent = micro?.microprint_status || "CRISP (HIGH RES)";
  itemMicroprint.className = (micro?.estimated_dpi >= 450) ? "font-semibold text-emerald-400" : "font-semibold text-rose-400";

  itemHologram.textContent = `${holo?.refraction_verdict || 'DIFFRACTIVE'} (${holo?.hologram_score || 90})`;
  itemHologram.className = (holo?.hologram_score >= 65) ? "font-semibold text-cyan-400" : "font-semibold text-amber-400";

  itemBatchMatch.textContent = result.batch_match ? "MATCHED ON-CHAIN" : "MISMATCH / ALTERED";
  itemBatchMatch.className = result.batch_match ? "font-semibold text-emerald-400" : "font-semibold text-rose-400";

  const totalLat = result.latency_ms || localLatency;
  itemLatency.textContent = `${totalLat} ms`;
  telemetryLatency.textContent = `< ${Math.max(8, totalLat)}ms`;

  // Alarm Banner Handling
  if (result.alert_type && result.alert_type !== "NORMAL" && result.alert_banner) {
    showAlarm(result.alert_type.replace(/_/g, " "), result.alert_banner);
  } else {
    dismissAlarm();
  }

  // Dossier & Provenance
  const batch = result.batch_details;
  if (batch) {
    dossierDrug.textContent = batch.drug_name;
    dossierBatch.textContent = batch.batch_id;
    dossierStatus.textContent = batch.status;
    dossierMfgAddr.textContent = batch.manufacturer_address;
    dossierRecordHash.textContent = batch.record_hash;

    // Status styling
    if (batch.status === "DISPENSED") {
      dossierStatus.className = "font-bold text-amber-400";
    } else if (batch.status === "RECEIVED_AT_PHARMACY") {
      dossierStatus.className = "font-bold text-emerald-400";
    } else {
      dossierStatus.className = "font-bold text-cyan-400";
    }

    renderCustodyTimeline(batch.custody_chain || []);
  }

  // Bounding Boxes on Canvas
  const boxes = result.vision_forensics?.details?.metadata?.bounding_boxes || [];
  drawBoundingBoxes(boxes, verdict);
}

// Draw Bounding Boxes on Overlay Canvas
function drawBoundingBoxes(boxes, verdict) {
  const canvas = overlayCanvas;
  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!boxes || boxes.length === 0) {
    // Draw standard scanning brackets
    const pad = 24;
    ctx.strokeStyle = (verdict === "GENUINE_AUTHENTIC") ? "#00ff9d" : "#ff0055";
    ctx.lineWidth = 2;
    // Corners
    ctx.strokeRect(pad, pad, canvas.width - pad * 2, canvas.height - pad * 2);
    return;
  }

  const scaleX = canvas.width / 640;
  const scaleY = canvas.height / 420;

  boxes.forEach((b, idx) => {
    const x = b.x * scaleX;
    const y = b.y * scaleY;
    const w = b.w * scaleX;
    const h = b.h * scaleY;

    ctx.strokeStyle = (idx === 0) ? "#00f0ff" : "#00ff9d";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);

    // Label tag
    ctx.fillStyle = "rgba(12, 18, 29, 0.85)";
    ctx.fillRect(x, Math.max(0, y - 16), 80, 15);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = "10px monospace";
    ctx.fillText(`ZONE #${idx + 1}`, x + 4, Math.max(10, y - 4));
  });
}

// Render Custody Timeline
function renderCustodyTimeline(chain) {
  custodyTimeline.innerHTML = "";
  if (!chain || chain.length === 0) {
    custodyTimeline.innerHTML = `<div class="text-slate-500 text-center py-2">No custody checkpoints recorded.</div>`;
    return;
  }

  chain.forEach((cp, idx) => {
    const isLast = idx === chain.length - 1;
    const item = document.createElement("div");
    item.className = "flex items-start space-x-2 text-[11px] font-mono border-l-2 border-cyan-500/40 pl-3 pb-2 relative";

    const dotColor = isLast ? "bg-emerald-400" : "bg-cyan-400";
    item.innerHTML = `
      <span class="absolute -left-[5px] top-1 w-2 h-2 rounded-full ${dotColor}"></span>
      <div class="flex-1 bg-slate-900/60 p-1.5 rounded border border-slate-800">
        <div class="flex items-center justify-between">
          <span class="font-bold text-cyan-300">${cp.entity}</span>
          <span class="text-[10px] text-slate-500">${cp.iso_time ? cp.iso_time.split('T')[0] : '2026-09-08'}</span>
        </div>
        <div class="text-slate-400 text-[10px] mt-0.5">${cp.location}</div>
        <div class="text-slate-500 text-[9px] truncate mt-0.5">SIG: ${cp.signature || '0x...'}</div>
      </div>
    `;
    custodyTimeline.appendChild(item);
  });
}

// Refresh Blockchain Ledger Block Feed
async function refreshLedgerBlocks() {
  try {
    const res = await fetch("/api/ledger/blocks");
    const data = await res.json();
    totalGasEl.textContent = Number(data.total_gas_consumed).toLocaleString();
    telemetryBlockHeight.textContent = `Block #${data.block_height}`;

    blocksStream.innerHTML = "";
    (data.blocks || []).forEach(b => {
      const blockEl = document.createElement("div");
      blockEl.className = "bg-slate-900/90 p-2 rounded border border-slate-800/90 hover:border-cyan-500/40 transition";
      const txCount = b.transactions ? b.transactions.length : 0;
      const txSummary = b.transactions && b.transactions[0] ? b.transactions[0].type : "TX";

      blockEl.innerHTML = `
        <div class="flex items-center justify-between text-cyan-400 font-bold">
          <span>BLOCK #${b.index}</span>
          <span class="text-[10px] text-slate-400">${b.iso_time}</span>
        </div>
        <div class="text-[10px] text-slate-400 truncate mt-0.5">HASH: <span class="text-slate-300">${b.hash}</span></div>
        <div class="text-[10px] text-slate-500 truncate">MERKLE: <span class="text-cyan-500">${b.merkle_root}</span></div>
        <div class="flex items-center justify-between text-[10px] text-slate-400 mt-1 pt-1 border-t border-slate-800">
          <span class="text-emerald-400 font-semibold">${txSummary} (${txCount} tx)</span>
          <span class="text-amber-400">${b.gas_consumed} gas</span>
        </div>
      `;
      blocksStream.appendChild(blockEl);
    });
  } catch (err) {
    console.error("Failed to load blocks:", err);
  }
}

// Alarm Banner Management
function showAlarm(title, message) {
  alarmBanner.classList.remove("hidden");
  alarmTitle.textContent = title;
  alarmMessage.textContent = message;
}

function dismissAlarm() {
  alarmBanner.classList.add("hidden");
}

// WebSocket Live Telemetry
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
  try {
    telemetrySocket = new WebSocket(wsUrl);
    telemetrySocket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.event === "SCAN_COMPLETED") {
        refreshLedgerBlocks();
      } else if (msg.event === "LEDGER_UPDATED") {
        refreshLedgerBlocks();
      }
    };
    telemetrySocket.onclose = () => {
      setTimeout(initWebSocket, 3000);
    };
  } catch (e) {
    console.warn("WebSocket not available, falling back to polling.");
  }
}

// Gauges Canvas Rendering
function initGauges(auth, dpi, tamper) {
  drawRadialGauge("gauge-authenticity", auth / 100.0, "#00ff9d", "#ff0055");
  drawRadialGauge("gauge-dpi", Math.min(1.0, dpi / 600.0), "#00f0ff", "#ffb800");
  drawRadialGauge("gauge-tamper", tamper, "#ff0055", "#00ff9d", true);
}

function updateGauges(auth, dpi, tamper) {
  valAuthenticity.textContent = `${auth}%`;
  valAuthenticity.className = (auth >= 88.0) ? "text-xl font-bold font-mono text-emerald-400" : "text-xl font-bold font-mono text-rose-400";

  valDpi.textContent = `${dpi}`;
  valDpi.className = (dpi >= 450) ? "text-xl font-bold font-mono text-cyan-400" : "text-xl font-bold font-mono text-rose-400";

  valTamper.textContent = `${tamper}`;
  valTamper.className = (tamper <= 0.20) ? "text-xl font-bold font-mono text-emerald-400" : "text-xl font-bold font-mono text-rose-400";

  drawRadialGauge("gauge-authenticity", auth / 100.0, "#00ff9d", "#ff0055");
  drawRadialGauge("gauge-dpi", Math.min(1.0, dpi / 600.0), "#00f0ff", "#ffb800");
  drawRadialGauge("gauge-tamper", tamper, "#ff0055", "#00ff9d", true);
}

function drawRadialGauge(canvasId, value, primaryColor, altColor, invert = false) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const radius = w / 2 - 8;

  ctx.clearRect(0, 0, w, h);

  // Background ring
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, radius, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(30, 41, 59, 0.7)";
  ctx.lineWidth = 7;
  ctx.stroke();

  // Active ring
  const startAngle = -Math.PI / 2;
  const endAngle = startAngle + (Math.PI * 2 * Math.max(0.01, Math.min(1.0, value)));

  ctx.beginPath();
  ctx.arc(w / 2, h / 2, radius, startAngle, endAngle);
  const color = invert ? (value > 0.25 ? primaryColor : altColor) : (value >= 0.75 ? primaryColor : altColor);
  ctx.strokeStyle = color;
  ctx.lineWidth = 7;
  ctx.lineCap = "round";
  ctx.shadowColor = color;
  ctx.shadowBlur = 8;
  ctx.stroke();
  ctx.shadowBlur = 0;
}
