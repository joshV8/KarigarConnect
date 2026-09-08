import 'package:flutter/material.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';
import 'home_screen.dart';

/// Shows the AI's output before it goes live. Every generated field
/// is visually separate so the artisan can tell what came from where,
/// and the price shows its reasoning rather than just a number —
/// that's what makes people trust it enough to hit Publish.
class PreviewScreen extends StatelessWidget {
  final Product product;
  const PreviewScreen({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('पूर्वावलोकन · Preview'),
        actions: const [HomeAction()],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Stack(
                        children: [
                          SizedBox(
                            height: 200,
                            width: double.infinity,
                            child: Hero(
                              tag: 'product-photo',
                              child: SafeImage(
                                file: product.image,
                                url: product.imageUrl,
                                borderRadius: BorderRadius.circular(18),
                              ),
                            ),
                          ),
                          Positioned(
                            top: 12,
                            left: 12,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: AppTheme.successBg,
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                'Enhanced',
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.success),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 60),
                        child: _fieldCard(
                          label: 'विवरण · Description (हिंदी)',
                          value: product.descriptionHi,
                          textTheme: textTheme,
                        ),
                      ),
                      const SizedBox(height: 12),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 140),
                        child: _fieldCard(
                          label: 'Description (English)',
                          value: product.descriptionEn,
                          textTheme: textTheme,
                        ),
                      ),
                      const SizedBox(height: 12),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 220),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppTheme.accent.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('सुझाई गई कीमत · Suggested price',
                                      style: textTheme.bodyMedium),
                                  Text(
                                    '₹${product.price.toInt()}',
                                    style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                product.priceReason,
                                style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.55)),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ApiService.instance.publish(product);
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const HomeScreen()),
                    (route) => false,
                  );
                },
                child: const Text('कैटलॉग में जोड़ें · Publish to catalog'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _fieldCard({required String label, required String value, required TextTheme textTheme}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.5))),
          const SizedBox(height: 6),
          Text(value, style: textTheme.bodyLarge),
        ],
      ),
    );
  }
}
