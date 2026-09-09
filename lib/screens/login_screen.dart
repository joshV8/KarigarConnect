import 'package:flutter/material.dart';
import '../language.dart';
import '../services/api_service.dart';
import '../widgets/decorative_background.dart';
import 'home_screen.dart';
import 'buyer_home_screen.dart';

/// Phone + OTP login with dynamic role routing for Sellers and Buyers.
class LoginScreen extends StatefulWidget {
  final String userRole;
  const LoginScreen({super.key, this.userRole = 'seller'});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _companyController = TextEditingController();
  final _otpController = TextEditingController();
  bool _otpSent = false;

  bool get isBuyer => widget.userRole == 'buyer';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          isBuyer ? S.get('role_buyer_title') : S.get('role_seller_title'),
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
                  isBuyer
                      ? (S.isHindi ? 'थोक खरीदार पोर्टल में आपका स्वागत है' : 'Welcome to Wholesale Buyer Portal')
                      : (S.isHindi ? 'कारीगर विक्रय पोर्टल में आपका स्वागत है' : 'Welcome to Artisan Seller Portal'),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.black54,
                      ),
                ),
                const SizedBox(height: 28),
                if (!_otpSent) ...[
                  if (isBuyer) ...[
                    TextField(
                      controller: _companyController,
                      style: const TextStyle(fontSize: 16),
                      decoration: InputDecoration(
                        prefixIcon: const Icon(Icons.business_outlined),
                        hintText: S.get('buyer_company_hint'),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
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
                      backgroundColor: isBuyer ? const Color(0xFF1E3A8A) : null,
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
                      final prefix = isBuyer ? 'buyer_' : 'artisan_';
                      final token = phone.isNotEmpty
                          ? '$prefix${phone.replaceAll(RegExp(r'\D'), '')}'
                          : '${prefix}demo_user';

                      ApiService.instance.setAuthToken(token);
                      ApiService.instance.setUserRole(widget.userRole);

                      if (isBuyer && _companyController.text.trim().isNotEmpty) {
                        ApiService.instance.setBuyerCompany(_companyController.text.trim());
                      }

                      if (isBuyer) {
                        Navigator.of(context).pushReplacement(
                          MaterialPageRoute(builder: (_) => const BuyerHomeScreen()),
                        );
                      } else {
                        Navigator.of(context).pushReplacement(
                          MaterialPageRoute(builder: (_) => const HomeScreen()),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: isBuyer ? const Color(0xFF1E3A8A) : null,
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
