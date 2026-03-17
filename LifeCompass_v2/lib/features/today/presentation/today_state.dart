import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../data/database.dart';

part 'today_state.freezed.dart';

@freezed
abstract class TodayState with _$TodayState {
  const factory TodayState({
    @Default(false) bool isLoading,
    DailyIntention? intention,
    @Default([]) List<Task> tasks,
    @Default([]) List<Habit> habits,
    @Default({}) Set<int> completedHabitIds,
    String? errorMessage,
  }) = _TodayState;
}
