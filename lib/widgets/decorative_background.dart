import 'package:flutter/material.dart';
import '../theme.dart';

/// Soft, out-of-focus color blobs behind a screen's content — a cheap
/// way to make a plain form screen feel designed rather than default.
/// Purely decorative; wrap the real content as [child].
class DecorativeBackground extends StatelessWidget {
  final Widget child;
  const DecorativeBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned(
          top: -80,
          right: -60,
          child: _blob(220, AppTheme.accent.withValues(alpha: 0.08)),
        ),
        Positioned(
          bottom: -100,
          left: -80,
          child: _blob(260, AppTheme.accent.withValues(alpha: 0.06)),
        ),
        child,
      ],
    );
  }

  Widget _blob(double size, Color color) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}
