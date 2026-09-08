import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';
import 'product_detail_screen.dart';

/// Full catalog grid. Kept separate from Home so Home can stay
/// focused on "add a new product" as the primary action.
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  Future<void> _refresh() async {
    await Future.delayed(const Duration(milliseconds: 400));
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final catalog = ApiService.instance.catalog;
    return Scaffold(
      appBar: AppBar(
        title: const Text('कैटलॉग · Catalog'),
        actions: const [HomeAction()],
      ),
      body: RefreshIndicator(
        color: AppTheme.accent,
        onRefresh: _refresh,
        child: catalog.isEmpty
            ? ListView(
                children: [
                  SizedBox(height: MediaQuery.of(context).size.height * 0.15),
                  Column(
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
                  ),
                ],
              )
            : GridView.builder(
                padding: const EdgeInsets.all(20),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 0.78,
                ),
                itemCount: catalog.length,
                itemBuilder: (context, i) {
                  final p = catalog[i];
                  return FadeSlideIn(
                    delay: Duration(milliseconds: 50 * i),
                    child: Material(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(18),
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => ProductDetailScreen(product: p)),
                        ),
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(child: SafeImage(file: p.image, url: p.imageUrl)),
                              Padding(
                                padding: const EdgeInsets.all(12),
                                child: Text(
                                  '₹${p.price.toInt()}',
                                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }
}
