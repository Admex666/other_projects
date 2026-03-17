import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/database.dart';

class HabitRepository {
  final AppDatabase _db;

  HabitRepository(this._db);

  Stream<List<Habit>> watchAllHabits() {
    return (_db.select(_db.habits)..where((t) => t.isDeleted.equals(false))).watch();
  }

  Future<int> createHabit(HabitsCompanion companion) {
    return _db.into(_db.habits).insert(companion);
  }

  Future<bool> updateHabit(HabitsCompanion companion) {
    return _db.update(_db.habits).replace(companion);
  }

  Future<int> softDeleteHabit(int id) {
    return (_db.update(_db.habits)..where((t) => t.id.equals(id)))
        .write(const HabitsCompanion(isDeleted: Value(true)));
  }

  Stream<List<HabitEntry>> watchEntriesForDate(DateTime date) {
    final startOfDay = DateTime(date.year, date.month, date.day);
    return (_db.select(_db.habitEntries)..where((t) => t.date.equals(startOfDay))).watch();
  }

  Future<void> toggleHabitCompletion(int habitId, DateTime date) async {
    final startOfDay = DateTime(date.year, date.month, date.day);
    final existing = await (_db.select(_db.habitEntries)
          ..where((t) => t.habitId.equals(habitId) & t.date.equals(startOfDay)))
        .getSingleOrNull();

    if (existing != null) {
      await (_db.delete(_db.habitEntries)..where((t) => t.id.equals(existing.id))).go();
    } else {
      await _db.into(_db.habitEntries).insert(
            HabitEntriesCompanion.insert(
              habitId: habitId,
              date: startOfDay,
            ),
          );
    }
  }
}

final habitRepositoryProvider = Provider<HabitRepository>((ref) {
  return HabitRepository(ref.watch(databaseProvider));
});
