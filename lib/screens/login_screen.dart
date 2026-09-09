import 'package:flutter/material.dart';
import '../language.dart';
import '../services/api_service.dart';
import '../widgets/decorative_background.dart';
import 'role_select_screen.dart';

/// Phone + OTP login. After verification, navigates to Role Selection.
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
      appBar: AppBar(
        title: Text(
          S.get('login_title'),
          style: const TextStyle(fontSize: 16),
        ),
      ),
      body: DecorativeBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  S.get('login_title'),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                Text(
                  S.isHindi
                      ? 'कारीगर कनेक्ट में आपका स्वागत है'
                      : 'Welcome to KarigarConnect',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.black54,
                      ),
                ),
                const SizedBox(height: 28),
                if (!_otpSent) ...[
                  TextField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    style: const TextStyle(fontSize: 18),
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.phone_outlined),
                      hintText: S.get('phone_hint'),
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () => setState(() => _otpSent = true),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
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
                          ? 'user_${phone.replaceAll(RegExp(r'\D'), '')}'
                          : 'user_demo';

                      ApiService.instance.setAuthToken(token);

                      // Navigate to Role Selection after OTP verification
                      Navigator.of(context).pushReplacement(
                        MaterialPageRoute(
                          builder: (_) => RoleSelectScreen(phone: phone),
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
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
