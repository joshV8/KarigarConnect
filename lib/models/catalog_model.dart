import 'product.dart';

/// Model representing an artisan's curated digital catalog.
class CatalogModel {
  final int id;
  final String title;
  final String? description;
  final String status; // draft | published | archived
  final List<Product> products;
  final DateTime? createdAt;

  CatalogModel({
    required this.id,
    required this.title,
    this.description,
    required this.status,
    required this.products,
    this.createdAt,
  });

  factory CatalogModel.fromJson(Map<String, dynamic> json) {
    final prodsRaw = json['products'] as List? ?? [];
    final List<Product> prods = [];
    for (final p in prodsRaw) {
      final m = p as Map<String, dynamic>;
      final images = m['images'] as List? ?? [];
      String? imgUrl;
      if (images.isNotEmpty) {
        imgUrl = images.first['original_url'] as String?;
      }
      prods.add(
        Product(
          id: m['id'].toString(),
          imageUrl: imgUrl,
          descriptionHi: m['name'] ?? '',
          descriptionEn: m['name'] ?? '',
          price: (m['recommended_price'] as num?)?.toDouble() ?? 0.0,
          priceReason: 'Included in collection',
        ),
      );
    }

    return CatalogModel(
      id: json['id'] as int,
      title: json['title'] as String? ?? 'Collection',
      description: json['description'] as String?,
      status: json['status'] as String? ?? 'draft',
      products: prods,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
    );
  }
}
