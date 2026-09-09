import 'package:flutter/material.dart';
import '../theme.dart';

/// The app's logo mark (matches the launcher icon) paired with the
/// wordmark. Used on the pre-login screens for a consistent, branded
/// first impression instead of a generic Material icon.
class BrandMark extends StatelessWidget {
  final double size;
  const BrandMark({super.key, this.size = 88});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: AppTheme.accent,
            borderRadius: BorderRadius.circular(size * 0.28),
            boxShadow: [
              BoxShadow(
                color: AppTheme.accent.withValues(alpha: 0.25),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Center(
            child: Image.asset('assets/icon/icon.png', fit: BoxFit.contain, width: size * 0.62),
          ),
        ),
        const SizedBox(height: 14),
        const Text(
          'KarigarConnect',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.ink, letterSpacing: 0.2),
        ),
      ],
    );
  }
}
