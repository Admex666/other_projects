import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../theme.dart';

class CoinVFX {
  static void show({
    required BuildContext context,
    required Offset source,
    required Offset target,
    int count = 12,
  }) {
    final overlay = Overlay.of(context);
    final List<OverlayEntry> entries = [];

    for (int i = 0; i < count; i++) {
      late OverlayEntry entry;
      entry = OverlayEntry(
        builder: (context) => _FlyingCoin(
          source: source,
          target: target,
          delay: (i * 80).ms,
          onComplete: () {
            entry.remove();
            entries.remove(entry);
          },
        ),
      );
      entries.add(entry);
      overlay.insert(entry);
    }
  }
}

class _FlyingCoin extends StatelessWidget {
  final Offset source;
  final Offset target;
  final Duration delay;
  final VoidCallback onComplete;

  const _FlyingCoin({
    required this.source,
    required this.target,
    required this.delay,
    required this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: source.dx,
      top: source.dy,
      child: Image.asset(
        'assets/knowcoin.png',
        width: 24,
        height: 24,
      )
      .animate(
        onComplete: (_) => onComplete(),
        delay: delay,
      )
      .move(
        begin: Offset.zero,
        end: target - source,
        duration: 800.ms,
        curve: Curves.easeInBack,
      )
      .scale(
        begin: const Offset(1.5, 1.5),
        end: const Offset(0.5, 0.5),
        duration: 800.ms,
      )
      .shake(hz: 4, duration: 800.ms)
      .fadeOut(delay: 600.ms, duration: 200.ms),
    );
  }
}
