import 'package:flutter/material.dart';
import 'theme.dart';
import 'screens/language_select_screen.dart';
import 'language.dart';

void main() {
  runApp(const ArtisanApp());
}

class ArtisanApp extends StatelessWidget {
  const ArtisanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppLanguage.instance,
      builder: (context, child) {
        return MaterialApp(
          title: 'KarigarConnect',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.theme,
          home: const LanguageSelectScreen(),
        );
      },
    );
  }
}
