import 'package:flutter/material.dart';
import '../models/product.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';

/// Read-only detail view for a published product — reachable by
/// tapping any item in Home or Catalog. Reuses the same visual
/// language as Preview so a published listing feels continuous with
/// how it looked right before publishing.
class ProductDetailScreen extends StatelessWidget {
  final Product product;
  const ProductDetailScreen({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('सामान विवरण · Product'),
        actions: const [HomeAction()],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 220,
                width: double.infinity,
                child: SafeImage(
                  file: product.image,
                  url: product.imageUrl,
                  borderRadius: BorderRadius.circular(18),
                ),
              ),
              const SizedBox(height: 20),
              FadeSlideIn(
                delay: const Duration(milliseconds: 60),
                child: _card(label: 'विवरण · Description (हिंदी)', value: product.descriptionHi, textTheme: textTheme),
              ),
              const SizedBox(height: 12),
              FadeSlideIn(
                delay: const Duration(milliseconds: 140),
                child: _card(label: 'Description (English)', value: product.descriptionEn, textTheme: textTheme),
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
                          Text('कीमत · Price', style: textTheme.bodyMedium),
                          Text('₹${product.price.toInt()}',
                              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(product.priceReason,
                          style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.55))),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _card({required String label, required String value, required TextTheme textTheme}) {
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
