import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'match_screen.dart';
import 'widgets/chunky_button.dart';
import 'widgets/profile_card.dart';
import 'league_road_screen.dart';
import '../models/game_data.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        final stats = game.userStats;

        return Column(
          children: [
            // Header: Profile/Guild Info (Clickable for ProfileCard)
            GestureDetector(
              onTap: () => showDialog(
                context: context,
                builder: (_) => const ProfileCard(),
              ),
              behavior: HitTestBehavior.opaque,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black26,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white10),
                ),
                child: Row(
                  children: [
                    // Avatar
                    Container(
                      padding: const EdgeInsets.all(2),
                      decoration: const BoxDecoration(color: AppTheme.neonCyan, shape: BoxShape.circle),
                      child: const CircleAvatar(
                        radius: 22,
                        backgroundColor: Colors.black,
                        child: Icon(Icons.person_rounded, color: Colors.white, size: 24),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Name & Guild
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            stats?.username.toUpperCase() ?? "GUEST",
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 1),
                          ),
                          Text(
                            stats?.guildTag != null ? "[${stats?.guildTag}]" : "NO GUILD",
                            style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    // League Badge
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.neonCyan.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        "${stats?.league.toUpperCase() ?? "UNRANKED"} ${stats?.division ?? ""}",
                        style: const TextStyle(color: AppTheme.neonCyan, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                      ),
                    ),
                  ],
                ),
              ),
            ).animate().fadeIn(duration: 600.ms).slideY(begin: -0.5, end: 0),

            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // --- CENTER PIECE: EQUIPPED DOT DISPLAY ---
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      // Outer glow
                      Container(
                        width: 180,
                        height: 180,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(color: AppTheme.neonCyan.withOpacity(0.15), blurRadius: 40, spreadRadius: 10)
                          ],
                        ),
                      ),
                      // The Dot
                      Hero(
                        tag: 'dot_hero',
                        child: Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.black,
                            border: Border.all(color: AppTheme.neonCyan, width: 4),
                            boxShadow: [
                              BoxShadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 15)
                            ],
                          ),
                          child: Center(
                            child: Icon(
                              _getSkinIcon(stats?.equippedSkin),
                              size: 60,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ).animate(onPlay: (c) => c.repeat(reverse: true))
                       .moveY(begin: -10, end: 10, duration: 2000.ms, curve: Curves.easeInOut),
                    ],
                  ),
                  
                  const SizedBox(height: 24),

                  // --- LEAGUE PROGRESS & NEXT MILESTONE ---
                  GestureDetector(
                    onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const LeagueRoadScreen())),
                    child: Container(
                      width: 280,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.03),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppTheme.neonCyan.withOpacity(0.2)),
                        boxShadow: [
                          BoxShadow(color: AppTheme.neonCyan.withOpacity(0.05), blurRadius: 20, spreadRadius: -5)
                        ],
                      ),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    "NEXT MILESTONE",
                                    style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
                                  ),
                                  Text(
                                    _getNextMilestoneName(stats?.elo ?? 0),
                                    style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: const BoxDecoration(color: Colors.white10, shape: BoxShape.circle),
                                child: const Icon(Icons.arrow_forward_ios_rounded, color: AppTheme.neonCyan, size: 12),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Stack(
                            alignment: Alignment.center,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: LinearProgressIndicator(
                                  value: _getProgressToNextMilestone(stats?.elo ?? 0),
                                  backgroundColor: Colors.white10,
                                  color: AppTheme.neonCyan,
                                  minHeight: 14,
                                ),
                              ),
                              Text(
                                "${stats?.elo ?? 0} ELO",
                                style: const TextStyle(color: Colors.black, fontSize: 9, fontWeight: FontWeight.w900),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.2, end: 0),

                  const SizedBox(height: 48),
                  
                  // PLAY BUTTON
                  SizedBox(
                    width: 220,
                    height: 80,
                    child: ChunkyButton(
                      onTap: () {
                        game.startNewMatch();
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MatchScreen()));
                      },
                      baseColor: AppTheme.neonCyan,
                      shadowColor: const Color(0xFF009989),
                      borderRadius: 40,
                      child: const Center(
                        child: Text(
                          "PLAY",
                          style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.black, letterSpacing: 4),
                        ),
                      ),
                    ),
                  ).animate().scale(delay: 600.ms, curve: Curves.elasticOut, duration: 800.ms),

                  const SizedBox(height: 32),

                  // Energy
                  _buildEnergyBar(),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildEnergyBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.neonCyan.withOpacity(0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.bolt_rounded, color: AppTheme.neonCyan, size: 20)
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .scale(end: const Offset(1.2, 1.2), duration: 800.ms),
          const SizedBox(width: 8),
          const Text("3 / 5", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
        ],
      ),
    ).animate().fadeIn(delay: 800.ms).slideY(begin: 0.5, end: 0);
  }

  IconData _getSkinIcon(String? skin) {
    switch (skin) {
      case 'knight': return Icons.shield;
      case 'mage': return Icons.auto_fix_high;
      case 'ninja': return Icons.bolt;
      case 'crown': return Icons.emoji_events;
      default: return Icons.person_rounded;
    }
  }

  String _getNextMilestoneName(int elo) {
    if (elo < 500) return "BRONZE II";
    if (elo < 1000) return "BRONZE I";
    if (elo < 1500) return "SILVER III";
    if (elo < 1666) return "SILVER II";
    if (elo < 1833) return "SILVER I";
    if (elo < 2000) return "GOLD III";
    if (elo < 2166) return "GOLD II";
    if (elo < 2333) return "GOLD I";
    if (elo < 2500) return "PLATINUM III";
    if (elo < 2666) return "PLATINUM II";
    if (elo < 2833) return "PLATINUM I";
    if (elo < 3000) return "DIAMOND";
    return "ELITE LEGEND";
  }

  double _getProgressToNextMilestone(int elo) {
    final floors = [0, 500, 1000, 1500, 1666, 1833, 2000, 2166, 2333, 2500, 2666, 2833, 3000];
    int currentFloor = 0;
    int nextFloor = 3000;
    
    for (int i = 0; i < floors.length; i++) {
      if (elo >= floors[i]) {
        currentFloor = floors[i];
        if (i + 1 < floors.length) nextFloor = floors[i+1];
      } else {
        break;
      }
    }
    
    if (elo >= 3000) return 1.0;
    return (elo - currentFloor) / (nextFloor - currentFloor);
  }
}

