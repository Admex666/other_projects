import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';
import 'inventory_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        final stats = game.userStats;
        if (stats == null) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.neonCyan));
        }

        final winRate = stats.gamesPlayed > 0 
            ? (stats.victories / stats.gamesPlayed * 100).toStringAsFixed(1) 
            : "0.0";

        return Scaffold(
          backgroundColor: AppTheme.backgroundDarkNavy,
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
              child: Column(
                children: [
                const SizedBox(height: 20),
                // Avatar / Header
                Center(
                  child: Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.neonCyan, width: 3),
                          boxShadow: [
                            BoxShadow(color: AppTheme.neonCyan.withOpacity(0.3), blurRadius: 20)
                          ],
                        ),
                        child: CircleAvatar(
                          radius: 50,
                          backgroundColor: Colors.black,
                          child: Icon(Icons.person_rounded, size: 60, color: Colors.white.withOpacity(0.8)),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: const BoxDecoration(
                          color: AppTheme.goldCoin,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.star_rounded, size: 20, color: Colors.black),
                      ),
                    ],
                  ),
                ).animate().scale(duration: 600.ms, curve: Curves.easeOutBack),

                const SizedBox(height: 16),
                Text(
                  stats.username.toUpperCase(),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 2,
                  ),
                ).animate().fadeIn(delay: 200.ms),

                const SizedBox(height: 4),
                Text(
                  "${stats.league.toUpperCase()} LEAGUE",
                  style: const TextStyle(
                    color: AppTheme.neonCyan,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 3,
                  ),
                ).animate().fadeIn(delay: 300.ms),

                const SizedBox(height: 40),

                // Stats Grid
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 1.2,
                  children: [
                    _buildStatCard("GOLD", stats.gold.toString(), AppTheme.goldCoin, Icons.monetization_on_rounded),
                    _buildStatCard("DIAMONDS", stats.diamonds.toString(), const Color(0xFFC429FF), Icons.diamond_rounded),
                    _buildStatCard("ELO", stats.elo.toString(), AppTheme.neonCyan, Icons.military_tech_rounded),
                    _buildStatCard("WIN RATE", "$winRate%", Colors.greenAccent, Icons.insights_rounded),
                  ],
                ),

                const SizedBox(height: 20),

                // Inventory Button
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: ChunkyButton(
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const InventoryScreen())),
                    baseColor: AppTheme.neonCyan.withOpacity(0.8),
                    shadowColor: Colors.black,
                    padding: EdgeInsets.zero, // Fixed clipping
                    child: const Center(
                      child: Text(
                        "MY INVENTORY",
                        style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, letterSpacing: 2),
                      ),
                    ),
                  ),
                ).animate().fadeIn(delay: 700.ms),

                const SizedBox(height: 16),

                // Logout Button
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ChunkyButton(
                    onTap: () => game.logout(),
                    baseColor: Colors.redAccent.withOpacity(0.5),
                    shadowColor: const Color(0xFF4A0000),
                    padding: EdgeInsets.zero, // Fixed clipping
                    child: const Center(
                      child: Text(
                        "LOGOUT",
                        style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold, letterSpacing: 2),
                      ),
                    ),
                  ),
                ).animate().fadeIn(delay: 800.ms),
                
                const SizedBox(height: 100), // Extra space for bottom nav
              ],
            ),
          ),
        ),
      );
    },
  );
}

  Widget _buildStatCard(String label, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.panelGlassColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color.withOpacity(0.5), size: 24),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(color: color, fontSize: 22, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 400.ms).scale(begin: const Offset(0.9, 0.9));
  }
}
