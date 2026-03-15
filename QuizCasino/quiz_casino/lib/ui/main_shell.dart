import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/audio_manager.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'home_screen.dart';
import 'leaderboard_screen.dart';
import 'guild_screen.dart';
import 'profile_screen.dart';
import 'shop_screen.dart';
import 'auth_screen.dart';
import 'widgets/cyber_loader.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 2; // Home is index 2 in [Shop, Guild, Home, Rank]

  final List<Widget> _screens = [
    const ShopScreen(),
    const GuildScreen(),
    const HomeScreen(),
    const LeaderboardScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        if (!game.isInitialized) {
          return const Scaffold(
            backgroundColor: AppTheme.backgroundDarkNavy,
            body: Center(child: CyberLoader(label: "BOOTING SYSTEM")),
          );
        }

        if (!game.isLoggedIn) {
          return const AuthScreen();
        }

        return Stack(
          children: [
            Scaffold(
              extendBody: true,
              body: Column(
                children: [
                  _buildGlobalTopBar(game),
                  Expanded(child: _screens[_currentIndex]),
                ],
              ),
              bottomNavigationBar: SafeArea(
                child: Container(
                  margin: const EdgeInsets.fromLTRB(16, 0, 16, 24),
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
                      _buildNavItem(Icons.shopping_bag_rounded, "SHOP", 0),
                      _buildNavItem(Icons.shield_rounded, "GUILD", 1),
                      _buildNavItem(Icons.home_rounded, "HOME", 2),
                      _buildNavItem(Icons.emoji_events_rounded, "RANK", 3),
                    ],
                  ),
                ),
              ),
            ),

            // --- CONNECTION LOST OVERLAY ---
            if (!game.isConnected)
              Positioned.fill(
                child: Container(
                  color: Colors.black.withOpacity(0.7),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.wifi_off_rounded, color: AppTheme.dangerRed, size: 80)
                            .animate(onPlay: (c) => c.repeat(reverse: true))
                            .scale(begin: const Offset(1, 1), end: const Offset(1.2, 1.2), duration: 1.seconds)
                            .shimmer(delay: 500.ms),
                        const SizedBox(height: 24),
                        const Text(
                          "CONNECTION LOST",
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 28, letterSpacing: 2),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          "Reconnecting to servers...",
                          style: TextStyle(color: Colors.white54, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ).animate().fadeIn(),
              ),
          ],
        );
      },
    );
  }

  Widget _buildGlobalTopBar(GameManager game) {
    return Container(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top + 8, left: 24, right: 24, bottom: 16),
      decoration: BoxDecoration(
        color: AppTheme.backgroundDarkNavy,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          _buildResourcePill(game.userStats?.gold.toString() ?? "0", Icons.toll_rounded, AppTheme.goldCoin),
          const SizedBox(width: 12),
          _buildResourcePill(game.userStats?.diamonds.toString() ?? "0", Icons.auto_awesome_rounded, AppTheme.purpleGlow),
        ],
      ),
    );
  }

  Widget _buildResourcePill(String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: color.withOpacity(0.3), width: 1.5),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 6),
          Text(
            value,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13),
          ),
        ],
      ),
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
