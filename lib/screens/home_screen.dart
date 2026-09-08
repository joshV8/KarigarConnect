import '../language.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/product.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import 'add_product_screen.dart';
import 'catalog_screen.dart';
import 'buyers_screen.dart';
import 'enquiries_screen.dart';
import 'marketplace_screen.dart';
import 'notifications_screen.dart';

/// Main Dashboard screen with tab navigation and access to all Artisan capabilities:
/// 1. My Shop & Add Product
/// 2. Verified B2B Wholesale Buyers
/// 3. Wholesale Deals & Enquiries
/// 4. Public Marketplace & Collections
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  int _unreadCount = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    await ApiService.instance.fetchCatalog();
    final unread = await ApiService.instance.fetchUnreadNotificationCount();
    if (mounted) {
      setState(() {
        _unreadCount = unread;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('app_title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.collections_bookmark_outlined),
            tooltip: S.get('catalog_title'),
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const CatalogScreen()),
              );
              _load();
            },
          ),
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                icon: const Icon(Icons.notifications_outlined),
                tooltip: S.get('notifications_title'),
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                  );
                  _load();
                },
              ),
              if (_unreadCount > 0)
                Positioned(
                  top: 10,
                  right: 10,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: AppTheme.accent,
                      shape: BoxShape.circle,
                    ),
                    constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                    child: Text(
                      '$_unreadCount',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildShopTab(),
          const BuyersScreen(),
          const EnquiriesScreen(),
          const MarketplaceScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) {
          setState(() => _currentIndex = idx);
          if (idx == 0) _load();
        },
        backgroundColor: Colors.white,
        elevation: 8,
        indicatorColor: AppTheme.accentBg,
        destinations: [NavigationDestination(
            icon: Icon(Icons.storefront_outlined),
            selectedIcon: Icon(Icons.storefront, color: AppTheme.accent),
            label: S.get('nav_shop'),
          ),
          NavigationDestination(
            icon: Icon(Icons.people_alt_outlined),
            selectedIcon: Icon(Icons.people_alt, color: AppTheme.accent),
            label: S.get('nav_buyers'),
          ),
          NavigationDestination(
            icon: Icon(Icons.handshake_outlined),
            selectedIcon: Icon(Icons.handshake, color: AppTheme.accent),
            label: S.get('nav_deals'),
          ),
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore, color: AppTheme.accent),
            label: S.get('nav_market'),
          ),
        ],
      ),
    );
  }

  Widget _buildShopTab() {
    final List<Product> catalog = ApiService.instance.catalog;

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _load,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Primary Add Product CTA
              ElevatedButton.icon(
                icon: const Icon(Icons.add_a_photo_outlined, size: 24),
                label: Text(S.get('add_product')),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const AddProductScreen()),
                  );
                  _load();
                },
              ),
              const SizedBox(height: 20),

              // Quick Action Grid
              Row(
                children: [
                  Expanded(
                    child: _quickActionCard(
                      icon: Icons.people_alt_outlined,
                      title: S.get('wholesale_buyers'),
                      subtitle: S.get('wholesale_buyers'),
                      color: AppTheme.accent,
                      onTap: () => setState(() => _currentIndex = 1),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _quickActionCard(
                      icon: Icons.handshake_outlined,
                      title: S.get('active_deals'),
                      subtitle: S.get('active_deals'),
                      color: AppTheme.success,
                      onTap: () => setState(() => _currentIndex = 2),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _quickActionCard(
                      icon: Icons.collections_bookmark_outlined,
                      title: S.get('digital_catalog'),
                      subtitle: S.get('digital_catalog'),
                      color: Colors.deepPurple,
                      onTap: () async {
                        await Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const CatalogScreen()),
                        );
                        _load();
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _quickActionCard(
                      icon: Icons.public,
                      title: S.get('public_market'),
                      subtitle: S.get('public_market'),
                      color: Colors.blue.shade700,
                      onTap: () => setState(() => _currentIndex = 3),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Recent Products Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(S.get('my_products') + ' (${catalog.length})', style: Theme.of(context).textTheme.titleLarge),
                  TextButton(
                    onPressed: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const CatalogScreen()),
                      );
                      _load();
                    },
                    child: Text(S.get('view_all')),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              catalog.isEmpty
                  ? Container(
                      padding: const EdgeInsets.symmetric(vertical: 40),
                      alignment: Alignment.center,
                      child: Column(
                        children: [
                          Icon(Icons.inventory_2_outlined, size: 56, color: AppTheme.ink.withValues(alpha: 0.25)),
                          const SizedBox(height: 12),
                          Text(
                            S.get('no_products'),
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: catalog.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, i) {
                        final p = catalog[i];
                        return FadeSlideIn(
                          delay: Duration(milliseconds: 50 * i),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(16),
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => BuyersScreen(selectedProduct: p),
                                ),
                              );
                            },
                            child: Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                              ),
                              padding: const EdgeInsets.all(12),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 60,
                                    height: 60,
                                    child: SafeImage(
                                      file: p.image,
                                      bytes: p.imageBytes,
                                      url: p.imageUrl,
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  const SizedBox(width: 14),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          p.descriptionEn,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          S.get('find_buyers'),
                                          style: TextStyle(fontSize: 12, color: AppTheme.accent.withValues(alpha: 0.8), fontWeight: FontWeight.w500),
                                        ),
                                      ],
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
                          ),
                        );
                      },
                    ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _quickActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            const SizedBox(height: 2),
            Text(subtitle, style: TextStyle(fontSize: 11, color: AppTheme.ink.withValues(alpha: 0.5))),
          ],
        ),
      ),
    );
  }
}
