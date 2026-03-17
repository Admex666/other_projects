import 'package:flutter/material.dart';
import 'package:animations/animations.dart';
import '../../features/today/presentation/today_screen.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/theme/app_colors.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const TodayScreen(),
    const Center(child: Text('Goals Content')),    // Placeholder
    const Center(child: Text('Projects Content')), // Placeholder
    const Center(child: Text('Habits Content')),   // Placeholder
    const Center(child: Text('Profile Content')),  // Placeholder
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      body: PageTransitionSwitcher(
        duration: const Duration(milliseconds: 400),
        transitionBuilder: (child, primaryAnimation, secondaryAnimation) {
          return FadeThroughTransition(
            animation: primaryAnimation,
            secondaryAnimation: secondaryAnimation,
            child: child,
          );
        },
        child: _pages[_currentIndex],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textMuted,
        backgroundColor: AppColors.background,
        type: BottomNavigationBarType.fixed,
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.today), label: l10n.todayTab),
          BottomNavigationBarItem(icon: const Icon(Icons.track_changes), label: l10n.goalsTab),
          BottomNavigationBarItem(icon: const Icon(Icons.assignment), label: l10n.projectsTab),
          BottomNavigationBarItem(icon: const Icon(Icons.repeat), label: l10n.habitsTab),
          BottomNavigationBarItem(icon: const Icon(Icons.person), label: l10n.profileTab),
        ],
      ),
    );
  }
}
