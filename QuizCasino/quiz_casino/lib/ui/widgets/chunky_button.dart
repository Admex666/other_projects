import 'package:flutter/material.dart';
import '../../core/audio_manager.dart';

class ChunkyButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;
  final Color baseColor;
  final Color shadowColor;
  final double elevation;
  final double borderRadius;
  final EdgeInsets padding;
  final bool isSelected;
  final Color? borderColor;

  const ChunkyButton({
    super.key,
    required this.child,
    this.onTap,
    required this.baseColor,
    required this.shadowColor,
    this.elevation = 6.0,
    this.borderRadius = 16.0,
    this.padding = const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
    this.isSelected = false,
    this.borderColor,
  });

  @override
  State<ChunkyButton> createState() => _ChunkyButtonState();
}

class _ChunkyButtonState extends State<ChunkyButton> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) {
        if (widget.onTap == null) return;
        setState(() => _isPressed = true);
        AudioManager().playClick();
      },
      onTapUp: (_) {
        if (widget.onTap == null) return;
        setState(() => _isPressed = false);
        widget.onTap!();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 80),
        curve: Curves.easeInOut,
        margin: EdgeInsets.only(
          top: _isPressed ? widget.elevation : 0,
          bottom: _isPressed ? 0 : widget.elevation,
        ),
        decoration: BoxDecoration(
          color: widget.baseColor,
          borderRadius: BorderRadius.circular(widget.borderRadius),
          border: widget.borderColor != null || widget.isSelected
              ? Border.all(color: widget.borderColor ?? Colors.white, width: 3)
              : null,
          boxShadow: [
            if (!_isPressed)
              BoxShadow(
                color: widget.shadowColor,
                offset: Offset(0, widget.elevation),
              ),
            if (widget.isSelected)
              BoxShadow(
                color: widget.baseColor.withOpacity(0.5),
                blurRadius: 15,
                spreadRadius: 2,
              )
          ],
        ),
        child: Padding(
          padding: widget.padding,
          child: widget.child,
        ),
      ),
    );
  }
}
