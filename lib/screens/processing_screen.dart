import 'dart:math';
import 'package:flutter/material.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../widgets/safe_image.dart';
import '../widgets/home_action.dart';
import 'preview_screen.dart';

/// Shown while the (mocked) AI pipeline runs. Displays the same photo
/// the artisan just took — carried over via a Hero from the photo
/// step and continuing on to Preview — dimmed under a pulsing icon,
/// so it visually reads as "your photo is being worked on" rather
/// than a generic loading spinner.
class ProcessingScreen extends StatefulWidget {
  final ProductDraft draft;
  const ProcessingScreen({super.key, required this.draft});

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController =
      AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat();

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    final Product result = await ApiService.instance.processNewProduct(widget.draft);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => PreviewScreen(product: result)),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        actions: const [HomeAction()],
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          Hero(
            tag: 'product-photo',
            child: SafeImage(file: widget.draft.photo),
          ),
          Container(color: Colors.black.withValues(alpha: 0.55)),
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    final scale = 1 + 0.1 * sin(_pulseController.value * 2 * pi);
                    return Transform.scale(scale: scale, child: child);
                  },
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.auto_awesome, color: Colors.white, size: 36),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'AI तैयार कर रहा है...',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: Colors.white),
                ),
                const SizedBox(height: 6),
                Text(
                  'AI is preparing your listing',
                  style: TextStyle(fontSize: 15, color: Colors.white.withValues(alpha: 0.8)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
