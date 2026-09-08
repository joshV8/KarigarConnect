import 'package:flutter/material.dart';
import 'utils/page_transitions.dart';

/// Central theme — a cooler teal/blue palette on a cool near-white
/// background, with a deliberately large type scale for users who
/// may not be confident readers. Change values here, not in
/// individual screens.
class AppTheme {
  // Cool teal accent — feels modern/tech, fits the "AI-driven" pitch.
  static const accent = Color(0xFF0E7C86);
  static const accentDark = Color(0xFF075E66);
  static const canvas = Color(0xFFF2F6FA);
  static const ink = Color(0xFF1C2733);
  static const success = Color(0xFF2E7D5B);
  static const successBg = Color(0xFFE3F3EC);
  static const danger = Color(0xFFB33951);

  static ThemeData get theme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: accent,
      brightness: Brightness.light,
    ).copyWith(primary: accent, surface: canvas);

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: canvas,
      fontFamily: 'Roboto',
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: FadeSlidePageTransitionsBuilder(),
          TargetPlatform.iOS: FadeSlidePageTransitionsBuilder(),
          TargetPlatform.windows: FadeSlidePageTransitionsBuilder(),
          TargetPlatform.macOS: FadeSlidePageTransitionsBuilder(),
          TargetPlatform.linux: FadeSlidePageTransitionsBuilder(),
        },
      ),
      textTheme: TextTheme(
        // Conspicuously large — this is the single most important
        // accessibility lever for low-literacy / low-confidence readers.
        headlineSmall: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: ink, height: 1.25),
        titleLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, color: ink),
        bodyLarge: TextStyle(fontSize: 18, color: ink, height: 1.4),
        bodyMedium: TextStyle(fontSize: 16, color: ink.withValues(alpha: 0.7)),
        labelLarge: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accent,
          foregroundColor: Colors.white,
          disabledBackgroundColor: accent.withValues(alpha: 0.35),
          minimumSize: const Size.fromHeight(58),
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ).copyWith(
          overlayColor: WidgetStateProperty.all(Colors.white.withValues(alpha: 0.15)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: ink,
          side: BorderSide(color: ink.withValues(alpha: 0.2), width: 1.5),
          minimumSize: const Size.fromHeight(58),
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: accentDark,
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: ink.withValues(alpha: 0.12)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: ink.withValues(alpha: 0.12)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: accent, width: 2),
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: canvas,
        surfaceTintColor: canvas,
        elevation: 0,
        foregroundColor: ink,
        centerTitle: true,
        titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: ink),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: ink.withValues(alpha: 0.06)),
        ),
      ),
    );
  }
}
