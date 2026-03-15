import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/game_data.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';
import 'widgets/chunky_button.dart';

class ChestOpeningDialog extends StatefulWidget {
  final Map<String, dynamic> rewards;

  const ChestOpeningDialog({super.key, required this.rewards});

  @override
  State<ChestOpeningDialog> createState() => _ChestOpeningDialogState();
}

class _ChestOpeningDialogState extends State<ChestOpeningDialog> {
  bool _revealed = false;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF151525),
          borderRadius: BorderRadius.circular(30),
          border: Border.all(color: AppTheme.neonCyan.withOpacity(0.5), width: 2),
          boxShadow: [
            BoxShadow(color: AppTheme.neonCyan.withOpacity(0.2), blurRadius: 40, spreadRadius: 5),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "CHEST OPENED!",
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 24, letterSpacing: 2),
            ),
            const SizedBox(height: 32),
            
            if (!_revealed)
               const Icon(Icons.inventory_2, color: AppTheme.goldCoin, size: 120)
                .animate(onPlay: (p) => p.repeat())
                .shimmer(duration: 2.seconds)
                .shake(hz: 4, curve: Curves.easeInOut)
                .scale(begin: const Offset(1,1), end: const Offset(1.1, 1.1), duration: 1.seconds)
            else
              _buildRewardsContent(),

            const SizedBox(height: 40),
            ChunkyButton(
              onTap: () {
                if (!_revealed) {
                  setState(() => _revealed = true);
                } else {
                  Navigator.pop(context);
                }
              },
              baseColor: AppTheme.neonCyan,
              shadowColor: Colors.black,
              child: Text(
                _revealed ? "AWESOME!" : "OPEN CHEST", 
                style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900)
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRewardsContent() {
    final int gold = widget.rewards['gold'] ?? 0;
    final int diamonds = widget.rewards['diamonds'] ?? 0;
    final Map<String, dynamic>? itemData = widget.rewards['item'];

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _rewardPill(gold.toString(), Icons.monetization_on, AppTheme.goldCoin, 0),
            const SizedBox(width: 12),
            _rewardPill(diamonds.toString(), Icons.diamond, AppTheme.purpleGlow, 200),
          ],
        ),
        if (itemData != null) ...[
          const SizedBox(height: 24),
          const Text("NEW ITEM UNLOCKED!", style: TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, fontSize: 12)),
          const SizedBox(height: 12),
          ChunkyCard(
            baseColor: const Color(0xFF1A1A33),
            shadowColor: Colors.black,
            borderColor: AppTheme.goldCoin,
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.auto_awesome, color: AppTheme.goldCoin),
                const SizedBox(width: 12),
                Text(
                  (itemData['name'] as String).toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16),
                ),
              ],
            ),
          ).animate().scale(duration: 600.ms, curve: Curves.elasticOut),
        ]
      ],
    ).animate().fadeIn(duration: 400.ms);
  }

  Widget _rewardPill(String text, IconData icon, Color color, int delay) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 8),
          Text(text, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18)),
        ],
      ),
    ).animate(delay: delay.ms).scale(duration: 500.ms, curve: Curves.easeOutBack).fadeIn();
  }
}
