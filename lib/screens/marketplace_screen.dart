import '../language.dart';
import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/catalog_model.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';

/// Screen showcasing publicly published artisan crafts and curated digital collections.
class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Product> _products = [];
  List<CatalogModel> _catalogs = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final prods = await ApiService.instance.fetchMarketplaceProducts();
    final cats = await ApiService.instance.fetchMarketplaceCatalogs();
    if (mounted) {
      setState(() {
        _products = prods;
        _catalogs = cats;
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('marketplace_title')),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.ink,
          indicatorColor: AppTheme.accent,
          tabs: [Tab(text: S.get('products_tab')),
            Tab(text: S.get('collections_tab')),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Products Tab
                _products.isEmpty
                    ? Center(
                        child: Text(
                          S.get('no_marketplace_products'),
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: GridView.builder(
                          padding: const EdgeInsets.all(20),
                          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2,
                            mainAxisSpacing: 16,
                            crossAxisSpacing: 16,
                            childAspectRatio: 0.72,
                          ),
                          itemCount: _products.length,
                          itemBuilder: (context, i) {
                            final p = _products[i];
                            return FadeSlideIn(
                              delay: Duration(milliseconds: 40 * i),
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                                ),
                                clipBehavior: Clip.antiAlias,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Expanded(
                                      child: SafeImage(
                                        file: p.image,
                                        bytes: p.imageBytes,
                                        url: p.imageUrl,
                                      ),
                                    ),
                                    Padding(
                                      padding: const EdgeInsets.all(12),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            p.descriptionEn,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                                          ),
                                          const SizedBox(height: 4),
                                          Row(
                                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                            children: [
                                              Text(
                                                '₹${p.price.toInt()}',
                                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.accent),
                                              ),
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                decoration: BoxDecoration(
                                                  color: AppTheme.successBg,
                                                  borderRadius: BorderRadius.circular(6),
                                                ),
                                                child: const Text('Live', style: TextStyle(fontSize: 10, color: AppTheme.success, fontWeight: FontWeight.w700)),
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),

                // Catalogs Tab
                _catalogs.isEmpty
                    ? Center(
                        child: Text(
                          S.get('no_published_collections'),
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(20),
                          itemCount: _catalogs.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 16),
                          itemBuilder: (context, i) {
                            final cat = _catalogs[i];
                            return FadeSlideIn(
                              delay: Duration(milliseconds: 50 * i),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          cat.title,
                                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
                                        ),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                          decoration: BoxDecoration(
                                            color: AppTheme.accentBg,
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: Text(
                                            '${cat.products.length} Items',
                                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.accent),
                                          ),
                                        ),
                                      ],
                                    ),
                                    if (cat.description != null && cat.description!.isNotEmpty) ...[
                                      const SizedBox(height: 6),
                                      Text(cat.description!, style: Theme.of(context).textTheme.bodyMedium),
                                    ],
                                    if (cat.products.isNotEmpty) ...[
                                      const SizedBox(height: 12),
                                      SizedBox(
                                        height: 80,
                                        child: ListView.separated(
                                          scrollDirection: Axis.horizontal,
                                          itemCount: cat.products.length,
                                          separatorBuilder: (_, __) => const SizedBox(width: 8),
                                          itemBuilder: (ctx, pi) {
                                            final cp = cat.products[pi];
                                            return ClipRRect(
                                              borderRadius: BorderRadius.circular(10),
                                              child: SizedBox(
                                                width: 80,
                                                height: 80,
                                                child: SafeImage(
                                                  file: cp.image,
                                                  bytes: cp.imageBytes,
                                                  url: cp.imageUrl,
                                                ),
                                              ),
                                            );
                                          },
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
              ],
            ),
    );
  }
}
