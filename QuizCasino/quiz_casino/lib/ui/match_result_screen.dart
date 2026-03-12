import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';
import 'widgets/chunky_button.dart';

class MatchResultScreen extends StatelessWidget {
  final int placement;
  final int pointsGained;

  const MatchResultScreen({super.key, required this.placement, required this.pointsGained});

  @override
  Widget build(BuildContext context) {
    bool isVictory = placement == 1;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                isVictory ? "VICTORY" : "ELIMINATED",
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.w900,
                  color: isVictory ? AppTheme.goldCoin : AppTheme.dangerRed,
                  letterSpacing: 4,
                ),
              ).animate().scale(curve: Curves.elasticOut, duration: 1000.ms).shimmer(duration: 1500.ms),
              const SizedBox(height: 20),
              ChunkyCard(
                baseColor: const Color(0xFF151525).withOpacity(0.9),
                shadowColor: Colors.black,
                borderColor: AppTheme.purpleGlow,
                elevation: 6.0,
                padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 24),
                child: Column(
                  children: [
                    const Text("FINAL PLACEMENT", style: TextStyle(color: Colors.white54)),
                    const SizedBox(height: 8),
                    Text("#$placement", style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.white)),
                    const Divider(color: Colors.white10, height: 40),
                    const Text("RATING POINTS", style: TextStyle(color: Colors.white54)),
                    const SizedBox(height: 8),
                    Text(
                      pointsGained > 0 ? "+$pointsGained" : "$pointsGained",
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: pointsGained > 0 ? AppTheme.successGreen : AppTheme.dangerRed,
                      ),
                    ),
                  ],
                ),
              ).animate().slideY(begin: 0.3, end: 0, delay: 200.ms, duration: 500.ms, curve: Curves.easeOutBack).fadeIn(delay: 200.ms),
              const SizedBox(height: 60),
              ChunkyButton(
                onTap: () {
                  // Pop back until the MainShell (Home)
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
                baseColor: AppTheme.neonCyan,
                shadowColor: const Color(0xFF009989),
                elevation: 6.0,
                borderRadius: 30.0,
                padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                child: const Text(
                  "RETURN HOME", 
                  style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 1),
                ),
              ).animate().slideY(begin: 0.5, end: 0, delay: 400.ms, duration: 500.ms, curve: Curves.easeOutBack).fadeIn(delay: 400.ms),
            ],
          ),
        ),
      ),
    );
  }
}
