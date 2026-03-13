import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../core/game_manager.dart';
import '../../theme.dart';

class MatchmakingOverlay extends StatelessWidget {
  const MatchmakingOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppTheme.backgroundDarkNavy,
      child: Stack(
        children: [
          // Animated Background Elements
          Positioned(
            top: -100,
            left: -100,
            child: _buildBlurCircle(AppTheme.neonCyan.withOpacity(0.1), 300),
          ),
          Positioned(
            bottom: -50,
            right: -50,
            child: _buildBlurCircle(AppTheme.goldCoin.withOpacity(0.1), 250),
          ),
          
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Pulsing Logo
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.neonCyan.withOpacity(0.2),
                        blurRadius: 40,
                        spreadRadius: 10,
                      )
                    ],
                  ),
                  child: Image.asset(
                    'assets/knowcoin.png',
                    height: 150,
                  ),
                )
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scaleXY(begin: 0.95, end: 1.05, duration: 2.seconds, curve: Curves.easeInOut),
                
                const SizedBox(height: 48),
                
                // Animated Text
                const Text(
                  "SEARCHING FOR OPPONENTS",
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 3,
                  ),
                )
                .animate(onPlay: (c) => c.repeat())
                .shimmer(duration: 2.seconds, color: AppTheme.neonCyan),
                
                const SizedBox(height: 16),
                
                // Loading indicator (custom dots)
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(3, (i) => 
                    Container(
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: AppTheme.neonCyan,
                        shape: BoxShape.circle,
                      ),
                    )
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .scaleXY(begin: 0.5, end: 1.2, delay: (i * 200).ms, duration: 600.ms)
                  ),
                ),
                
                const SizedBox(height: 60),
                
                // Tip of the day
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.1)),
                    ),
                    child: const Column(
                      children: [
                        Text(
                          "PRO TIP",
                          style: TextStyle(color: AppTheme.goldCoin, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "The faster you answer, the bigger the reward pot grows! But careful - a wrong answer loses it all.",
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                ).animate().fadeIn(delay: 1.seconds).slideY(begin: 0.2, end: 0),
              ],
            ),
          ),
          
          // Cancel Button
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Center(
              child: TextButton(
                onPressed: () {
                  context.read<GameManager>().cancelMatchmaking();
                  Navigator.of(context).pop();
                },
                child: Text(
                  "CANCEL",
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.3),
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBlurCircle(Color color, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
      ),
    ).animate().fadeIn(duration: 2.seconds);
  }
}
