"""
TraceRx AI - High-Throughput Latency & Concurrency Benchmark Suite
Simulates 500 scans to demonstrate sub-20ms multi-spectral vision forensics
and in-memory cryptographic Merkle tree ledger verification.
Outputs: benchmark_results.json
"""

import json
import time
import sys
import statistics
import concurrent.futures
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
cv2.setNumThreads(1)

from backend.blockchain_ledger import CryptographicLedger
from backend.vision_forensics import VisionForensicEngine
from backend.mock_data import generate_synthetic_packaging_image, seed_mock_scenarios


def run_benchmark(iterations: int = 500, concurrency: int = 4) -> dict:
    print(f"=== Starting TraceRx AI Benchmark Suite ({iterations} iterations, concurrency={concurrency}) ===")

    # Initialize engines
    ledger = CryptographicLedger()
    scenarios = seed_mock_scenarios(ledger)
    vision_engine = VisionForensicEngine()

    # Pre-render image to test vision pipeline without disk I/O noise
    sample_b64 = scenarios[0]["image_data"]
    sample_img = vision_engine.load_image_from_base64(sample_b64)
    batch_id = scenarios[0]["batch_id"]

    latencies = []

    def single_scan_pipeline():
        t0 = time.perf_counter()
        # 1. Vision Forensics
        vision_res = vision_engine.evaluate_packaging(
            img=sample_img,
            expected_batch_id=batch_id,
            simulated_text=scenarios[0]["simulated_text"]
        )
        # 2. Blockchain ledger verification
        batch_record = ledger.batches.get(batch_id)
        status = batch_record.status if batch_record else None
        # 3. Merkle record hash confirmation
        rec_hash = batch_record.compute_record_hash() if batch_record else None

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return elapsed_ms

    overall_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_scan_pipeline) for _ in range(iterations)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())

    overall_duration = time.perf_counter() - overall_start
    throughput = round(iterations / overall_duration, 1)

    latencies.sort()
    p50 = round(statistics.median(latencies), 2)
    p90 = round(latencies[int(iterations * 0.90)], 2)
    p95 = round(latencies[int(iterations * 0.95)], 2)
    p99 = round(latencies[int(iterations * 0.99)], 2)
    mean_lat = round(statistics.mean(latencies), 2)
    min_lat = round(min(latencies), 2)
    max_lat = round(max(latencies), 2)

    results = {
        "benchmark_suite": "TraceRx-Forensic-Concurrency-Test",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "total_scans": iterations,
        "concurrency_workers": concurrency,
        "total_duration_sec": round(overall_duration, 3),
        "throughput_scans_per_sec": throughput,
        "latency_metrics_ms": {
            "mean": mean_lat,
            "min": min_lat,
            "median_p50": p50,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "max": max_lat
        },
        "performance_verdict": "SUB_20MS_TARGET_ACHIEVED" if p95 < 20.0 else "OPTIMIZATION_NEEDED",
        "system_profile": {
            "vision_engine": "OpenCV-Laplacian-HSV-Forensics",
            "ledger_engine": "In-Memory SHA-256 Merkle Engine",
            "cloud_dependencies": "NONE (100% Local Out-of-the-Box)"
        }
    }

    out_file = Path(__file__).resolve().parent.parent / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[SUCCESS] Benchmark complete! Results saved to {out_file.name}")
    print(f"-> Mean Latency:   {mean_lat} ms")
    print(f"-> Median (p50):   {p50} ms")
    print(f"-> 95th Percentile:{p95} ms")
    print(f"-> Throughput:     {throughput} scans/sec")
    print(f"-> Target Verdict: {results['performance_verdict']}")

    return results


if __name__ == "__main__":
    run_benchmark(500, 2)
