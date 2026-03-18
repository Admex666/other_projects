import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/goal_repository.dart';
import '../../../core/widgets/goal_card.dart';
import '../domain/goal_enums.dart';

class GoalHierarchyView extends ConsumerWidget {
  final int? parentId;

  const GoalHierarchyView({super.key, this.parentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goalsStream = parentId == null 
        ? ref.watch(goalRepositoryProvider).watchAllGoals().map((list) => list.where((g) => g.parentGoalId == null).toList())
        : ref.watch(goalRepositoryProvider).watchSubGoals(parentId!);

    return StreamBuilder(
      stream: goalsStream,
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final goals = snapshot.data!;

        return ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: goals.length,
          separatorBuilder: (context, index) => const SizedBox(height: 16),
          itemBuilder: (context, index) {
            final goal = goals[index];
            return Column(
              children: [
                GoalCard(
                  title: goal.title,
                  type: _parseGoalType(goal.type),
                  horizon: _parseHorizon(goal.horizon),
                  progress: goal.progress,
                  onTap: () {
                    // Navigate deeper or show details
                  },
                ),
                // Optionally show sub-goals inline or via expansion
              ],
            );
          },
        );
      },
    );
  }

  GoalType _parseGoalType(String type) => GoalType.values.byName(type);
  GoalHorizon _parseHorizon(String horizon) => GoalHorizon.values.byName(horizon);
}
