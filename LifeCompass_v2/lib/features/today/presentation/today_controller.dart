import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:drift/drift.dart';
import '../data/intention_repository.dart';
import '../data/task_repository.dart';
import '../../habits/data/habit_repository.dart';
import '../../../data/database.dart';
import 'today_state.dart';

class TodayController extends Notifier<TodayState> {
  IntentionRepository get _intentionRepo => ref.read(intentionRepositoryProvider);
  TaskRepository get _taskRepo => ref.read(taskRepositoryProvider);
  HabitRepository get _habitRepo => ref.read(habitRepositoryProvider);

  StreamSubscription? _intentionSub;
  StreamSubscription? _tasksSub;
  StreamSubscription? _habitsSub;
  StreamSubscription? _entriesSub;

  @override
  TodayState build() {
    ref.onDispose(() {
      _intentionSub?.cancel();
      _tasksSub?.cancel();
      _habitsSub?.cancel();
      _entriesSub?.cancel();
    });

    // Schedule init so it runs after build completes and does not mutate state synchronously
    Future.microtask(() => _init());
    return const TodayState(isLoading: true);
  }

  void _init() {
    final now = DateTime.now();
    
    _intentionSub = _intentionRepo.watchIntentionForDate(now).listen((intention) {
      state = state.copyWith(intention: intention);
    });

    _tasksSub = _taskRepo.watchTodayTasks().listen((tasks) {
      state = state.copyWith(tasks: tasks);
    });

    _habitsSub = _habitRepo.watchAllHabits().listen((habits) {
      state = state.copyWith(habits: habits);
    });

    _entriesSub = _habitRepo.watchEntriesForDate(now).listen((entries) {
      final completedIds = entries.map((e) => e.habitId).toSet();
      state = state.copyWith(completedHabitIds: completedIds);
    });

    state = state.copyWith(isLoading: false);
  }

  Future<void> updateIntention(String content) async {
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    await _intentionRepo.upsertIntention(
      DailyIntentionsCompanion.insert(
        date: startOfDay,
        content: content,
        updatedAt: Value(DateTime.now()),
      ),
    );
  }

  Future<void> toggleHabit(int habitId) async {
    await _habitRepo.toggleHabitCompletion(habitId, DateTime.now());
  }
}

final todayControllerProvider = NotifierProvider<TodayController, TodayState>(() {
  return TodayController();
});
