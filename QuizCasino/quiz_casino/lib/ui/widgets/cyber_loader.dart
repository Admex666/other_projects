import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../theme.dart';

class CyberLoader extends StatelessWidget {
  final double size;
  final String? label;

  const CyberLoader({
    super.key, 
    this.size = 60,
    this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Stack(
          alignment: Alignment.center,
          children: [
            // Outer spinning ring
            Container(
              width: size,
              height: size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppTheme.neonCyan.withOpacity(0.1), width: 2),
              ),
            ),
            // Spinning neon arc
            SizedBox(
              width: size,
              height: size,
              child: CircularProgressIndicator(
                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.neonCyan),
                strokeWidth: 3,
                backgroundColor: Colors.transparent,
              ),
            ),
            // Branded Coin in the middle
            Image.asset(
              'assets/knowcoin.png',
              width: size * 0.6,
              height: size * 0.6,
            ).animate(onPlay: (c) => c.repeat(reverse: true))
             .scale(begin: const Offset(0.8, 0.8), end: const Offset(1.1, 1.1), duration: 1.seconds, curve: Curves.easeInOut),
          ],
        ),
        if (label != null) ...[
          const SizedBox(height: 16),
          Text(
            label!.toUpperCase(),
            style: const TextStyle(
              color: AppTheme.neonCyan,
              fontWeight: FontWeight.w900,
              fontSize: 10,
              letterSpacing: 2,
            ),
          ).animate(onPlay: (c) => c.repeat())
           .shimmer(duration: 2.seconds, color: Colors.white),
        ],
      ],
    );
  }
}
