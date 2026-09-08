import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/product.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import 'add_product_screen.dart';
import 'catalog_screen.dart';
import 'product_detail_screen.dart';
import 'buyer_enquiries_screen.dart';

/// Landing screen after login: recent catalog items + one obvious
/// next action. Deliberately not cluttered with a bottom nav bar or
/// multiple CTAs — one big action beats five small ones here. This
/// screen IS home, so it doesn't need a HomeAction itself.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Future<void> _refresh() async {
    await Future.delayed(const Duration(milliseconds: 400));
    setState(() {});
  }

  Future<void> _startAddProduct() async {
    final saved = ApiService.instance.savedDraft;
    ProductDraft? draftToOpen;

    if (saved != null) {
      final choice = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('अधूरा काम मिला · Unfinished draft found'),
          content: const Text('क्या आप पिछला अधूरा सामान जारी रखना चाहते हैं?\nContinue where you left off?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, 'new'), child: const Text('नया शुरू करें · Start new')),
            ElevatedButton(onPressed: () => Navigator.pop(ctx, 'resume'), child: const Text('जारी रखें · Resume')),
          ],
        ),
      );
      if (choice == null) return;
      if (choice == 'resume') {
        draftToOpen = saved;
      } else {
        ApiService.instance.clearDraft();
      }
    }

    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => AddProductScreen(initialDraft: draftToOpen)),
    );
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final List<Product> catalog = ApiService.instance.catalog;
    final enquiryCount = ApiService.instance.enquiries.length;

    return Scaffold(
      appBar: AppBar(title: const Text('मेरी दुकान · My shop')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.add_a_photo_outlined, size: 24),
                label: const Text('नया सामान जोड़ें · Add product'),
                onPressed: _startAddProduct,
              ),
              const SizedBox(height: 14),
              Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: () async {
                    await Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const BuyerEnquiriesScreen()),
                    );
                    if (mounted) setState(() {});
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.storefront_outlined, color: AppTheme.accent, size: 22),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text('खरीदार पूछताछ · Buyer enquiries',
                              style: Theme.of(context).textTheme.bodyLarge),
                        ),
                        if (enquiryCount > 0)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppTheme.accent.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text('$enquiryCount',
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.accent)),
                          ),
                        const SizedBox(width: 4),
                        Icon(Icons.chevron_right, color: AppTheme.ink.withValues(alpha: 0.3)),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('कैटलॉग · Catalog', style: Theme.of(context).textTheme.titleLarge),
                  TextButton(
                    onPressed: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const CatalogScreen()),
                      );
                      if (mounted) setState(() {});
                    },
                    child: const Text('सब देखें · View all'),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Expanded(
                child: RefreshIndicator(
                  color: AppTheme.accent,
                  onRefresh: _refresh,
                  child: catalog.isEmpty
                      ? ListView(
                          children: [
                            SizedBox(height: MediaQuery.of(context).size.height * 0.1),
                            _emptyState(context),
                          ],
                        )
                      : ListView.separated(
                          itemCount: catalog.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 12),
                          itemBuilder: (context, i) {
                            final p = catalog[i];
                            return FadeSlideIn(
                              delay: Duration(milliseconds: 60 * i),
                              child: Material(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(16),
                                  onTap: () async {
                                    await Navigator.of(context).push(
                                      MaterialPageRoute(builder: (_) => ProductDetailScreen(product: p)),
                                    );
                                    if (mounted) setState(() {});
                                  },
                                  child: Container(
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                                    ),
                                    padding: const EdgeInsets.all(10),
                                    child: Row(
                                      children: [
                                        SizedBox(
                                          width: 56,
                                          height: 56,
                                          child: SafeImage(
                                            file: p.image,
                                            url: p.imageUrl,
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                        ),
                                        const SizedBox(width: 14),
                                        Expanded(
                                          child: Text(
                                            p.descriptionEn,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: Theme.of(context).textTheme.bodyLarge,
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          '₹${p.price.toInt()}',
                                          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                                        ),
                                        const SizedBox(width: 4),
                                        Icon(Icons.chevron_right, color: AppTheme.ink.withValues(alpha: 0.3)),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _emptyState(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(color: AppTheme.accent.withValues(alpha: 0.08), shape: BoxShape.circle),
          child: Icon(Icons.inventory_2_outlined, size: 32, color: AppTheme.accent.withValues(alpha: 0.6)),
        ),
        const SizedBox(height: 16),
        Text(
          'अभी कोई सामान नहीं\nNo products yet',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }
}
