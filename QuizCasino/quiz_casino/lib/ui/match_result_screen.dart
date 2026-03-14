import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../models/game_data.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';

class MatchResultScreen extends StatelessWidget {
  final int placement;
  final int chipsRemaining;

  const MatchResultScreen({super.key, required this.placement, required this.chipsRemaining});

  @override
  Widget build(BuildContext context) {
    final game = context.read<GameManager>();
    final finalPlayers = game.finalPlayers;
    final isEliminated = game.localPlayer.isEliminated;
    // Victory only if placement == 1 AND not eliminated
    final isVictory = placement == 1 && !isEliminated;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            children: [
              // Header
              Image.asset('assets/knowcoin.png', height: 60)
                  .animate().fadeIn(duration: 600.ms),
              const SizedBox(height: 12),
              Text(
                isVictory ? '🏆 VICTORY!' : '💀 GAME OVER',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w900,
                  color: isVictory ? AppTheme.goldCoin : AppTheme.dangerRed,
                  letterSpacing: 3,
                ),
              ).animate().scale(curve: Curves.elasticOut, duration: 1000.ms)
               .shimmer(duration: 1500.ms, color: Colors.white),

              const SizedBox(height: 24),

              // Leaderboard title
              const Text(
                'FINAL STANDINGS',
                style: TextStyle(color: Colors.white54, letterSpacing: 2, fontSize: 13, fontWeight: FontWeight.bold),
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 12),

              // Leaderboard
              Expanded(
                child: ListView.builder(
                  physics: const BouncingScrollPhysics(),
                  itemCount: finalPlayers.isNotEmpty ? finalPlayers.length : 0,
                  itemBuilder: (context, i) {
                    final player = finalPlayers[i];
                    final rank = i + 1;
                    final isMe = player.username == game.localPlayer.username;
                    return _buildLeaderboardRow(rank, player, isMe, i);
                  },
                ),
              ),

              const SizedBox(height: 20),

              // Stats row
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                decoration: BoxDecoration(
                  color: const Color(0xFF151525),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.purpleGlow.withOpacity(0.5)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('GOLD EARNED', style: TextStyle(color: Colors.white54, fontSize: 11)),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.monetization_on, color: AppTheme.goldCoin, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              '+${(chipsRemaining * (placement == 1 ? 3 : placement == 2 ? 2 : placement == 3 ? 1 : 0.5)).floor()}',
                              style: const TextStyle(color: AppTheme.goldCoin, fontSize: 24, fontWeight: FontWeight.w900),
                            ),
                          ],
                        ),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text('ELO CHANGE', style: TextStyle(color: Colors.white54, fontSize: 11)),
                        const SizedBox(height: 4),
                        Text(
                          placement == 1 ? '+25' : (placement <= 2 ? '+10' : '-15'),
                          style: TextStyle(
                            color: placement <= 2 ? AppTheme.successGreen : AppTheme.dangerRed,
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ).animate().slideY(begin: 0.3, end: 0, delay: 300.ms, duration: 500.ms, curve: Curves.easeOutBack)
               .fadeIn(delay: 300.ms),

              const SizedBox(height: 20),

              // Return button
              ChunkyButton(
                onTap: () => Navigator.of(context).popUntil((route) => route.isFirst),
                baseColor: AppTheme.neonCyan,
                shadowColor: const Color(0xFF009989),
                elevation: 6.0,
                borderRadius: 30.0,
                padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                child: const Text(
                  'RETURN HOME',
                  style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 1),
                ),
              ).animate().slideY(begin: 0.5, end: 0, delay: 500.ms, duration: 500.ms, curve: Curves.easeOutBack)
               .fadeIn(delay: 500.ms),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLeaderboardRow(int rank, Player player, bool isMe, int animIndex) {
    Color rankColor;
    IconData? medal;
    switch (rank) {
      case 1:
        rankColor = AppTheme.goldCoin;
        medal = Icons.emoji_events_rounded;
        break;
      case 2:
        rankColor = Colors.grey.shade300;
        medal = Icons.emoji_events_rounded;
        break;
      case 3:
        rankColor = const Color(0xFFCD7F32);
        medal = Icons.emoji_events_rounded;
        break;
      default:
        rankColor = Colors.white38;
        medal = null;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: isMe
            ? AppTheme.purpleGlow.withOpacity(0.2)
            : const Color(0xFF1A1A2E),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isMe ? AppTheme.purpleGlow : Colors.white10,
          width: isMe ? 2 : 1,
        ),
      ),
      child: Row(
        children: [
          // Rank
          SizedBox(
            width: 40,
            child: medal != null
                ? Icon(medal, color: rankColor, size: 22)
                : Text('#$rank', style: TextStyle(color: rankColor, fontWeight: FontWeight.w900, fontSize: 16)),
          ),
          const SizedBox(width: 12),
          // Eliminated badge or empty
          if (player.isEliminated)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppTheme.dangerRed.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.dangerRed, width: 1),
              ),
              child: const Text('OUT', style: TextStyle(color: AppTheme.dangerRed, fontSize: 10, fontWeight: FontWeight.bold)),
            ),
          // Name
          Expanded(
            child: Text(
              player.username + (isMe ? ' (You)' : ''),
              style: TextStyle(
                color: isMe ? Colors.white : Colors.white70,
                fontWeight: isMe ? FontWeight.w900 : FontWeight.normal,
                fontSize: 16,
              ),
            ),
          ),
          // Stack
          Text(
            '${player.stack}',
            style: TextStyle(
              color: rankColor,
              fontWeight: FontWeight.w900,
              fontSize: 20,
            ),
          ),
          const SizedBox(width: 4),
          const Text('KC', style: TextStyle(color: Colors.white38, fontSize: 11)),
        ],
      ),
    ).animate().slideX(begin: 0.3, end: 0, delay: (100 + animIndex * 80).ms, duration: 400.ms, curve: Curves.easeOutQuad)
     .fadeIn(delay: (100 + animIndex * 80).ms);
  }
}
