import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../core/game_manager.dart';
import '../../theme.dart';
import '../league_road_screen.dart';

class ProfileCard extends StatelessWidget {
  const ProfileCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        final stats = game.userStats;
        if (stats == null) return const SizedBox.shrink();

        final winRate = stats.gamesPlayed > 0 
            ? (stats.victories / stats.gamesPlayed * 100).toStringAsFixed(1) 
            : "0.0";

        return Dialog(
          backgroundColor: Colors.transparent,
          insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
          child: Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A2E),
              borderRadius: BorderRadius.circular(30),
              border: Border.all(color: AppTheme.neonCyan.withOpacity(0.5), width: 2),
              boxShadow: [
                BoxShadow(color: AppTheme.neonCyan.withOpacity(0.2), blurRadius: 30, spreadRadius: 5)
              ],
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Header / Close button
                  Padding(
                    padding: const EdgeInsets.only(top: 16, right: 16),
                    child: Align(
                      alignment: Alignment.topRight,
                      child: IconButton(
                        icon: const Icon(Icons.close, color: Colors.white54),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ),
                  ),

                  // Avatar
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppTheme.neonCyan, width: 3),
                    ),
                    child: const CircleAvatar(
                      radius: 40,
                      backgroundColor: Colors.black,
                      child: Icon(Icons.person_rounded, size: 50, color: Colors.white),
                    ),
                  ),

                  const SizedBox(height: 16),
                  Text(
                    stats.username.toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 2),
                  ),
                  Text(
                    stats.guildTag != null ? "[${stats.guildTag}]" : "NO GUILD",
                    style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, letterSpacing: 1),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.neonCyan.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3)),
                    ),
                    child: InkWell(
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const LeagueRoadScreen()));
                      },
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            "${stats.league.toUpperCase()} ${stats.division}",
                            style: const TextStyle(color: AppTheme.neonCyan, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1),
                          ),
                          const SizedBox(width: 4),
                          const Icon(Icons.info_outline, color: AppTheme.neonCyan, size: 14),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Stats Grid
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      mainAxisSpacing: 16,
                      crossAxisSpacing: 16,
                      childAspectRatio: 1.3,
                      children: [
                        _buildStatCard("GOLD", stats.gold.toString(), AppTheme.goldCoin, Icons.monetization_on),
                        _buildStatCard("DIAMONDS", stats.diamonds.toString(), AppTheme.purpleGlow, Icons.diamond),
                        _buildStatCard("ELO", stats.elo.toString(), AppTheme.neonCyan, Icons.military_tech),
                        _buildStatCard("WIN RATE", "$winRate%", Colors.greenAccent, Icons.insights),
                      ],
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Logout Option
                  TextButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      game.logout();
                    },
                    icon: const Icon(Icons.logout, color: Colors.redAccent, size: 18),
                    label: const Text("LOGOUT", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
                  ),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ).animate().scale(duration: 400.ms, curve: Curves.easeOutBack).fadeIn(),
        );
      },
    );
  }

  Widget _buildStatCard(String label, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900),
          ),
          Text(
            label,
            style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
