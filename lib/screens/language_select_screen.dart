import 'package:flutter/material.dart';
import '../language.dart';
import '../widgets/brand_mark.dart';
import '../widgets/decorative_background.dart';
import 'role_select_screen.dart';

/// First screen the user sees. Language choice happens before role selection.
class LanguageSelectScreen extends StatelessWidget {
  const LanguageSelectScreen({super.key});

  void _choose(BuildContext context, String lang) {
    AppLanguage.instance.setLanguage(lang);
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const RoleSelectScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecorativeBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const BrandMark(),
                const SizedBox(height: 16),
                Text('अपनी भाषा चुनें · Choose Language', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 48),
                ElevatedButton(
                  onPressed: () => _choose(context, 'hi'),
                  child: const Text('हिंदी (Hindi)'),
                ),
                const SizedBox(height: 14),
                OutlinedButton(
                  onPressed: () => _choose(context, 'en'),
                  child: const Text('English'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
