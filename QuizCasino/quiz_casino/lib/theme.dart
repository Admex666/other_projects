import 'package:flutter/material.dart';

class AppTheme {
  // Backgrounds
  static const Color backgroundDarkNavy = Color(0xFF0D0D1A);
  static const Color panelGlassColor = Color(0x801A1A33); // 50% opacity

  // Accents
  static const Color neonCyan = Color(0xFF00FFE5);
  static const Color purpleGlow = Color(0xFF991AFF);
  static const Color goldCoin = Color(0xFFFFCC1A);

  // States
  static const Color successGreen = Color(0xFF33E54D);
  static const Color dangerRed = Color(0xFFE53333);

  static ThemeData get themeData {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: backgroundDarkNavy,
      primaryColor: neonCyan,
      colorScheme: const ColorScheme.dark(
        primary: neonCyan,
        secondary: purpleGlow,
        surface: panelGlassColor,
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: neonCyan,
        inactiveTrackColor: neonCyan.withOpacity(0.3),
        thumbColor: neonCyan,
        overlayColor: neonCyan.withOpacity(0.2),
      ),
      fontFamily: 'Input', // Assuming a modern font
    );
  }
}
