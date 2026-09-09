import 'dart:async';
import 'package:camera/camera.dart';

class CameraService {
  CameraController? _controller;
  bool _isInitialized = false;

  CameraController? get controller => _controller;
  bool get isInitialized => _isInitialized;

  Future<void> initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) return;

      final backCamera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      _controller = CameraController(
        backCamera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _controller!.initialize();
      // Set macro focus mode for close packaging inspection if supported
      try {
        await _controller!.setFocusMode(FocusMode.auto);
      } catch (_) {}

      _isInitialized = true;
    } catch (e) {
      _isInitialized = false;
    }
  }

  Future<void> toggleTorch(bool enable) async {
    if (_controller != null && _controller!.value.isInitialized) {
      await _controller!.setFlashMode(enable ? FlashMode.torch : FlashMode.off);
    }
  }

  Future<XFile?> takeSnapshot() async {
    if (_controller == null || !_controller!.value.isInitialized) {
      return null;
    }
    try {
      return await _controller!.takePicture();
    } catch (e) {
      return null;
    }
  }

  void dispose() {
    _controller?.dispose();
    _isInitialized = false;
  }
}
