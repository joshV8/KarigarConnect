import 'package:flutter/material.dart';
import '../widgets/brand_mark.dart';
import '../widgets/decorative_background.dart';
import 'login_screen.dart';

/// First screen the artisan sees. Language choice happens before
/// anything else — it's not buried in settings.
class LanguageSelectScreen extends StatelessWidget {
  const LanguageSelectScreen({super.key});

  void _choose(BuildContext context) {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
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
                const SizedBox(height: 8),
                Text('अपनी भाषा चुनें', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 4),
                Text('Choose your language', style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 48),
                ElevatedButton(
                  onPressed: () => _choose(context),
                  child: const Text('हिंदी'),
                ),
                const SizedBox(height: 14),
                OutlinedButton(
                  onPressed: () => _choose(context),
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
