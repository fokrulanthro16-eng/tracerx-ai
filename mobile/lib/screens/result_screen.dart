import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> forensicResult;

  const ResultScreen({super.key, required this.forensicResult});

  @override
  Widget build(BuildContext context) {
    final verdict = forensicResult['verdict'] ?? 'UNKNOWN';
    final authIndex = (forensicResult['authenticity_index'] ?? forensicResult['authenticity_score'] ?? 0.0) as num;
    final isDoubleSpend = verdict == 'DUPLICATE_QR_REUSE_ATTEMPT' ||
        forensicResult['on_chain_provenance']?['double_spend_flag'] == true;
    final isCounterfeit = verdict.toString().contains('COUNTERFEIT') || isDoubleSpend || authIndex < 60;
    final gs1 = forensicResult['gs1_metadata'] ?? {};

    final primaryColor = isDoubleSpend || isCounterfeit ? const Color(0xFFFF0055) : const Color(0xFF00FF9D);

    return Scaffold(
      backgroundColor: const Color(0xFF06090E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0C1322),
        title: const Text(
          "VERIFICATION DOSSIER",
          style: TextStyle(fontFamily: 'monospace', fontSize: 15, fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 1. Critical Alarm Banner if Fraud or Double Spend
            if (isDoubleSpend)
              Container(
                margin: const EdgeInsets.bottom(16),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFFF0055).withOpacity(0.18),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFFF0055), width: 1.5),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber_rounded, color: Color(0xFFFF0055), size: 30),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "DUPLICATE QR REUSE DETECTED",
                            style: TextStyle(color: Color(0xFFFF0055), fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            forensicResult['alert_banner'] ??
                                "CRITICAL: Cloned QR code! Product was already dispensed on Sep 5, 2026 at Square Hospital, Dhaka.",
                            style: const TextStyle(color: Colors.white70, fontSize: 11, fontFamily: 'monospace'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

            // 2. Main Authenticity Dial Box
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF0C1322),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: primaryColor.withOpacity(0.4)),
              ),
              child: Column(
                children: [
                  Text(
                    verdict,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      color: primaryColor,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 110,
                        height: 110,
                        child: CircularProgressIndicator(
                          value: (authIndex / 100.0).clamp(0.01, 1.0),
                          strokeWidth: 8,
                          backgroundColor: Colors.white10,
                          valueColor: AlwaysStoppedAnimation<Color>(primaryColor),
                        ),
                      ),
                      Column(
                        children: [
                          Text(
                            "${authIndex.toStringAsFixed(1)}%",
                            style: TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: primaryColor,
                            ),
                          ),
                          const Text(
                            "CONFIDENCE",
                            style: TextStyle(color: Colors.white54, fontSize: 9, fontFamily: 'monospace'),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _metricCol("PRINT DPI", "${forensicResult['print_resolution_dpi'] ?? 600}"),
                      _metricCol("TAMPER PROB", "${forensicResult['tamper_probability'] ?? 0.02}"),
                      _metricCol("NETWORK", "Polygon Amoy"),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 3. GS1 Application Identifier Breakdown
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0C1322),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "GS1 DATAMATRIX APPLICATION IDENTIFIERS",
                    style: TextStyle(
                      color: Color(0xFF00F0FF),
                      fontFamily: 'monospace',
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Divider(color: Colors.white12, height: 16),
                  _infoRow("(01) GTIN", gs1['gtin'] ?? '00300019920148'),
                  _infoRow("(10) BATCH / LOT", gs1['batch_lot'] ?? 'PZ-2026-X99'),
                  _infoRow("(17) EXPIRATION", gs1['expiry_date'] ?? '2028-03-01'),
                  _infoRow("(21) SERIAL NO", gs1['serial_number'] ?? 'SN-PFZ-990142'),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 4. Action Buttons
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1E293B),
                foregroundColor: Colors.white,
                minimumSize: const Size.fromHeight(46),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text(
                "SCAN NEXT PACKAGE",
                style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricCol(String title, String val) {
    return Column(
      children: [
        Text(title, style: const TextStyle(color: Colors.white38, fontSize: 9, fontFamily: 'monospace')),
        const SizedBox(height: 2),
        Text(val, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
      ],
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 11, fontFamily: 'monospace')),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
        ],
      ),
    );
  }
}
