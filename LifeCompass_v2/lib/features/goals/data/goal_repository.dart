import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/database.dart';

class GoalRepository {
  final AppDatabase _db;

  GoalRepository(this._db);

  Stream<List<Goal>> watchAllGoals() {
    return (_db.select(_db.goals)..where((t) => t.isDeleted.equals(false))).watch();
  }

  Stream<List<Goal>> watchSubGoals(int parentId) {
    return (_db.select(_db.goals)
          ..where((t) => t.parentGoalId.equals(parentId) & t.isDeleted.equals(false)))
        .watch();
  }

  Future<Goal?> getGoalById(int id) {
    return (_db.select(_db.goals)..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  Future<int> createGoal(GoalsCompanion companion) {
    return _db.into(_db.goals).insert(companion);
  }

  Future<bool> updateGoal(GoalsCompanion companion) {
    return _db.update(_db.goals).replace(companion);
  }

  Future<int> softDeleteGoal(int id) {
    return (_db.update(_db.goals)..where((t) => t.id.equals(id)))
        .write(const GoalsCompanion(isDeleted: Value(true)));
  }

  Future<void> updateProgress(int id, double progress) {
    return (_db.update(_db.goals)..where((t) => t.id.equals(id))).write(
      GoalsCompanion(
        progress: Value(progress),
        lastReviewedAt: Value(DateTime.now()),
        updatedAt: Value(DateTime.now()),
      ),
    );
  }
}

final goalRepositoryProvider = Provider<GoalRepository>((ref) {
  return GoalRepository(ref.watch(databaseProvider));
});
