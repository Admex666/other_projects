import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../../../data/database.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BackupService {
  final AppDatabase _db;

  BackupService(this._db);

  Future<String> exportToJson() async {
    // This is a simplified export. In a real app, you'd fetch all tables.
    final goals = await _db.select(_db.goals).get();
    final habits = await _db.select(_db.habits).get();
    
    final data = {
      'goals': goals.map((e) => e.toJson()).toList(),
      'habits': habits.map((e) => e.toJson()).toList(),
      'exported_at': DateTime.now().toIso8601String(),
    };

    return jsonEncode(data);
  }

  Future<void> importFromJson(String json) async {
    final data = jsonDecode(json) as Map<String, dynamic>;
    // Import logic would involve transactionally inserting into Drift tables
    // and handling potential conflicts.
  }

  Future<File> saveBackupToFile(String json) async {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/life_compass_backup_${DateTime.now().millisecondsSinceEpoch}.json');
    return await file.writeAsString(json);
  }
}

final backupServiceProvider = Provider<BackupService>((ref) {
  return BackupService(ref.watch(databaseProvider));
});
