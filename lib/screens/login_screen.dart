import '../language.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

/// Phone + OTP login. For the hackathon demo this is entirely local —
/// any 4-digit code is accepted. Swap in Firebase Auth once Person 1
/// has time post-MVP.
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
      body: SafeArea(
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
                    prefixIcon: Icon(Icons.phone_outlined),
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
                  decoration: InputDecoration(hintText: '••••'),
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
    );
  }
}
