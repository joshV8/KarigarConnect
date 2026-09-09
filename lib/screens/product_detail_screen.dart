import 'package:flutter/material.dart';
import '../models/product.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/safe_image.dart';
import '../widgets/fade_slide_in.dart';
import '../widgets/home_action.dart';

/// Detail view for a published product — reachable by tapping any
/// item in Home or Catalog. Supports editing the AI-generated text
/// and price (the artisan should always have final say), and
/// deleting a listing outright.
class ProductDetailScreen extends StatefulWidget {
  final Product product;
  const ProductDetailScreen({super.key, required this.product});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late Product _product = widget.product;
  bool _editing = false;
  late final _hiController = TextEditingController(text: _product.descriptionHi);
  late final _enController = TextEditingController(text: _product.descriptionEn);
  late double _price = _product.price;

  @override
  void dispose() {
    _hiController.dispose();
    _enController.dispose();
    super.dispose();
  }

  void _save() {
    final updated = Product(
      id: _product.id,
      image: _product.image,
      imageUrl: _product.imageUrl,
      descriptionHi: _hiController.text.trim(),
      descriptionEn: _enController.text.trim(),
      price: _price,
      priceReason: _product.priceReason,
    );
    ApiService.instance.updateProduct(updated);
    setState(() {
      _product = updated;
      _editing = false;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('अपडेट हो गया · Updated'), duration: Duration(seconds: 2)),
    );
  }

  Future<void> _confirmDelete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('हटाएं? · Delete this listing?'),
        content: const Text('यह कैटलॉग से हमेशा के लिए हट जाएगा।\nThis will be removed from your catalog permanently.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('रद्द करें · Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('हटाएं · Delete', style: TextStyle(color: AppTheme.danger)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      ApiService.instance.deleteProduct(_product.id);
      if (mounted) Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(
        title: Text(_editing ? 'संपादित करें · Editing' : 'सामान विवरण · Product'),
        actions: [
          IconButton(
            icon: Icon(_editing ? Icons.check : Icons.edit_outlined),
            tooltip: _editing ? 'Save' : 'Edit',
            onPressed: _editing ? _save : () => setState(() => _editing = true),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Delete',
            onPressed: _confirmDelete,
          ),
          const HomeAction(),
        ],
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
                  file: _product.image,
                  url: _product.imageUrl,
                  borderRadius: BorderRadius.circular(18),
                ),
              ),
              const SizedBox(height: 20),
              FadeSlideIn(
                delay: const Duration(milliseconds: 60),
                child: _editing
                    ? _editField(label: 'विवरण · Description (हिंदी)', controller: _hiController)
                    : _card(label: 'विवरण · Description (हिंदी)', value: _product.descriptionHi, textTheme: textTheme),
              ),
              const SizedBox(height: 12),
              FadeSlideIn(
                delay: const Duration(milliseconds: 140),
                child: _editing
                    ? _editField(label: 'Description (English)', controller: _enController)
                    : _card(label: 'Description (English)', value: _product.descriptionEn, textTheme: textTheme),
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
                          _editing
                              ? Row(
                                  children: [
                                    _stepBtn(Icons.remove, () => setState(() => _price = (_price - 10).clamp(0, 100000))),
                                    SizedBox(
                                      width: 70,
                                      child: Text('₹${_price.toInt()}',
                                          textAlign: TextAlign.center,
                                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                                    ),
                                    _stepBtn(Icons.add, () => setState(() => _price = (_price + 10).clamp(0, 100000))),
                                  ],
                                )
                              : Text('₹${_product.price.toInt()}',
                                  style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(_product.priceReason,
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

  Widget _stepBtn(IconData icon, VoidCallback onTap) {
    return IconButton(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
      padding: EdgeInsets.zero,
      style: IconButton.styleFrom(
        backgroundColor: Colors.white,
        shape: const CircleBorder(),
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

  Widget _editField({required String label, required TextEditingController controller}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.accent, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 4, bottom: 6),
            child: Text(label, style: TextStyle(fontSize: 12, color: AppTheme.ink.withValues(alpha: 0.5))),
          ),
          TextField(
            controller: controller,
            maxLines: 3,
            style: const TextStyle(fontSize: 17),
            decoration: const InputDecoration(border: InputBorder.none, isDense: true),
          ),
        ],
      ),
    );
  }
}
