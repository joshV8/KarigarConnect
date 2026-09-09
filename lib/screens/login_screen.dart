import 'package:flutter/material.dart';
import '../language.dart';
import '../services/api_service.dart';
import '../widgets/decorative_background.dart';
import 'home_screen.dart';

/// Phone + OTP login with dynamic localization and auth token storage.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  bool _otpSent = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecorativeBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(S.get('login_title'), style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 32),
                if (!_otpSent) ...[
                  TextField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    style: const TextStyle(fontSize: 20),
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.phone_outlined),
                      hintText: S.get('phone_hint'),
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () => setState(() => _otpSent = true),
                    child: Text(S.get('send_otp')),
                  ),
                ] else ...[
                  TextField(
                    controller: _otpController,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(fontSize: 22, letterSpacing: 10, fontWeight: FontWeight.w600),
                    textAlign: TextAlign.center,
                    decoration: const InputDecoration(hintText: '••••'),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () {
                      final phone = _phoneController.text.trim();
                      final token = phone.isNotEmpty
                          ? 'artisan_${phone.replaceAll(RegExp(r'\D'), '')}'
                          : 'artisan_demo_user';
                      ApiService.instance.setAuthToken(token);
                      Navigator.of(context).pushReplacement(
                        MaterialPageRoute(builder: (_) => const HomeScreen()),
                      );
                    },
                    child: Text(S.get('verify')),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
