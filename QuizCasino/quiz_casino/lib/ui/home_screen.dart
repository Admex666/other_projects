import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'match_screen.dart';
import 'match_result_screen.dart';
import 'widgets/chunky_button.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Padding(
              padding: const EdgeInsets.only(bottom: 24.0),
              child: Image.asset(
                'assets/knowcoin.png',
                height: 120, // adjust size as needed
              ).animate().fadeIn(duration: 800.ms).scaleXY(begin: 0.8, end: 1.0, curve: Curves.easeOutBack),
            ),
            // User Rank & Stats
            Consumer<GameManager>(
              builder: (context, game, child) {
                if (!game.isInitialized) {
                  return const CircularProgressIndicator(color: AppTheme.neonCyan);
                }
                final stats = game.userStats;
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.panelGlassColor,
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: AppTheme.goldCoin.withOpacity(0.5)),
                    boxShadow: [
                      BoxShadow(color: AppTheme.goldCoin.withOpacity(0.1), blurRadius: 20, spreadRadius: 2)
                    ],
                  ),
                  child: Column(
                    children: [
                      Text(stats != null ? "KNOWLEDGE: ${stats.totalCoins}" : "LOADING...", 
                          style: const TextStyle(color: AppTheme.goldCoin, fontWeight: FontWeight.bold, letterSpacing: 2)),
                      const SizedBox(height: 8),
                      Text(stats != null ? "Wins: ${stats.victories}" : "Rank: ---", 
                          style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
                    ],
                  ),
                );
              }
            ).animate().slideY(begin: -0.2, end: 0, curve: Curves.easeOutCubic, duration: 600.ms).fadeIn(),
            const SizedBox(height: 60),
            
            // Play Button
            SizedBox(
              width: 200,
              height: 100,
              child: ChunkyButton(
                onTap: () {
                  final game = context.read<GameManager>();
                  game.startNewMatch(); // Result screen is handled inside MatchScreen
                  Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MatchScreen()));
                },
                baseColor: AppTheme.neonCyan,
                shadowColor: const Color(0xFF009989),
                elevation: 12.0,
                borderRadius: 50.0,
                child: Center(
                  child: Text(
                    "PLAY",
                    style: TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: Colors.black, letterSpacing: 4),
                  ).animate(onPlay: (controller) => controller.repeat(reverse: true))
                   .shimmer(color: Colors.white, duration: 1500.ms),
                ),
              ).animate().scale(curve: Curves.elasticOut, duration: 1000.ms, delay: 200.ms),
            ),
            
            const SizedBox(height: 40),
            
            // Gamified Energy / Daily Matches Tracker
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF151525).withOpacity(0.8),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3), width: 2),
                boxShadow: [
                  BoxShadow(color: AppTheme.neonCyan.withOpacity(0.1), blurRadius: 10, spreadRadius: 1)
                ]
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.bolt_rounded, color: AppTheme.neonCyan, size: 28)
                      .animate(onPlay: (c) => c.repeat(reverse: true))
                      .scaleXY(end: 1.2, duration: 800.ms),
                  const SizedBox(width: 8),
                  const Text("ENERGY: ", style: TextStyle(color: Colors.white54, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  const Text("3", style: TextStyle(color: AppTheme.neonCyan, fontSize: 20, fontWeight: FontWeight.w900)),
                  const Text(" / 5", style: TextStyle(color: Colors.white54, fontSize: 16, fontWeight: FontWeight.w900)),
                ],
              ),
            ).animate().slideY(begin: 0.5, end: 0, duration: 600.ms, curve: Curves.easeOutBack).fadeIn(),
          ],
        ),
      ),
    );
  }
}
