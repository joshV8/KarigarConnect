import '../language.dart';
import 'package:flutter/material.dart';
import '../theme.dart';
import 'login_screen.dart';

/// First screen the artisan sees. Language choice happens before
/// anything else — it's not buried in settings.
class LanguageSelectScreen extends StatelessWidget {
  const LanguageSelectScreen({super.key});

  void _choose(BuildContext context, String lang) {
    AppLanguage.instance.setLanguage(lang);
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 88,
                height: 88,
                decoration: BoxDecoration(
                  color: AppTheme.accent.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.storefront_outlined, size: 44, color: AppTheme.accent),
              ),
              const SizedBox(height: 24),
              Text(S.get('choose_language'), style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text(S.get('choose_language'), style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 48),
              ElevatedButton(
                onPressed: () => _choose(context, 'hi'),
                child: const Text('हिंदी'),
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
    );
  }
}
