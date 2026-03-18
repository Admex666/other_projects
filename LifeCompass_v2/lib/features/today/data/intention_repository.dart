import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/database.dart';

class IntentionRepository {
  final AppDatabase _db;

  IntentionRepository(this._db);

  Stream<DailyIntention?> watchIntentionForDate(DateTime date) {
    final startOfDay = DateTime(date.year, date.month, date.day);
    return (_db.select(_db.dailyIntentions)
          ..where((t) => t.date.equals(startOfDay)))
        .watchSingleOrNull();
  }

  Future<int> upsertIntention(DailyIntentionsCompanion companion) {
    return _db.into(_db.dailyIntentions).insertOnConflictUpdate(companion);
  }
}

final intentionRepositoryProvider = Provider<IntentionRepository>((ref) {
  return IntentionRepository(ref.watch(databaseProvider));
});
