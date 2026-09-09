import 'dart:async';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// TraceRx Offline-First Local SQLite Cache
/// Enables instantaneous verification and double-dispense traps even in remote clinics
/// with zero cellular or satellite connectivity.
class OfflineBatchCache {
  static final OfflineBatchCache instance = OfflineBatchCache._init();
  static Database? _database;

  OfflineBatchCache._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('tracerx_offline.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE cached_batches (
        batch_id TEXT PRIMARY KEY,
        gtin TEXT NOT NULL,
        drug_name TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        merkle_root TEXT NOT NULL,
        status TEXT NOT NULL,
        is_dispensed INTEGER NOT NULL DEFAULT 0,
        dispensed_at INTEGER,
        dispensed_location TEXT,
        last_verified_at INTEGER NOT NULL
      )
    ''');

    // Pre-seed known local scenarios for zero-network validation
    await db.insert('cached_batches', {
      'batch_id': 'PZ-2026-X99',
      'gtin': '00300019920148',
      'drug_name': 'Remdesivir (Veklury) 100mg',
      'expiry_date': '2028-03-01',
      'merkle_root': '0x9a8f4c2e71b5d6a89c0e3f2187b5a3c9e120f4b8',
      'status': 'ACTIVE',
      'is_dispensed': 0,
      'last_verified_at': DateTime.now().millisecondsSinceEpoch,
    });

    await db.insert('cached_batches', {
      'batch_id': 'GSK-8812-D',
      'gtin': '00300018812042',
      'drug_name': 'Amoxicillin & Clavulanate 625mg',
      'expiry_date': '2027-06-15',
      'merkle_root': '0x77c2b09a4d3f18e9a2b5c87e1f40d2a938c11e74',
      'status': 'DISPENSED',
      'is_dispensed': 1,
      'dispensed_at': 1757040000000,
      'dispensed_location': 'Square Hospital Dispensary, Dhaka',
      'last_verified_at': DateTime.now().millisecondsSinceEpoch,
    });
  }

  Future<void> saveBatch(Map<String, dynamic> batch) async {
    final db = await instance.database;
    await db.insert(
      'cached_batches',
      {
        'batch_id': batch['batch_id'],
        'gtin': batch['gtin'] ?? '00300010000000',
        'drug_name': batch['drug_name'] ?? 'Generic Formulation',
        'expiry_date': batch['expiry_date'] ?? '2028-01-01',
        'merkle_root': batch['merkle_root'] ?? '0x0',
        'status': batch['status'] ?? 'ACTIVE',
        'is_dispensed': batch['status'] == 'DISPENSED' ? 1 : 0,
        'dispensed_at': batch['dispensed_at'],
        'dispensed_location': batch['dispensed_location'],
        'last_verified_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Map<String, dynamic>?> getBatch(String batchId) async {
    final db = await instance.database;
    final results = await db.query(
      'cached_batches',
      where: 'batch_id = ?',
      whereArgs: [batchId],
    );

    if (results.isNotEmpty) {
      return results.first;
    }
    return null;
  }

  Future<bool> isBatchDispensed(String batchId) async {
    final batch = await getBatch(batchId);
    if (batch == null) return false;
    return batch['is_dispensed'] == 1 || batch['status'] == 'DISPENSED';
  }

  Future<void> markDispensedLocally(String batchId, String location) async {
    final db = await instance.database;
    await db.update(
      'cached_batches',
      {
        'status': 'DISPENSED',
        'is_dispensed': 1,
        'dispensed_at': DateTime.now().millisecondsSinceEpoch,
        'dispensed_location': location,
      },
      where: 'batch_id = ?',
      whereArgs: [batchId],
    );
  }
}
