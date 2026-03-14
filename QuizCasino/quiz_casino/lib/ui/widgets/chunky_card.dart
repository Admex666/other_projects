import 'package:flutter/material.dart';

class ChunkyCard extends StatelessWidget {
  final Widget child;
  final Color baseColor;
  final Color shadowColor;
  final double elevation;
  final double borderRadius;
  final EdgeInsets padding;
  final EdgeInsets? margin;
  final Color? borderColor;

  const ChunkyCard({
    super.key,
    required this.child,
    required this.baseColor,
    required this.shadowColor,
    this.elevation = 6.0,
    this.borderRadius = 16.0,
    this.padding = const EdgeInsets.all(16.0),
    this.margin,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin ?? EdgeInsets.only(bottom: elevation + 8),
      decoration: BoxDecoration(
        color: baseColor,
        borderRadius: BorderRadius.circular(borderRadius),
        border: borderColor != null ? Border.all(color: borderColor!, width: 3) : null,
        boxShadow: [
          BoxShadow(
            color: shadowColor,
            offset: Offset(0, elevation),
          ),
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 10,
            spreadRadius: 2,
            offset: const Offset(0, 5),
          )
        ],
      ),
      child: Padding(
        padding: padding,
        child: child,
      ),
    );
  }
}
