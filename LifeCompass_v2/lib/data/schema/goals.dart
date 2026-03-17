import 'package:drift/drift.dart';
import 'base_table.dart';

class Goals extends BaseTable {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get parentGoalId => integer().nullable().references(Goals, #id)();
  TextColumn get title => text().withLength(min: 1, max: 255)();
  TextColumn get type => text()(); // financial, career, mental, physical, spiritual, time
  TextColumn get horizon => text()(); // vision, strategy, objective, quarter, month
  RealColumn get targetValue => real().nullable()();
  TextColumn get targetType => text().nullable()();
  DateTimeColumn get targetDate => dateTime().nullable()();
  RealColumn get progress => real().withDefault(const Constant(0.0))();
  DateTimeColumn get lastReviewedAt => dateTime().nullable()();
}
