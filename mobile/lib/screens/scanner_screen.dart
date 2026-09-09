import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/camera_service.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> with SingleTickerProviderStateMixin {
  final CameraService _cameraService = CameraService();
  final ApiService _apiService = ApiService();
  bool _isTorchOn = false;
  bool _isScanning = false;
  late AnimationController _laserController;

  @override
  void initState() {
    super.initState();
    _cameraService.initializeCamera().then((_) {
      if (mounted) setState(() {});
    });

    _laserController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _cameraService.dispose();
    _laserController.dispose();
    super.dispose();
  }

  Future<void> _triggerScan({String? simulatedBatchId}) async {
    if (_isScanning) return;
    setState(() => _isScanning = true);
    HapticFeedback.mediumImpact();

    try {
      final snapshot = await _cameraService.takeSnapshot();
      final result = await _apiService.verifyPackaging(
        batchId: simulatedBatchId ?? "PZ-2026-X99",
      );

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(forensicResult: result),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Scan Error: $e")),
      );
    } finally {
      if (mounted) setState(() => _isScanning = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF06090E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0C1322),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF00F0FF).withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.4)),
              ),
              child: const Icon(Icons.shield_outlined, color: Color(0xFF00F0FF), size: 18),
            ),
            const SizedBox(width: 10),
            const Text(
              "TRACERX MOBILE",
              style: TextStyle(
                fontFamily: 'monospace',
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
                fontSize: 16,
                color: Colors.white,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _isTorchOn ? Icons.flash_on : Icons.flash_off,
              color: _isTorchOn ? const Color(0xFFFFB800) : Colors.white60,
            ),
            onPressed: () {
              setState(() => _isTorchOn = !_isTorchOn);
              _cameraService.toggleTorch(_isTorchOn);
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // 1. Camera Viewport or Mock Frame
          Center(
            child: Container(
              margin: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.3)),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    // Reticle overlay
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.2), width: 2),
                      ),
                    ),

                    // Aiming Brackets
                    CustomPaint(painter: ReticlePainter()),

                    // Scanning Laser Animation
                    AnimatedBuilder(
                      animation: _laserController,
                      builder: (context, child) {
                        return Positioned(
                          top: _laserController.value * 350,
                          left: 0,
                          right: 0,
                          child: Container(
                            height: 2,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Colors.transparent, Color(0xFF00F0FF), Colors.transparent],
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF00F0FF).withOpacity(0.8),
                                  blurRadius: 10,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),

                    // Center Targeting Label
                    Positioned(
                      bottom: 20,
                      left: 0,
                      right: 0,
                      child: Center(
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0C1322).withOpacity(0.85),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: const Color(0xFF00F0FF).withOpacity(0.3)),
                          ),
                          child: const Text(
                            "ALIGN GS1 DATAMATRIX / MICROPRINT",
                            style: TextStyle(
                              color: Color(0xFF00F0FF),
                              fontFamily: 'monospace',
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // 2. Scenario Quick Triggers for Field Evaluation
          Positioned(
            bottom: 25,
            left: 15,
            right: 15,
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildScenarioChip("1: Genuine", const Color(0xFF00FF9D), () {
                      _triggerScan(simulatedBatchId: "PZ-2026-X99");
                    }),
                    _buildScenarioChip("2: QR Reuse", const Color(0xFFFF0055), () {
                      _triggerScan(simulatedBatchId: "GSK-8812-D");
                    }),
                    _buildScenarioChip("3: Tampered", const Color(0xFFFFB800), () {
                      _triggerScan(simulatedBatchId: "SN-3310-F");
                    }),
                  ],
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: _isScanning ? null : () => _triggerScan(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00F0FF),
                    foregroundColor: Colors.black,
                    minimumSize: const Size.fromHeight(50),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: _isScanning
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                        )
                      : const Text(
                          "SCAN PACKAGING",
                          style: TextStyle(
                            fontFamily: 'monospace',
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                            letterSpacing: 1.5,
                          ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScenarioChip(String label, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: color.withOpacity(0.5)),
        ),
        child: Text(
          label,
          style: TextStyle(color: color, fontFamily: 'monospace', fontSize: 11, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}

class ReticlePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF00F0FF)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    const cornerLength = 30.0;
    const pad = 40.0;

    // Top-Left
    canvas.drawLine(const Offset(pad, pad), const Offset(pad + cornerLength, pad), paint);
    canvas.drawLine(const Offset(pad, pad), const Offset(pad, pad + cornerLength), paint);

    // Top-Right
    canvas.drawLine(Offset(size.width - pad, pad), Offset(size.width - pad - cornerLength, pad), paint);
    canvas.drawLine(Offset(size.width - pad, pad), Offset(size.width - pad, pad + cornerLength), paint);

    // Bottom-Left
    canvas.drawLine(Offset(pad, size.height - pad), Offset(pad + cornerLength, size.height - pad), paint);
    canvas.drawLine(Offset(pad, size.height - pad), Offset(pad, size.height - pad - cornerLength), paint);

    // Bottom-Right
    canvas.drawLine(Offset(size.width - pad, size.height - pad), Offset(size.width - pad - cornerLength, size.height - pad), paint);
    canvas.drawLine(Offset(size.width - pad, size.height - pad), Offset(size.width - pad, size.height - pad - cornerLength), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
