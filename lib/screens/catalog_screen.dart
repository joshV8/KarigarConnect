import 'package:flutter/material.dart';
import '../language.dart';
import '../models/catalog_model.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';
import 'product_detail_screen.dart';

/// Full catalog screen supporting both raw Products and curated digital Collections.
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
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
    await ApiService.instance.fetchCatalog();
    final cats = await ApiService.instance.fetchCatalogs();
    if (mounted) {
      setState(() {
        _catalogs = cats;
        _loading = false;
      });
    }
  }

  void _showCreateCatalogDialog() {
    final titleController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Text(S.get('new_collection')),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: InputDecoration(
                  labelText: S.get('title_label'),
                  hintText: S.get('title_hint'),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descController,
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: S.get('description_label'),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(S.get('cancel')),
            ),
            ElevatedButton(
              onPressed: () async {
                final title = titleController.text.trim();
                if (title.isEmpty) return;
                Navigator.pop(ctx);
                try {
                  await ApiService.instance.createCatalog(
                    title: title,
                    description: descController.text.trim().isNotEmpty ? descController.text.trim() : null,
                  );
                  _load();
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        backgroundColor: AppTheme.success,
                        content: Text(S.get('collection_created')),
                      ),
                    );
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error: $e')),
                    );
                  }
                }
              },
              child: Text(S.get('create')),
            ),
          ],
        );
      },
    );
  }

  void _showAddToCatalogDialog(CatalogModel catalog) {
    final products = ApiService.instance.catalog;
    if (products.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(S.get('no_products_available'))),
      );
      return;
    }

    Product selected = products.first;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: Text('${S.get('add_to_collection')} ${catalog.title}'),
              content: DropdownButtonFormField<Product>(
                initialValue: selected,
                decoration: InputDecoration(
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                ),
                items: products.map((p) {
                  return DropdownMenuItem(
                    value: p,
                    child: Text('${p.descriptionEn} (₹${p.price.toInt()})', maxLines: 1, overflow: TextOverflow.ellipsis),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) setDialogState(() => selected = val);
                },
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: Text(S.get('cancel'))),
                ElevatedButton(
                  onPressed: () async {
                    final messenger = ScaffoldMessenger.of(context);
                    Navigator.pop(ctx);
                    try {
                      await ApiService.instance.addProductToCatalog(
                        catalog.id,
                        int.tryParse(selected.id) ?? 1,
                      );
                      _load();
                      messenger.showSnackBar(
                        SnackBar(
                          backgroundColor: AppTheme.success,
                          content: Text(S.get('product_added')),
                        ),
                      );
                    } catch (e) {
                      messenger.showSnackBar(
                        SnackBar(content: Text('Error: $e')),
                      );
                    }
                  },
                  child: Text(S.get('add_btn')),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _publishCatalog(CatalogModel catalog) async {
    try {
      await ApiService.instance.publishCatalog(catalog.id);
      _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppTheme.success,
            content: Text(S.get('published_to_marketplace')),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Publish error: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final catalog = ApiService.instance.catalog;

    return Scaffold(
      appBar: AppBar(
        title: Text(S.get('catalog_title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.create_new_folder_outlined),
            tooltip: S.get('new_collection'),
            onPressed: _showCreateCatalogDialog,
          ),
          const HomeAction(),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.ink,
          indicatorColor: AppTheme.accent,
          tabs: [
            Tab(text: '${S.get('all_items')} (${catalog.length})'),
            Tab(text: '${S.get('digital_collections')} (${_catalogs.length})'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Products Grid
                catalog.isEmpty
                    ? Center(
                        child: Text(
                          S.get('no_items'),
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
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
                                onTap: () async {
                                  await Navigator.of(context).push(
                                    MaterialPageRoute(builder: (_) => ProductDetailScreen(product: p)),
                                  );
                                  if (mounted) _load();
                                },
                                child: Container(
                                  decoration: BoxDecoration(
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

                // Digital Collections Tab
                _catalogs.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.folder_open, size: 64, color: AppTheme.ink.withValues(alpha: 0.25)),
                            const SizedBox(height: 16),
                            Text(
                              S.get('no_collections'),
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.add),
                              label: Text(S.get('create_collection')),
                              onPressed: _showCreateCatalogDialog,
                            ),
                          ],
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
                            final isPublished = cat.status == 'published';

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
                                            color: isPublished ? AppTheme.successBg : AppTheme.accentBg,
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: Text(
                                            isPublished ? 'PUBLISHED' : 'DRAFT',
                                            style: TextStyle(
                                              fontSize: 11,
                                              fontWeight: FontWeight.w700,
                                              color: isPublished ? AppTheme.success : AppTheme.accent,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    if (cat.description != null) ...[
                                      const SizedBox(height: 6),
                                      Text(cat.description!, style: Theme.of(context).textTheme.bodyMedium),
                                    ],
                                    const SizedBox(height: 10),
                                    Text(
                                      '${cat.products.length} ${S.get('items_included')}',
                                      style: TextStyle(fontSize: 13, color: AppTheme.ink.withValues(alpha: 0.6)),
                                    ),
                                    const SizedBox(height: 14),
                                    Row(
                                      children: [
                                        Expanded(
                                          child: OutlinedButton.icon(
                                            icon: const Icon(Icons.add, size: 16),
                                            label: Text(S.get('add_item')),
                                            onPressed: () => _showAddToCatalogDialog(cat),
                                          ),
                                        ),
                                        if (!isPublished) ...[
                                          const SizedBox(width: 10),
                                          Expanded(
                                            child: ElevatedButton.icon(
                                              icon: const Icon(Icons.public, size: 16),
                                              label: Text(S.get('publish_btn')),
                                              onPressed: () => _publishCatalog(cat),
                                            ),
                                          ),
                                        ],
                                      ],
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
    );
  }
}
