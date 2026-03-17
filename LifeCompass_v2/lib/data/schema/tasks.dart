import 'package:drift/drift.dart';
import 'base_table.dart';
import 'projects.dart';

class Tasks extends BaseTable {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get projectId => integer().nullable().references(Projects, #id)();
  TextColumn get title => text().withLength(min: 1, max: 255)();
  DateTimeColumn get dueDate => dateTime().nullable()();
  TextColumn get status => text()(); // todo, in_progress, done
  IntColumn get priority => integer().withDefault(const Constant(1))();
}
