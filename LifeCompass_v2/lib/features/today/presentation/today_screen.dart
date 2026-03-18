import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'today_controller.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/widgets/goal_card.dart';
import '../../goals/domain/goal_enums.dart';
import '../../../core/theme/app_colors.dart';
import 'today_state.dart';

import 'package:flutter_animate/flutter_animate.dart';

class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(todayControllerProvider);
    final l10n = AppLocalizations.of(context)!;

    if (state.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: CustomScrollView(
        slivers: [
          SliverAppBar.large(
            title: Text(l10n.todayTab),
            floating: true,
            pinned: true,
            backgroundColor: AppColors.background,
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _buildIntentionCard(context, ref, state, l10n)
                    .animate()
                    .fadeIn(delay: 200.ms, duration: 600.ms)
                    .scale(begin: const Offset(0.95, 0.95), end: const Offset(1, 1)),
                const SizedBox(height: 32),
                _buildHeading(l10n.habitsTab)
                    .animate()
                    .fadeIn(delay: 400.ms),
                const SizedBox(height: 12),
              ]),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final habit = state.habits[index];
                  final isCompleted = state.completedHabitIds.contains(habit.id);
                  return _buildHabitTile(context, ref, habit, isCompleted)
                      .animate()
                      .fadeIn(delay: (500 + (index * 100)).ms)
                      .slideX(begin: 0.1, end: 0);
                },
                childCount: state.habits.length,
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                const SizedBox(height: 32),
                _buildHeading(l10n.goalsTab).animate().fadeIn(delay: 800.ms),
                const SizedBox(height: 12),
                GoalCard(
                  title: 'Financial Freedom 2026',
                  type: GoalType.financial,
                  horizon: GoalHorizon.strategy,
                  progress: 0.45,
                  onTap: () {},
                ).animate().fadeIn(delay: 1000.ms).slideY(begin: 0.1, end: 0),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIntentionCard(BuildContext context, WidgetRef ref, TodayState state, AppLocalizations l10n) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.surface, AppColors.surfaceVariant],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.surfaceVariant),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.stars, color: AppColors.amber, size: 20),
              const SizedBox(width: 8),
              Text(
                l10n.dailyIntention.toUpperCase(),
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (state.intention == null)
            TextField(
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w500),
              decoration: InputDecoration(
                hintText: l10n.whatIsYourFocus,
                hintStyle: TextStyle(color: AppColors.textMuted),
                border: InputBorder.none,
              ),
              onSubmitted: (value) => ref.read(todayControllerProvider.notifier).updateIntention(value),
            )
          else
            Text(
              state.intention!.content,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildHeading(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.w800,
        color: AppColors.textPrimary,
      ),
    );
  }

  Widget _buildHabitTile(BuildContext context, WidgetRef ref, dynamic habit, bool isCompleted) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        title: Text(
          habit.title,
          style: TextStyle(
            decoration: isCompleted ? TextDecoration.lineThrough : null,
            color: isCompleted ? AppColors.textMuted : AppColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
        subtitle: Text(
          isCompleted ? 'Done for today' : 'Tap to complete',
          style: TextStyle(color: AppColors.textMuted, fontSize: 12),
        ),
        trailing: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isCompleted ? AppColors.emerald : Colors.transparent,
            border: Border.all(
              color: isCompleted ? AppColors.emerald : AppColors.textMuted,
              width: 2,
            ),
          ),
          child: isCompleted ? const Icon(Icons.check, size: 18, color: Colors.black) : null,
        ),
        onTap: () => ref.read(todayControllerProvider.notifier).toggleHabit(habit.id),
      ),
    );
  }
}
