import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';

class GuildScreen extends StatelessWidget {
  const GuildScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ChunkyCard(
              baseColor: const Color(0xFF151525).withOpacity(0.9),
              shadowColor: Colors.black,
              borderColor: AppTheme.purpleGlow,
              elevation: 4.0,
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  const Text("NEON KNIGHTS [NN]", style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2)),
                  const SizedBox(height: 8),
                  const Text("Weekly Guild Score: 142,500", style: TextStyle(color: AppTheme.goldCoin, fontSize: 18, fontWeight: FontWeight.bold)).animate(onPlay: (c) => c.repeat(reverse: true)).shimmer(color: Colors.white, duration: 2.seconds),
                ],
              ),
            ),
          ).animate().slideY(begin: -0.2, end: 0, duration: 400.ms, curve: Curves.easeOutBack).fadeIn(),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: 15,
              itemBuilder: (context, index) {
                return ChunkyCard(
                  baseColor: const Color(0xFF2A2A4A),
                  shadowColor: const Color(0xFF151525),
                  elevation: 4.0,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const CircleAvatar(backgroundColor: AppTheme.purpleGlow, radius: 16, child: Icon(Icons.person, size: 16)),
                          const SizedBox(width: 16),
                          Text("GuildMember_${index+1}", style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      Text("+${(15 - index) * 400}", style: const TextStyle(color: AppTheme.successGreen, fontSize: 16, fontWeight: FontWeight.w900)),
                    ],
                  ),
                ).animate().slideX(begin: -0.2, end: 0, delay: (30 * index).ms, duration: 400.ms, curve: Curves.easeOut).fadeIn();
              },
            ),
          ),
        ],
      ),
    );
  }
}
