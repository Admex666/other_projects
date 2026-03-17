import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/database.dart';

class TaskRepository {
  final AppDatabase _db;

  TaskRepository(this._db);

  Stream<List<Task>> watchTasksByProject(int projectId) {
    return (_db.select(_db.tasks)
          ..where((t) => t.projectId.equals(projectId) & t.isDeleted.equals(false)))
        .watch();
  }

  Stream<List<Task>> watchTodayTasks() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    return (_db.select(_db.tasks)
          ..where((t) => 
            t.dueDate.isSmallerOrEqualValue(today.add(const Duration(days: 1))) & 
            t.isDeleted.equals(false)))
        .watch();
  }

  Future<int> createTask(TasksCompanion companion) {
    return _db.into(_db.tasks).insert(companion);
  }

  Future<bool> updateTask(TasksCompanion companion) {
    return _db.update(_db.tasks).replace(companion);
  }

  Future<int> softDeleteTask(int id) {
    return (_db.update(_db.tasks)..where((t) => t.id.equals(id)))
        .write(const TasksCompanion(isDeleted: Value(true)));
  }
}

final taskRepositoryProvider = Provider<TaskRepository>((ref) {
  return TaskRepository(ref.watch(databaseProvider));
});
