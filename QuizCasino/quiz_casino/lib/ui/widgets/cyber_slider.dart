import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../theme.dart';

class CyberSlider extends StatelessWidget {
  final double value;
  final double min;
  final double max;
  final ValueChanged<double> onChanged;
  final int? divisions;

  const CyberSlider({
    super.key,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
    this.divisions,
  });

  @override
  Widget build(BuildContext context) {
    return SliderTheme(
      data: SliderThemeData(
        trackHeight: 8,
        activeTrackColor: AppTheme.neonCyan,
        inactiveTrackColor: Colors.white10,
        thumbColor: AppTheme.neonCyan,
        overlayColor: AppTheme.neonCyan.withOpacity(0.2),
        thumbShape: const _CyberThumbShape(),
        trackShape: const _CyberTrackShape(),
        tickMarkShape: SliderTickMarkShape.noTickMark,
      ),
      child: Slider(
        value: value,
        min: min,
        max: max,
        divisions: divisions,
        onChanged: (val) {
          if (val != value) {
            HapticFeedback.selectionClick();
            onChanged(val);
          }
        },
      ),
    );
  }
}

class _CyberThumbShape extends RoundSliderThumbShape {
  const _CyberThumbShape({super.enabledThumbRadius = 12});

  @override
  void paint(
    PaintingContext context,
    Offset center, {
    required Animation<double> activationAnimation,
    required Animation<double> enableAnimation,
    required bool isDiscrete,
    required TextPainter labelPainter,
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required TextDirection textDirection,
    required double value,
    required double textScaleFactor,
    required Size sizeWithOverflow,
  }) {
    final Canvas canvas = context.canvas;

    final basePaint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.fill;

    final glowPaint = Paint()
      ..color = AppTheme.neonCyan
      ..maskFilter = const MaskFilter.blur(BlurStyle.outer, 6);

    final borderPaint = Paint()
      ..color = AppTheme.neonCyan
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    // Glow
    canvas.drawCircle(center, enabledThumbRadius, glowPaint);
    // Base
    canvas.drawCircle(center, enabledThumbRadius, basePaint);
    // Border
    canvas.drawCircle(center, enabledThumbRadius, borderPaint);
    // Center point
    canvas.drawCircle(center, 4, Paint()..color = AppTheme.neonCyan);
  }
}

class _CyberTrackShape extends RoundedRectSliderTrackShape {
  const _CyberTrackShape();

  @override
  void paint(
    PaintingContext context,
    Offset offset, {
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required Animation<double> enableAnimation,
    required TextDirection textDirection,
    required Offset thumbCenter,
    Offset? secondaryOffset,
    bool isDiscrete = false,
    bool isEnabled = false,
    double additionalActiveTrackHeight = 2,
  }) {
    if (sliderTheme.trackHeight == null || sliderTheme.trackHeight! <= 0) return;

    final Rect trackRect = getPreferredRect(
      parentBox: parentBox,
      offset: offset,
      sliderTheme: sliderTheme,
      isEnabled: isEnabled,
      isDiscrete: isDiscrete,
    );

    final activePaint = Paint()..color = sliderTheme.activeTrackColor!;
    final inactivePaint = Paint()..color = sliderTheme.inactiveTrackColor!;

    // Inactive track
    context.canvas.drawRRect(
      RRect.fromRectAndRadius(trackRect, const Radius.circular(4)),
      inactivePaint,
    );

    // Active track
    final Rect activeRect = Rect.fromLTRB(
      trackRect.left,
      trackRect.top,
      thumbCenter.dx,
      trackRect.bottom,
    );

    context.canvas.drawRRect(
      RRect.fromRectAndRadius(activeRect, const Radius.circular(4)),
      activePaint,
    );

    // Neon glow for active track if enabled
    final glowPaint = Paint()
      ..color = sliderTheme.activeTrackColor!.withOpacity(0.3)
      ..maskFilter = const MaskFilter.blur(BlurStyle.outer, 8);
    
    context.canvas.drawRRect(
      RRect.fromRectAndRadius(activeRect, const Radius.circular(4)),
      glowPaint,
    );
  }
}
