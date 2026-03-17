import 'package:drift/drift.dart';
import 'habits.dart';

class HabitEntries extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get habitId => integer().references(Habits, #id)();
  DateTimeColumn get date => dateTime()(); // The date for which the habit was completed
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}
