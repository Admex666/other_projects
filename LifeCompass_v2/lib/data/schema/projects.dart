import 'package:drift/drift.dart';
import 'base_table.dart';
import 'goals.dart';

class Projects extends BaseTable {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get goalId => integer().nullable().references(Goals, #id)();
  TextColumn get title => text().withLength(min: 1, max: 255)();
  TextColumn get status => text()(); // planned, active, paused, completed
  IntColumn get priority => integer().withDefault(const Constant(1))();
}
