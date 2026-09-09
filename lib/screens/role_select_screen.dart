import 'package:flutter/material.dart';
import '../language.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/brand_mark.dart';
import '../widgets/decorative_background.dart';
import '../widgets/fade_slide_in.dart';
import 'home_screen.dart';
import 'buyer_home_screen.dart';

/// Screen shown AFTER OTP login. User chooses whether they are an Artisan (Seller)
/// or a Wholesale Buyer, then gets routed to the appropriate dashboard.
class RoleSelectScreen extends StatefulWidget {
  final String phone;
  const RoleSelectScreen({super.key, this.phone = ''});

  @override
  State<RoleSelectScreen> createState() => _RoleSelectScreenState();
}

class _RoleSelectScreenState extends State<RoleSelectScreen> {
  String _selectedRole = 'seller'; // 'seller' or 'buyer'

  void _proceed() {
    // Set the auth token with role prefix
    final phone = widget.phone.isNotEmpty
        ? widget.phone.replaceAll(RegExp(r'\D'), '')
        : 'demo';
    final prefix = _selectedRole == 'buyer' ? 'buyer_' : 'artisan_';
    ApiService.instance.setAuthToken('$prefix$phone');
    ApiService.instance.setUserRole(_selectedRole);

    if (_selectedRole == 'buyer') {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const BuyerHomeScreen()),
      );
    } else {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecorativeBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 12),
                const Center(child: BrandMark()),
                const SizedBox(height: 20),
                Text(
                  S.get('role_select_title'),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 6),
                Text(
                  S.get('role_select_subtitle'),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.ink.withValues(alpha: 0.65),
                      ),
                ),
                const SizedBox(height: 32),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Seller Option
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 60),
                        child: _roleCard(
                          roleKey: 'seller',
                          title: S.get('role_seller_title'),
                          description: S.get('role_seller_desc'),
                          icon: Icons.storefront_rounded,
                          accentColor: AppTheme.accent,
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Buyer Option
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 120),
                        child: _roleCard(
                          roleKey: 'buyer',
                          title: S.get('role_buyer_title'),
                          description: S.get('role_buyer_desc'),
                          icon: Icons.business_center_rounded,
                          accentColor: const Color(0xFF1E3A8A), // Navy/Blue for B2B buyer
                        ),
                      ),
                    ],
                  ),
                ),
                ElevatedButton(
                  onPressed: _proceed,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    backgroundColor: _selectedRole == 'seller' ? AppTheme.accent : const Color(0xFF1E3A8A),
                  ),
                  child: Text(
                    _selectedRole == 'seller' ? S.get('continue_as_seller') : S.get('continue_as_buyer'),
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                ),
                const SizedBox(height: 12),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _roleCard({
    required String roleKey,
    required String title,
    required String description,
    required IconData icon,
    required Color accentColor,
  }) {
    final isSelected = _selectedRole == roleKey;

    return InkWell(
      onTap: () => setState(() => _selectedRole = roleKey),
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? accentColor : AppTheme.ink.withValues(alpha: 0.08),
            width: isSelected ? 2.5 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: accentColor.withValues(alpha: 0.15),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ]
              : [],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: accentColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: accentColor, size: 30),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      Container(
                        width: 22,
                        height: 22,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: isSelected ? accentColor : AppTheme.ink.withValues(alpha: 0.3),
                            width: isSelected ? 6 : 2,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.4,
                      color: AppTheme.ink.withValues(alpha: 0.65),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
