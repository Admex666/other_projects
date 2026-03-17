import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/database.dart';

class ProjectRepository {
  final AppDatabase _db;

  ProjectRepository(this._db);

  Stream<List<Project>> watchAllProjects() {
    return (_db.select(_db.projects)..where((t) => t.isDeleted.equals(false))).watch();
  }

  Stream<List<Project>> watchProjectsByGoal(int goalId) {
    return (_db.select(_db.projects)
          ..where((t) => t.goalId.equals(goalId) & t.isDeleted.equals(false)))
        .watch();
  }

  Future<int> createProject(ProjectsCompanion companion) {
    return _db.into(_db.projects).insert(companion);
  }

  Future<bool> updateProject(ProjectsCompanion companion) {
    return _db.update(_db.projects).replace(companion);
  }

  Future<int> softDeleteProject(int id) {
    return (_db.update(_db.projects)..where((t) => t.id.equals(id)))
        .write(const ProjectsCompanion(isDeleted: Value(true)));
  }
}

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  return ProjectRepository(ref.watch(databaseProvider));
});
