import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class KeldorTheme {
  // Midnight & Vibrant Green Palette
  static const Color background = Color(0xFF000000); // Midnight Black
  static const Color surface = Color(0xFF0A0A0A);   // Surface
  static const Color primary = Color(0xFF39FF14);   // Vibrant Green
  static const Color secondary = Color(0xFF00CC00); // Darker Green
  static const Color error = Color(0xFFCF6679);
  static const Color onBackground = Color(0xFFE0E0E0);
  static const Color onSurface = Color(0xFFE0E0E0);
  static const Color accent = Color(0xFF39FF14);    // Vibrant Green for special items

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      primaryColor: primary,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface,
        background: background,
        error: error,
        onBackground: onBackground,
        onSurface: onSurface,
      ),
      textTheme: TextTheme(
        displayLarge: GoogleFonts.cinzel(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: primary,
          letterSpacing: 1.2,
        ),
        displayMedium: GoogleFonts.cinzel(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: onBackground,
        ),
        bodyLarge: GoogleFonts.merriweather(
          fontSize: 16,
          color: onBackground,
          height: 1.5,
        ),
        bodyMedium: GoogleFonts.merriweather(
          fontSize: 14,
          color: onBackground.withOpacity(0.8),
        ),
        labelLarge: GoogleFonts.inter(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: background, // For buttons
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: background,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: GoogleFonts.inter(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: primary,
        unselectedItemColor: Colors.white54,
      ),
    );
  }
}
