import 'package:drift/drift.dart';
import 'base_table.dart';
import 'goals.dart';

class Habits extends BaseTable {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get goalId => integer().nullable().references(Goals, #id)();
  TextColumn get title => text().withLength(min: 1, max: 255)();
  TextColumn get frequency => text()(); // Daily, Weekly, etc.
  IntColumn get streak => integer().withDefault(const Constant(0))();
}
