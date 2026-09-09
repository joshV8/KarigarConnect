import '../language.dart';
import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/catalog_model.dart';
import '../models/buyer.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import 'language_select_screen.dart';
import 'role_select_screen.dart';
import 'notifications_screen.dart';

/// Dedicated Dashboard tailored specifically for Wholesale Buyers and Bulk Retailers.
/// Includes 4 specialized sections:
/// 1. Discover Products (with Search & Category Filters)
/// 2. Curated Digital Collections
/// 3. My Purchase Enquiries & Orders Tracking
/// 4. Verified Artisan Directory
class BuyerHomeScreen extends StatefulWidget {
  const BuyerHomeScreen({super.key});

  @override
  State<BuyerHomeScreen> createState() => _BuyerHomeScreenState();
}

class _BuyerHomeScreenState extends State<BuyerHomeScreen> {
  int _currentIndex = 0;
  List<Product> _products = [];
  List<CatalogModel> _catalogs = [];
  List<Buyer> _artisans = [];
  bool _loading = true;
  String _searchQuery = '';
  String _selectedCategory = 'All';

  final List<String> _categories = [
    'All',
    'Home Decor',
    'Handicrafts',
    'Pottery & Terracotta',
    'Textiles & Handloom',
    'Bamboo & Wooden Craft',
    'Brass & Metal Craft',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final prods = await ApiService.instance.fetchMarketplaceProducts(
      category: _selectedCategory == 'All' ? null : _selectedCategory,
    );
    final cats = await ApiService.instance.fetchMarketplaceCatalogs();
    final buyers = await ApiService.instance.fetchBuyers();
    if (mounted) {
      setState(() {
        _products = prods;
        _catalogs = cats;
        _artisans = buyers;
        _loading = false;
      });
    }
  }

  void _showEnquiryDialog(Product product) {
    final qtyController = TextEditingController(text: '50');
    final targetPriceController = TextEditingController(text: '${(product.price * 0.85).toInt()}');
    final notesController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Text(S.get('inquire_dialog_title')),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    SizedBox(
                      width: 50,
                      height: 50,
                      child: SafeImage(
                        file: product.image,
                        bytes: product.imageBytes,
                        url: product.imageUrl,
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            product.descriptionEn,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                          ),
                          Text(
                            'MRP: ₹${product.price.toInt()}',
                            style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.6)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: qtyController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: S.get('quantity_needed'),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: targetPriceController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: S.get('target_price'),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesController,
                  maxLines: 2,
                  decoration: InputDecoration(
                    labelText: S.get('enquiry_notes'),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(S.get('cancel')),
            ),
            ElevatedButton(
              onPressed: () async {
                final qty = int.tryParse(qtyController.text) ?? 50;
                final target = double.tryParse(targetPriceController.text);
                final notes = notesController.text.trim();
                final intProdId = int.tryParse(product.id) ?? 1;

                Navigator.pop(ctx);
                final messenger = ScaffoldMessenger.of(context);
                try {
                  await ApiService.instance.sendBuyerPurchaseEnquiry(
                    productId: intProdId,
                    productName: product.descriptionEn,
                    quantity: qty,
                    targetPrice: target,
                    message: notes.isNotEmpty ? notes : 'Wholesale bulk order request for festive stocking.',
                  );
                  if (mounted) {
                    setState(() {});
                    messenger.showSnackBar(
                      SnackBar(
                        backgroundColor: AppTheme.success,
                        content: Text(S.get('enquiry_sent_success')),
                      ),
                    );
                  }
                } catch (e) {
                  messenger.showSnackBar(
                    SnackBar(content: Text('Error: $e')),
                  );
                }
              },
              child: Text(S.get('submit_enquiry')),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('buyer_app_title')),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert_rounded),
            onSelected: (val) {
              if (val == 'switch_role') {
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(builder: (_) => const RoleSelectScreen()),
                  (route) => false,
                );
              } else if (val == 'logout') {
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(builder: (_) => const LanguageSelectScreen()),
                  (route) => false,
                );
              }
            },
            itemBuilder: (ctx) => [
              PopupMenuItem(
                value: 'switch_role',
                child: Row(
                  children: [
                    const Icon(Icons.swap_horiz_rounded, size: 20),
                    const SizedBox(width: 10),
                    Text(S.isHindi ? 'भूमिका बदलें' : 'Switch Role'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    const Icon(Icons.logout_rounded, size: 20),
                    const SizedBox(width: 10),
                    Text(S.isHindi ? 'लॉगआउट' : 'Logout'),
                  ],
                ),
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            tooltip: S.get('notifications_title'),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const NotificationsScreen()),
              );
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildDiscoverTab(),
          _buildCollectionsTab(),
          _buildEnquiriesTab(),
          _buildArtisansTab(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) {
          setState(() => _currentIndex = idx);
          if (idx == 0 || idx == 1) _load();
        },
        backgroundColor: Colors.white,
        elevation: 8,
        indicatorColor: const Color(0xFFE0E7FF),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.search_rounded),
            selectedIcon: const Icon(Icons.search, color: Color(0xFF1E3A8A)),
            label: S.get('buyer_nav_discover'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.collections_bookmark_outlined),
            selectedIcon: const Icon(Icons.collections_bookmark, color: Color(0xFF1E3A8A)),
            label: S.get('buyer_nav_collections'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.receipt_long_outlined),
            selectedIcon: const Icon(Icons.receipt_long, color: Color(0xFF1E3A8A)),
            label: S.get('buyer_nav_orders'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.people_alt_outlined),
            selectedIcon: const Icon(Icons.people_alt, color: Color(0xFF1E3A8A)),
            label: S.get('buyer_nav_artisans'),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // Tab 1: Discover Crafts (Buyer Feed)
  // ==========================================
  Widget _buildDiscoverTab() {
    final filtered = _products.where((p) {
      if (_searchQuery.isEmpty) return true;
      final query = _searchQuery.toLowerCase();
      return p.descriptionEn.toLowerCase().contains(query) ||
          p.descriptionHi.toLowerCase().contains(query);
    }).toList();

    return RefreshIndicator(
      onRefresh: _load,
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Search Bar
                  TextField(
                    onChanged: (val) => setState(() => _searchQuery = val.trim()),
                    decoration: InputDecoration(
                      hintText: S.get('search_crafts_hint'),
                      prefixIcon: const Icon(Icons.search_rounded, color: Color(0xFF1E3A8A)),
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(color: AppTheme.ink.withValues(alpha: 0.1)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(color: AppTheme.ink.withValues(alpha: 0.1)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Category Filter Chips
                  SizedBox(
                    height: 38,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _categories.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (ctx, idx) {
                        final cat = _categories[idx];
                        final isSel = _selectedCategory == cat;
                        return ChoiceChip(
                          label: Text(cat),
                          selected: isSel,
                          selectedColor: const Color(0xFF1E3A8A),
                          labelStyle: TextStyle(
                            color: isSel ? Colors.white : AppTheme.ink,
                            fontWeight: isSel ? FontWeight.w700 : FontWeight.w500,
                            fontSize: 12,
                          ),
                          onSelected: (val) {
                            if (val) {
                              setState(() => _selectedCategory = cat);
                              _load();
                            }
                          },
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${filtered.length} ${S.get('direct_from_artisan')}',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.ink.withValues(alpha: 0.65),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          _loading
              ? const SliverFillRemaining(
                  child: Center(child: CircularProgressIndicator()),
                )
              : filtered.isEmpty
                  ? SliverFillRemaining(
                      child: Center(
                        child: Text(
                          S.get('no_marketplace_products'),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                    )
                  : SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      sliver: SliverGrid(
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          mainAxisSpacing: 16,
                          crossAxisSpacing: 16,
                          childAspectRatio: 0.65,
                        ),
                        delegate: SliverChildBuilderDelegate(
                          (context, i) {
                            final p = filtered[i];
                            return FadeSlideIn(
                              delay: Duration(milliseconds: 40 * i),
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: 0.03),
                                      blurRadius: 10,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                                ),
                                clipBehavior: Clip.antiAlias,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                  children: [
                                    Expanded(
                                      flex: 5,
                                      child: SafeImage(
                                        file: p.image,
                                        bytes: p.imageBytes,
                                        url: p.imageUrl,
                                      ),
                                    ),
                                    Expanded(
                                      flex: 5,
                                      child: Padding(
                                        padding: const EdgeInsets.all(10),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              p.descriptionEn,
                                              maxLines: 2,
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                            ),
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text(
                                                  '₹${p.price.toInt()}',
                                                  style: const TextStyle(
                                                    fontSize: 16,
                                                    fontWeight: FontWeight.w700,
                                                    color: Color(0xFF1E3A8A),
                                                  ),
                                                ),
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                  decoration: BoxDecoration(
                                                    color: AppTheme.successBg,
                                                    borderRadius: BorderRadius.circular(6),
                                                  ),
                                                  child: const Text(
                                                    'B2B Ready',
                                                    style: TextStyle(
                                                      fontSize: 9,
                                                      fontWeight: FontWeight.w700,
                                                      color: AppTheme.success,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                            SizedBox(
                                              width: double.infinity,
                                              height: 32,
                                              child: ElevatedButton(
                                                onPressed: () => _showEnquiryDialog(p),
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: const Color(0xFF1E3A8A),
                                                  padding: EdgeInsets.zero,
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius: BorderRadius.circular(10),
                                                  ),
                                                ),
                                                child: Text(
                                                  S.get('inquire_wholesale'),
                                                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                          childCount: filtered.length,
                        ),
                      ),
                    ),
        ],
      ),
    );
  }

  // ==========================================
  // Tab 2: Curated Collections
  // ==========================================
  Widget _buildCollectionsTab() {
    return _loading
        ? const Center(child: CircularProgressIndicator())
        : _catalogs.isEmpty
            ? Center(
                child: Text(
                  S.get('no_market_collections'),
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
                                Expanded(
                                  child: Text(
                                    cat.title,
                                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFE0E7FF),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    '${cat.products.length} Items',
                                    style: const TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                      color: Color(0xFF1E3A8A),
                                    ),
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
                                height: 85,
                                child: ListView.separated(
                                  scrollDirection: Axis.horizontal,
                                  itemCount: cat.products.length,
                                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                                  itemBuilder: (ctx, pi) {
                                    final cp = cat.products[pi];
                                    return ClipRRect(
                                      borderRadius: BorderRadius.circular(10),
                                      child: SizedBox(
                                        width: 85,
                                        height: 85,
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
              );
  }

  // ==========================================
  // Tab 3: My Orders & Enquiries (Buyer View)
  // ==========================================
  Widget _buildEnquiriesTab() {
    final buyerEnquiries = ApiService.instance.buyerSentEnquiries;
    final mockEnquiries = ApiService.instance.enquiries;

    return buyerEnquiries.isEmpty && mockEnquiries.isEmpty
        ? Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                S.get('no_buyer_enquiries'),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          )
        : ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (buyerEnquiries.isNotEmpty) ...[
                Text('Active Purchase Enquiries (${buyerEnquiries.length})',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                const SizedBox(height: 12),
                ...buyerEnquiries.map((enq) {
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                enq.productName ?? 'Artisan Craft Order',
                                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: enq.status == 'accepted' ? AppTheme.successBg : AppTheme.accentBg,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                enq.status == 'accepted' ? S.get('status_accepted_buyer') : S.get('status_pending_buyer'),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: enq.status == 'accepted' ? AppTheme.success : AppTheme.accent,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          enq.message,
                          style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.8)),
                        ),
                        if (enq.artisanResponse != null && enq.artisanResponse!.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppTheme.successBg,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.check_circle_outline, size: 16, color: AppTheme.success),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Artisan Response: "${enq.artisanResponse}"',
                                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.success),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                }),
              ],
              const SizedBox(height: 16),
              const Text('Market Quotes & Deals Feed', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
              const SizedBox(height: 12),
              ...mockEnquiries.map((me) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.ink.withValues(alpha: 0.06)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              me.productDescription,
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                            ),
                          ),
                          Text(
                            '₹${me.productPrice.toInt()}',
                            style: const TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF1E3A8A)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(me.message, style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.7))),
                      const SizedBox(height: 6),
                      Text(
                        'Artisan Partner: ${me.buyerName}',
                        style: TextStyle(fontSize: 11, color: AppTheme.ink.withValues(alpha: 0.5)),
                      ),
                    ],
                  ),
                );
              }),
            ],
          );
  }

  // ==========================================
  // Tab 4: Artisan Directory
  // ==========================================
  Widget _buildArtisansTab() {
    return _loading
        ? const Center(child: CircularProgressIndicator())
        : ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: _artisans.length,
            separatorBuilder: (_, __) => const SizedBox(height: 14),
            itemBuilder: (context, i) {
              final art = _artisans[i];
              return FadeSlideIn(
                delay: Duration(milliseconds: 40 * i),
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
                        children: [
                          Container(
                            width: 46,
                            height: 46,
                            decoration: BoxDecoration(
                              color: const Color(0xFFE0E7FF),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.person, color: Color(0xFF1E3A8A)),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  art.name,
                                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                                ),
                                Text(
                                  '${art.category} • ${art.location}',
                                  style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.6)),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppTheme.successBg,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Text('Verified', style: TextStyle(fontSize: 10, color: AppTheme.success, fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                      if (art.description != null && art.description!.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Text(
                          art.description!,
                          style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.8)),
                        ),
                      ],
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          if (art.phone != null) ...[
                            Icon(Icons.phone_outlined, size: 14, color: AppTheme.ink.withValues(alpha: 0.5)),
                            const SizedBox(width: 4),
                            Text(art.phone!, style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.6))),
                          ],
                          const Spacer(),
                          TextButton.icon(
                            icon: const Icon(Icons.storefront_outlined, size: 16),
                            label: Text(S.get('view_artisan_catalog')),
                            onPressed: () {
                              setState(() => _currentIndex = 0);
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          );
  }
}
