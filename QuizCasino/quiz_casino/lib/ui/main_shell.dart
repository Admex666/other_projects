import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import '../core/audio_manager.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'home_screen.dart';
import 'leaderboard_screen.dart';
import 'guild_screen.dart';
import 'profile_screen.dart';
import 'auth_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HomeScreen(),
    const LeaderboardScreen(),
    const GuildScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        if (!game.isInitialized) {
          return const Scaffold(
            backgroundColor: AppTheme.backgroundDarkNavy,
            body: Center(child: CircularProgressIndicator(color: AppTheme.neonCyan)),
          );
        }

        if (!game.isLoggedIn) {
          return const AuthScreen();
        }

        return Scaffold(
          extendBody: true,
          body: _screens[_currentIndex],
          bottomNavigationBar: SafeArea(
            child: Container(
              margin: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF151525).withOpacity(0.95),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3), width: 2),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.neonCyan.withOpacity(0.2),
                    blurRadius: 20,
                    spreadRadius: 2,
                  )
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(Icons.home_rounded, "HOME", 0),
                  _buildNavItem(Icons.emoji_events_rounded, "RANK", 1),
                  _buildNavItem(Icons.shield_rounded, "GUILD", 2),
                  _buildNavItem(Icons.person_rounded, "PROFILE", 3),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildNavItem(IconData icon, String label, int index) {
    bool isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () {
        if (_currentIndex != index) AudioManager().playClick();
        setState(() => _currentIndex = index);
      },
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.neonCyan.withOpacity(0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? AppTheme.neonCyan : Colors.white54,
              size: isSelected ? 26 : 24,
            ),
            if (isSelected)
              Padding(
                padding: const EdgeInsets.only(left: 8.0),
                child: Text(
                  label,
                  style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, letterSpacing: 1),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
