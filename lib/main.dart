import 'package:flutter/material.dart';
import 'theme.dart';
import 'screens/language_select_screen.dart';

void main() {
  runApp(const ArtisanApp());
}

class ArtisanApp extends StatelessWidget {
  const ArtisanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Artisan App',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.theme,
      home: const LanguageSelectScreen(),
    );
  }
}
