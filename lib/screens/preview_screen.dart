import '../language.dart';
import 'package:flutter/material.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';
import 'home_screen.dart';
import 'buyers_screen.dart';

/// Shows the AI's output before it goes live. Every generated field
/// is visually separate so the artisan can tell what came from where,
/// including voice transcriptions, AI translations, and the price reasoning.
class PreviewScreen extends StatelessWidget {
  final Product product;
  const PreviewScreen({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final hasVoice = product.voiceTranscription != null && product.voiceTranscription!.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('preview_title')),
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
                                bytes: product.imageBytes,
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
                              child: const Text(
                                'AI Enhanced',
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.success),
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (hasVoice) ...[
                        const SizedBox(height: 16),
                        FadeSlideIn(
                          delay: const Duration(milliseconds: 40),
                          child: Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: AppTheme.accent.withValues(alpha: 0.05),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: AppTheme.accent.withValues(alpha: 0.2)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.mic, size: 16, color: AppTheme.accent),
                                    const SizedBox(width: 6),
                                    Text(
                                      S.get('original_voice'),
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.accent),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  product.voiceTranscription ?? '',
                                  style: textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic),
                                ),
                                if (product.translatedVoiceText != null && product.translatedVoiceText!.isNotEmpty) ...[
                                  const SizedBox(height: 8),
                                  const Divider(height: 1),
                                  const SizedBox(height: 8),
                                  Text(
                                    S.get('ai_translation') + ': "${product.translatedVoiceText}"',
                                    style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.7)),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 80),
                        child: _fieldCard(
                          label: S.get('description_hi'),
                          value: product.descriptionHi,
                          textTheme: textTheme,
                        ),
                      ),
                      const SizedBox(height: 12),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 140),
                        child: _fieldCard(
                          label: S.get('description_en'),
                          value: product.descriptionEn,
                          textTheme: textTheme,
                        ),
                      ),
                      const SizedBox(height: 12),
                      FadeSlideIn(
                        delay: const Duration(milliseconds: 200),
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
                                  Text(S.get('suggested_price'),
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
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.people_alt_outlined, size: 18),
                      label: Text(S.get('find_buyers_btn')),
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => BuyersScreen(selectedProduct: product),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: () {
                        ApiService.instance.publish(product);
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(builder: (_) => const HomeScreen()),
                          (route) => false,
                        );
                      },
                      child: Text(S.get('publish')),
                    ),
                  ),
                ],
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
