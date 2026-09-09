import 'package:flutter/material.dart';
import '../theme.dart';

/// Brief full-screen "done!" moment shown after a meaningful action
/// (publishing a product) — a checkmark that pops in, holds, then
/// calls [onComplete]. Gives the artisan clear, satisfying
/// confirmation instead of an abrupt screen change.
class SuccessOverlay extends StatefulWidget {
  final String message;
  final VoidCallback onComplete;
  const SuccessOverlay({super.key, required this.message, required this.onComplete});

  @override
  State<SuccessOverlay> createState() => _SuccessOverlayState();
}

class _SuccessOverlayState extends State<SuccessOverlay> with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 450));
  late final Animation<double> _scale = CurvedAnimation(parent: _controller, curve: Curves.elasticOut);
  late final Animation<double> _fade = CurvedAnimation(parent: _controller, curve: const Interval(0, 0.4));

  @override
  void initState() {
    super.initState();
    _controller.forward();
    Future.delayed(const Duration(milliseconds: 1100), widget.onComplete);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppTheme.canvas,
      child: Center(
        child: FadeTransition(
          opacity: _fade,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ScaleTransition(
                scale: _scale,
                child: Container(
                  width: 96,
                  height: 96,
                  decoration: const BoxDecoration(color: AppTheme.success, shape: BoxShape.circle),
                  child: const Icon(Icons.check_rounded, color: Colors.white, size: 52),
                ),
              ),
              const SizedBox(height: 20),
              Text(widget.message, style: Theme.of(context).textTheme.titleLarge, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
