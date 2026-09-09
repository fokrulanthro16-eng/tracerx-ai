import 'package:flutter/material.dart';
import 'screens/scanner_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const TraceRxMobileApp());
}

class TraceRxMobileApp extends StatelessWidget {
  const TraceRxMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TraceRx AI Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF06090E),
        primaryColor: const Color(0xFF00F0FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00F0FF),
          secondary: Color(0xFF00FF9D),
          error: Color(0xFFFF0055),
          surface: Color(0xFF0C1322),
        ),
      ),
      home: const ScannerScreen(),
    );
  }
}
