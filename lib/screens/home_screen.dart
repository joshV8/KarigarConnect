import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/product.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import 'add_product_screen.dart';
import 'catalog_screen.dart';

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
  void _refresh() => setState(() {});

  @override
  Widget build(BuildContext context) {
    final List<Product> catalog = ApiService.instance.catalog;

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
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const AddProductScreen()),
                  );
                  _refresh();
                },
              ),
              const SizedBox(height: 28),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('कैटलॉग · Catalog', style: Theme.of(context).textTheme.titleLarge),
                  TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const CatalogScreen()),
                    ),
                    child: const Text('सब देखें · View all'),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Expanded(
                child: catalog.isEmpty
                    ? Center(
                        child: Text(
                          'अभी कोई सामान नहीं\nNo products yet',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      )
                    : ListView.separated(
                        itemCount: catalog.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (context, i) {
                          final p = catalog[i];
                          return FadeSlideIn(
                            delay: Duration(milliseconds: 60 * i),
                            child: Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
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
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
